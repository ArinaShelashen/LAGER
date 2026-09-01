import os
import json
import uuid
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

from rdkit import Chem
from rdkit.Chem import Draw


# ============================================================
# CONFIG
# ============================================================

MOLECULE_SIZE = (300,220)

STATUS_COLORS = {
    "buyable": {
        "border": "#35A66F",
        "fill": "#F3FBF7",
        "text": "#258354",
        "label": "BUYABLE",
    },
    "side_product": {
        "border": "#8AC2D1",
        "fill": "#FFFFFF",
        "text": "#8AC2D1",
        "label": "SIDE PRODUCT",
    },
    "unreachable": {
        "border": "#A22332",
        "fill": "#FFF5F5",
        "text": "#A22332",
        "label": "UNREACHABLE",
    },
    "intermediate": {
        "border": "#B7BDC5",
        "fill": "#F7F8FA",
        "text": "#B7BDC5",
        "label": "INTERMEDIATE",
    },
    None: {
        "border": "#AAB2BC",
        "fill": "#FFFFFF",
        "text": "#69737E",
        "label": "",
    },
}


# ============================================================
# RDKit rendering
# ============================================================
def save_json(root):
    with open("retrosynthesis_tree.json", "w") as f:
        if isinstance(root, dict):
            json.dump(root, f, indent=2)
        elif hasattr(root, "to_dict"):
            json.dump(root.to_dict(), f, indent=2)
        else:
            print(f"Unexpected type: {type(root)}")

def pathway_to_branched_tree_dict(pathway, buyables_set, side_set):
    """
    Converts the chronological reaction log from a convergent A* search
    into a nested tree dictionary for Graphviz visualization.
    """
    if not pathway:
        return None

    def build_node(smiles, status=None, step_data=None, rule_name=None, side_reactions=None):
        return {
            "id": str(uuid.uuid4()),
            "smiles": smiles,
            "status": status,
            "g": step_data.get("g_score") if step_data else None,
            "h": step_data.get("h_score") if step_data else None,
            "f": step_data.get("f_score") if step_data else None,
            "rule_name": rule_name,
            "side_reactions": side_reactions,
            "branches": []
        }

    # We use a dictionary of lists (a stack) to track active nodes.
    # This prevents bugs if a molecule is split into two identical fragments!
    active_nodes = {}

    def register_node(smiles, node):
        if smiles not in active_nodes:
            active_nodes[smiles] = []
        active_nodes[smiles].append(node)

    def pull_node_to_react(smiles):
        if smiles in active_nodes and len(active_nodes[smiles]) > 0:
            return active_nodes[smiles].pop()
        return None

    # --- 1. Initialize the Root (Target Molecule) ---
    # The target is the very first molecule in the unsolved pool at Step 0
    target_smiles = pathway[0]["unsolved_pool"][0]

    # Check if the target is trivially buyable right out of the gate
    root_status = "buyable" if target_smiles in buyables_set else "intermediate"
    root = build_node(target_smiles, status=root_status, step_data=pathway[0])

    register_node(target_smiles, root)

    # --- 2. Build the Tree from the Reaction Log ---
    for i in range(1, len(pathway)):
        step = pathway[i]
        reaction = step["reaction"]

        if not reaction:
            continue  # Failsafe

        current_rule_name = reaction.get("rule_name", "Unknown Reaction")
        side_reactions_names = reaction.get("side_reactions", "No side reactions detected")

        # Find the node that underwent this reaction
        parent_smiles = reaction["parent_mol"]
        parent_node = pull_node_to_react(parent_smiles)

        if not parent_node:
            print(f"Warning: Disconnected tree! Could not find parent node for {parent_smiles}")
            continue

        branch = []

        # A) Attach Buyables and Side Products
        for b_smiles in reaction["buyables_cleaved"]:
            status = "buyable" if b_smiles in buyables_set else ("side_product" if b_smiles in side_set else "buyable")
            child_node = build_node(b_smiles, status=status, rule_name=current_rule_name, side_reactions=side_reactions_names)
            branch.append(child_node)

        # B) Attach New Intermediates
        for int_smiles in reaction["new_intermediates"]:
            # Even if it's an "intermediate", check if we just hit a buyable!
            status = "buyable" if int_smiles in buyables_set else "intermediate"

            # Pass the global step scores down so they print on the new intermediate
            child_node = build_node(int_smiles, status=status, step_data=step, rule_name=current_rule_name, side_reactions=side_reactions_names)
            branch.append(child_node)

            # Put this new intermediate on the active stack in case a future step reacts it
            register_node(int_smiles, child_node)

        # Snap the finished branch onto the parent molecule
        parent_node["branches"].append(branch)

    return root

