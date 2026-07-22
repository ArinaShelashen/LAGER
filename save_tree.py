import json
import uuid
from rdkit import Chem
from rdkit.Chem import Draw
import os
import shutil
import subprocess

def smiles_to_png(smiles, out_path, size=(300, 300)):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    # --- VISUALIZATION HACK: Replace [2H] with 'ACT' ---
    # [2H] is used in COOH activation for condensation reaction to encode all possible activators
    for atom in mol.GetAtoms():
        # Find any Hydrogen atom that is the [2H] isotope
        if atom.GetAtomicNum() == 1 and atom.GetIsotope() == 2:
            # Set a custom label for RDKit to render instead of the element symbol
            atom.SetProp("atomLabel", "ACTIVATOR")
            # Clear the isotope number so RDKit doesn't accidentally draw "2ACT"
            atom.SetIsotope(0)
    # ----------------------------------------------------

    Draw.MolToFile(mol, out_path, size=size)

def annotate_with_images(node, img_dir="imgs"):
    os.makedirs(img_dir, exist_ok=True)

    img_path = os.path.join(img_dir, f"{node['id']}.png")
    smiles_to_png(node["smiles"], img_path)
    node["img"] = img_path

    for branch in node["branches"]:
        for child in branch:
            annotate_with_images(child, img_dir)

def to_dot(node, dot):
    node_id = node["id"]
    # Map status to colors
    status_colors = {
        "buyable": "#49B375",
        "side_product": "lightgray",
        "unreachable": "#b02f2c",
        None: "white"
    }
    color = status_colors.get(node.get("status"), "white")

    label_text = ""
    if node.get("g") is not None and node.get("h") is not None:
        label_text = f"g={node['g']} | h={node['h']} | f={node['f']}"

    dot.append(
        f'"{node_id}" [shape=box,  image="{node["img"]}", label="{label_text}", labelloc="b", '
        f'color="{color}", penwidth=6, imagescale=true];'
    )


    for i, branch in enumerate(node["branches"]):
        rxn_id = f"{node_id}_rxn_{i}"

        dot.append(f'"{rxn_id}" [shape=diamond, label="", width=0.4, height=0.4];')
        dot.append(f'"{node_id}" -> "{rxn_id}";')

        for child in branch:
            dot.append(f'"{rxn_id}" -> "{child["id"]}";')
            to_dot(child, dot)


def save_json(root):
    with open("retrosynthesis_tree.json", "w") as f:
        if isinstance(root, dict):
            json.dump(root, f, indent=2)
        elif hasattr(root, "to_dict"):
            json.dump(root.to_dict(), f, indent=2)
        else:
            print(f"Unexpected type: {type(root)}")


def save_png(root, output_filename="pathway.png"):
    if isinstance(root, dict):
        root_dict = root
    elif hasattr(root, "to_dict"):
        root_dict = root.to_dict()
    else:
        print(f"Unexpected type: {type(root)}")
        return
    annotate_with_images(root_dict)

    dot = [
        "digraph Retrosynthesis {",
        "rankdir=TB;",
        "node [fontname=Helvetica];"
    ]
    to_dot(root_dict, dot)
    dot.append("}")

    dot_filename = "retrosynthesis_tree.dot"
    with open(dot_filename, "w") as f:
        f.write("\n".join(dot))

    try:
        # Run the Graphviz 'dot' command to render the final PNG
        subprocess.run(["dot", "-Tpng", dot_filename, "-o", output_filename], check=True)
        print(f"Saved pathway visualization to {output_filename}")

        # --- THE CLEANUP STEP ---
        # Delete the whole temporary imgs folder
        if os.path.exists("imgs"):
            shutil.rmtree("imgs")

        # Delete the .dot file
        if os.path.exists(dot_filename):
            os.remove(dot_filename)

    except FileNotFoundError:
        print("Warning: Graphviz ('dot' command) is not installed or not in PATH.")
        print("The .dot file and imgs/ folder were kept so you can render it manually.")
    except subprocess.CalledProcessError as e:
        print(f"Error rendering the final image with Graphviz: {e}")

def pathway_to_tree_dict(pathway, buyables_set, side_set):
    """
    Converts the flat list output of A* into a nested tree dictionary
    compatible with the dot visualization functions.
    """
    if not pathway:
        return None

    def build_node(smiles, status=None, g=None, h=None, f=None):
        return {
            "id": str(uuid.uuid4()),
            "smiles": smiles,
            "status": status,
            "g": g, "h": h, "f": f,
            "branches": []
        }

    # Start with the target molecule
    root_step = pathway[0]
    root = build_node(
        root_step["intermediate"],
        g=root_step.get("g_score"),
        h=root_step.get("h_score"),
        f=root_step.get("f_score")
    )
    current_node = root

    # Iterate through the reaction steps
    for i in range(1, len(pathway)):
        step = pathway[i]
        branch = []

        # 1. Add the buyables/side-products cleaved in this step
        for b_smiles in step["buyables_cleaved_in_this_step"]:
            status = "buyable" if b_smiles in buyables_set else ("side_product" if b_smiles in side_set else "buyable")
            branch.append(build_node(b_smiles, status=status))

        # 2. Add the next intermediate (unless the goal was completely reached)
        if step["intermediate"] != "GOAL_REACHED":
            next_intermediate_node = build_node(
                step["intermediate"],
                g=step.get("g_score"),
                h=step.get("h_score"),
                f=step.get("f_score")
            )
            branch.append(next_intermediate_node)
            current_node["branches"].append(branch)
            current_node = next_intermediate_node # Move down the chain for the next loop
        else:
            current_node["branches"].append(branch)

    # If the final intermediate happens to be buyable itself, color it green
    if current_node["smiles"] in buyables_set:
        current_node["status"] = "buyable"

    return root

def pathway_to_branched_tree_dict(pathway, buyables_set, side_set):
    """
    Converts the chronological reaction log from a convergent A* search
    into a nested tree dictionary for Graphviz visualization.
    """
    if not pathway:
        return None

    def build_node(smiles, status=None, step_data=None):
        return {
            "id": str(uuid.uuid4()),
            "smiles": smiles,
            "status": status,
            "g": step_data.get("g_score") if step_data else None,
            "h": step_data.get("h_score") if step_data else None,
            "f": step_data.get("f_score") if step_data else None,
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
            child_node = build_node(b_smiles, status=status)
            branch.append(child_node)

        # B) Attach New Intermediates
        for int_smiles in reaction["new_intermediates"]:
            # Even if it's an "intermediate", check if we just hit a buyable!
            status = "buyable" if int_smiles in buyables_set else "intermediate"

            # Pass the global step scores down so they print on the new intermediate
            child_node = build_node(int_smiles, status=status, step_data=step)
            branch.append(child_node)

            # Put this new intermediate on the active stack in case a future step reacts it
            register_node(int_smiles, child_node)

        # Snap the finished branch onto the parent molecule
        parent_node["branches"].append(branch)

    return root