def smiles_to_png(smiles, out_path, size=MOLECULE_SIZE):

    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    # [2H] -> ACTIVATOR
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 1 and atom.GetIsotope() == 2:
            atom.SetProp("atomLabel", "ACTIVATOR")
            atom.SetIsotope(0)

    Draw.MolToFile(
        mol,
        out_path,
        size=size
    )


def annotate_with_images(node, img_dir="imgs"):

    os.makedirs(img_dir, exist_ok=True)

    img_path = os.path.abspath(
        os.path.join(
            img_dir,
            f"{node['id']}.png"
        )
    )

    smiles_to_png(
        node["smiles"],
        img_path
    )

    node["img"] = img_path

    for branch in node["branches"]:
        for child in branch:
            annotate_with_images(
                child,
                img_dir
            )


# ============================================================
# Graphviz helpers
# ============================================================

def dot_escape(value):

    if value is None:
        return ""

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
    )


def fmt_score(value):

    if value is None:
        return ""

    if isinstance(value, float):
        return f"{value:.3f}"

    return str(value)


def clean_rule_name(rule_name):

    if not rule_name:
        return "reaction"

    name = rule_name.replace("_", " ")
    if name.endswith(" inv"):
        name = name[:-4]


    # Split long names at a word boundary
    if len(name) > 38:
        split_pos = name.rfind(" ", 0, 39)

        if split_pos == -1:
            split_pos = 38

        name = (
            name[:split_pos]
            + r"\n"
            + name[split_pos + 1:]
        )
    return name


# ============================================================
# Molecule node
# ============================================================

def add_molecule_node(node, dot):

    node_id = node["id"]

    status = node.get("status")

    colors = STATUS_COLORS.get(
        status,
        STATUS_COLORS["intermediate"]
    )

    border = colors["border"]
    fill = colors["fill"]
    text_color = colors["text"]

    # --------------------------------------------------------
    # Score label
    # --------------------------------------------------------

    score_parts = []

    if node.get("g") is not None:
        score_parts.append(
            f"g {fmt_score(node['g'])}"
        )

    if node.get("h") is not None:
        score_parts.append(
            f"h {fmt_score(node['h'])}"
        )

    if node.get("f") is not None:
        score_parts.append(
            f"f {fmt_score(node['f'])}"
        )

    score_text = "   ·   ".join(score_parts)

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    status_text = colors["label"]

    if status_text:
        status_label = (
            f"{status_text}"
        )
    else:
        status_label = ""

    # --------------------------------------------------------
    # Main molecule node
    #
    # IMPORTANT:
    # Use Graphviz's native `image=` attribute instead of
    # <IMG> inside an HTML label.
    # --------------------------------------------------------

    dot.append(
        f'"{node_id}" '
        f'[shape=box, '
        f'style="rounded,filled", '
        f'fillcolor="white", ' #"{fill}", '
        f'color="{border}", '
        f'penwidth=6.0, '
        f'fixedsize=true, '
        f'width=3.5, '
        f'height=2.75, '
        f'margin="0.2,0.2", '
        f'image="{dot_escape(node["img"])}", '
        f'label="", '
        # f'imagescale=true, '
        f'labelloc="b", '
        f'fontname="Helvetica", '
        f'fontcolor="{text_color}", '
        f'fontsize=20, '
        f'xlabel="{dot_escape(score_text)}"];'
    )

    # --------------------------------------------------------
    # Status badge as a tiny secondary node
    # --------------------------------------------------------

    if status_label:

        badge_id = f"{node_id}_status"

        dot.append(
            f'"{badge_id}" '
            f'[shape=plaintext, '
            f'label="{dot_escape(status_label)}", '
            f'fontname="Helvetica", '
            f'fontsize=16, '
            f'fontcolor="{text_color}"];'
        )

        dot.append(
            f'"{node_id}" -> "{badge_id}" '
            f'[style=invis, weight=10];'
        )


# ============================================================
# Reaction node
# ============================================================

def add_reaction_node(
    reaction_id,
    rule_name,
    side_reactions,
    step_number,
    dot
):

    clean_name = clean_rule_name(rule_name)

    if side_reactions and isinstance(side_reactions, list):
        warning = (
            "\\nWarning! The following side reactions detected:"
            f"\\n{', '.join(side_reactions)}"
        )
    else:
        # This catches empty lists [], None, or the string itself
        warning = "\\nNo side reactions detected"

    # Use a normal Graphviz box instead of an HTML label.
    dot.append(
        f'"{reaction_id}" '
        f'[shape=box, '
        f'style="rounded,filled", '
        f'fillcolor="#F7F9FB", '
        f'color="#D5DAE0", '
        f'penwidth=3.6, '
        f'fontname="Helvetica", '
        f'fontsize=18, '
        f'fontcolor="#4D5864", '
        f'width=1.65, '
        f'height=0.55, '
        f'label="STEP {step_number}\\n{clean_name}\\n\\n{warning}"];'
    )


# ============================================================
# Recursive tree -> DOT
# ============================================================

def to_dot(
    node,
    dot,
    depth=0
):

    node_id = node["id"]

    # Add molecule
    add_molecule_node(
        node,
        dot
    )

    # --------------------------------------------------------
    # Reactions
    # --------------------------------------------------------

    for branch_index, branch in enumerate(
        node["branches"]
    ):

        reaction_id = (
            f"{node_id}_rxn_{branch_index}"
        )

        rule_name = ""
        side_reactions_names = ""

        if branch and isinstance(branch[0], dict):
            rule_name = branch[0].get(
                "rule_name",
                ""
            )
            side_reactions_names = branch[0].get(
                "side_reactions", ""
            )

        step_number = depth + 1

        add_reaction_node(
            reaction_id,
            rule_name,
            side_reactions_names,
            step_number,
            dot
        )

        # Parent -> reaction
        dot.append(
            f'"{node_id}" -> "{reaction_id}" '
            f'[color="#AAB2BC", '
            f'penwidth=1.5, '
            f'arrowsize=0.65];'
        )

        # Reaction -> children
        for child in branch:

            child_id = child["id"]

            dot.append(
                f'"{reaction_id}" -> "{child_id}" '
                f'[color="#AAB2BC", '
                f'penwidth=1.5, '
                f'arrowsize=0.65];'
            )

            to_dot(
                child,
                dot,
                depth + 1
            )


# ============================================================
# Legend
# ============================================================

def add_legend(dot):

    # Native Graphviz nodes, no HTML labels.
    dot.append(
        '"legend_title" '
        '[shape=plaintext, '
        'label="RETROSYNTHESIS PATHWAY", '
        'fontname="Helvetica-Bold", '
        'fontsize=30, '
        'fontcolor="#303943"];'
    )

    dot.append(
        '"legend_subtitle" '
        '[shape=plaintext, '
        'label="Target → disconnection → precursors", '
        'fontname="Helvetica", '
        'fontsize=18, '
        'fontcolor="#7A8491"];'
    )

    dot.append(
        '"legend_buyable" '
        '[shape=plaintext, '
        'label="● BUYABLE", '
        'fontname="Helvetica-Bold", '
        'fontsize=18, '
        'fontcolor="#35A66F"];'
    )

    dot.append(
        '"legend_intermediate" '
        '[shape=plaintext, '
        'label="● INTERMEDIATE", '
        'fontname="Helvetica-Bold", '
        'fontsize=18, '
        'fontcolor="#B7BDC5"];'
    )

    dot.append(
        '"legend_side" '
        '[shape=plaintext, '
        'label="● SIDE PRODUCT", '
        'fontname="Helvetica-Bold", '
        'fontsize=18, '
        'fontcolor="#8AC2D1"];'
    )

    # Invisible alignment edges
    dot.append(
        '"legend_title" -> "legend_subtitle" '
        '[style=invis];'
    )

    dot.append(
        '"legend_subtitle" -> "legend_buyable" '
        '[style=invis];'
    )

    dot.append(
        '"legend_buyable" -> "legend_intermediate" '
        '[style=invis];'
    )

    dot.append(
        '"legend_intermediate" -> "legend_side" '
        '[style=invis];'
    )


# ============================================================
# Main renderer
# ============================================================

def save_png(
    root,
    output_filename="pathway.png",
    output_svg="pathway.svg"
):

    if isinstance(root, dict):

        root_dict = root

    elif hasattr(root, "to_dict"):

        root_dict = root.to_dict()

    else:

        raise TypeError(
            f"Unexpected type: {type(root)}"
        )

    img_dir = "imgs"

    annotate_with_images(
        root_dict,
        img_dir
    )

    # --------------------------------------------------------
    # DOT
    # --------------------------------------------------------

    dot = [
        "digraph Retrosynthesis {",

        # Left -> right retrosynthesis
        "rankdir=LR;",

        # Layout
        "nodesep=0.30;",
        "ranksep=0.55;",
        "pad=0.35;",
        "margin=0.1;",

        # Graph
        'bgcolor="white";',

        # Default node settings
        'node [fontname="Helvetica"];',

        # Edge defaults
        'edge [fontname="Helvetica"];',
    ]

    to_dot(
        root_dict,
        dot
    )

    add_legend(dot)

    dot.append("}")

    dot_filename = "retrosynthesis_tree.dot"

    with open(
        dot_filename,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "\n".join(dot)
        )

    # --------------------------------------------------------
    # Render
    # --------------------------------------------------------

    try:

        subprocess.run(
            [
                "dot",
                "-Tpng",
                dot_filename,
                "-o",
                output_filename
            ],
            check=True
        )

        subprocess.run(
            [
                "dot",
                "-Tsvg",
                dot_filename,
                "-o",
                output_svg
            ],
            check=True
        )

        print(
            f"Saved PNG: {output_filename}"
        )

        print(
            f"Saved SVG: {output_svg}"
        )

    except FileNotFoundError:

        print(
            "Graphviz 'dot' was not found on PATH."
        )

    except subprocess.CalledProcessError as e:

        print(
            f"Graphviz rendering failed: {e}"
        )

        print(
            f"DOT file retained at: {dot_filename}"
        )

        return

    finally:

        if os.path.exists(img_dir):
            shutil.rmtree(img_dir)

        if os.path.exists(dot_filename):
            os.remove(dot_filename)


def stack_pngs_vertically(image_paths, output_path, labels=None,
                           padding=40, bg_color="white",
                           caption_height=40, font_size=56):
    """Stacks PNGs on top of each other into a single image, left-aligned,
    with a caption above each image and fixed padding between them."""
    images = [Image.open(p) for p in image_paths]

    if labels is None:
        labels = [f"PATHWAY {i+1}" for i in range(len(images))]

    # Try to load a nicer font, fall back to default if unavailable
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    max_width = max(img.width for img in images)
    block_heights = [caption_height + img.height for img in images]
    total_height = sum(block_heights) + padding * (len(images) - 1)

    combined = Image.new("RGB", (max_width, total_height), color=bg_color)
    draw = ImageDraw.Draw(combined)

    y_offset = 0
    for img, label in zip(images, labels):
        # Caption, centered horizontally over this image's block
        text_bbox = draw.textbbox((0, 0), label, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (max_width - text_width) // 2
        draw.text((text_x, y_offset -15), label, fill="black", font=font)

        # Image, left-aligned below the caption
        combined.paste(img, (0, y_offset + caption_height))

        y_offset += caption_height + img.height + padding

    combined.save(output_path)
    print(f"Saved combined pathways image to {output_path}")