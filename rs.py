import argparse
import os
import uuid
import subprocess
from mod import *
from save_tree import save_dot, save_json
from rdkit import Chem
import mod

class RetroNode:
    def __init__(self, smiles, status=None):
        self.id = str(uuid.uuid4())
        self.smiles = smiles
        self.children = []
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "smiles": self.smiles,
            "status": self.status,
            "branches": [
                [child.to_dict() for child in branch]
                for branch in self.children
            ]
        }


def canonical_smiles(smiles: str) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol, canonical=True)

def remove_stereo(smiles: str) -> str | None:
    """
    Remove stereochemistry from a SMILES string.
    Returns canonical SMILES without stereo information.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    # Remove chiral tags
    for atom in mol.GetAtoms():
        atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    for bond in mol.GetBonds():
        bond.SetStereo(Chem.BondStereo.STEREONONE)
    return Chem.MolToSmiles(mol, canonical=True)

def generate_graphs(csv_file, addHs=True):
    """
    Calls mol_graph_creator.py CLI to generate .gml graphs
    Returns list of Graph objects
    """
    output_file = csv_file.replace(".csv", "_graphs")
    os.makedirs(output_file, exist_ok=True)
    cmd = ["python", "mol_graphs_creator.py", csv_file, "-o", output_file, "-Hs", str(addHs)]
    subprocess.run(cmd, check=True)
    gml_files = [os.path.join(output_file, f) for f in os.listdir(output_file) if f.endswith(".gml")]
    return [Graph.fromGMLFile(f) for f in gml_files]


def retrosynthesis_step(target_node, rules, side_graphs,
                        buyables_set, side_set, max_depth=5, depth=1,
                        reaction_cache=None, stats=None):
    # Initialize the trackers on the first run
    if reaction_cache is None:
        reaction_cache = {}
    if stats is None:
        stats = {"visited": 0}

    # 1. INCREMENT STATES VISITED
    stats["visited"] += 1
    precursors_to_expand = []

    # 2. THE MASSIVE SPEEDUP: MEMOIZATION
    # If we have already expanded this exact SMILES in another branch,
    # simply link to the cached children and return immediately!
    if target_node.smiles in reaction_cache:
        # Load the raw strings and status from cache
        cached_status, cached_branches_smiles = reaction_cache[target_node.smiles]
        target_node.status = cached_status
        # Rebuild fresh RetroNode objects to keep your Tree clean
        for branch_smiles in cached_branches_smiles:
            branch = []
            for cs in branch_smiles:
                node = RetroNode(cs)
                branch.append(node)

                if cs in buyables_set:
                    node.status = "buyable"
                elif cs in side_set:
                    node.status = "side_product"
                else:
                    precursors_to_expand.append(node)
            target_node.children.append(branch)

    else:
        target_graph = Graph.fromSMILES(target_node.smiles)

        dg = DG(graphDatabase=[target_graph, *side_graphs])
        strat = (
            addUniverse(*side_graphs)
            >> addSubset(target_graph)
            >> rules
        )

        with dg.build() as builder:
            builder.execute(strat)

        if target_node.status == None and dg.numEdges == 0:
            target_node.status = "unreachable"
            return
        branches_to_cache = []
        for e in dg.edges:
            branch = []
            branch_smiles = []

            for v in e.targets:
                cs = canonical_smiles(v.graph.smiles)
                if cs is None:
                    continue
                branch_smiles.append(cs)
                node = RetroNode(cs)
                branch.append(node)
                # if cs not in buyables_set and cs not in side_set:
                #     precursors_to_expand.append(node)
                if cs in buyables_set:
                    node.status = "buyable"
                    # print(f"Precursor {cs} is among buyables")
                elif cs in side_set:
                    node.status = "side_product"
                    # print(f"Precursor {cs} is a side product")
                else:
                    precursors_to_expand.append(node)
                    # precursors_to_expand_smiles.append(cs)
            if branch:
                target_node.children.append(branch)
                branches_to_cache.append(branch_smiles)

    # 3. CACHE THE RESULT BEFORE RECURSING
    # Save the successfully generated branches for this SMILES so we never
    # have to run MØD on it again in future recursive steps.
        reaction_cache[target_node.smiles] = (target_node.status, branches_to_cache)
    # print(f'Level {depth} is finished')
    # print(f"Precursors to synthesize: {precursors_to_expand_smiles}")
    if depth < max_depth:
        for node in precursors_to_expand:
            retrosynthesis_step(node, rules, side_graphs, buyables_set, side_set, max_depth, depth + 1, reaction_cache, stats)
    else:
        return True

def remove_counterions(smiles):
    mol = Chem.MolFromSmiles(smiles)
    frags = Chem.GetMolFrags(mol, asMols=True)
    largest = max(frags, key=lambda m: m.GetNumAtoms())
    # return Chem.MolToSmiles(largest)
    return Chem.MolToSmiles(largest, canonical=True)

def load_smiles_csv(file_path):
    import pandas as pd
    df = pd.read_csv(file_path)
    smiles = df["smiles"].dropna().tolist()
    # return set(filter(None, (remove_counterions(canonical_smiles(remove_stereo(s))) for s in smiles)))
    return set(df["smiles"].dropna().tolist())


def main():
    parser = argparse.ArgumentParser(description="Retrosynthesis CLI with mol_graph_creator")
    parser.add_argument("--buyables", required=True, help="CSV with buyable SMILES")
    parser.add_argument("--side-products", required=True, help="CSV with side product SMILES")
    parser.add_argument("--rules", required=True, help="Folder with .gml rules")
    parser.add_argument("--target", required=True, help="Target SMILES")
    parser.add_argument("--depth", type=int, default=3)
    args = parser.parse_args()

    # Load and canonicalize SMILES
    buyables_set = load_smiles_csv(args.buyables)

    side_products_set = load_smiles_csv(args.side_products)

    # Generate graphs using mol_graph_creator.py
    side_graphs = generate_graphs(args.side_products, addHs=False)

    # Load rules
    rules = [
        Rule.fromGMLFile(os.path.join(args.rules, f))
        for f in os.listdir(args.rules) if f.endswith(".gml")
    ]

    # Target
    target_smiles = canonical_smiles(args.target)
    if target_smiles is None:
        raise ValueError("Invalid target SMILES")

    root = RetroNode(target_smiles)

    # Initialize our tracking dictionary
    run_stats = {"visited": 0}

    timeout = retrosynthesis_step(
        root,
        rules,
        side_graphs,
        buyables_set,
        side_products_set,
        max_depth=args.depth,
        stats=run_stats
    )
    # print(root.to_dict())
    save_dot(root)
    save_json(root)
    print(run_stats["visited"], timeout)


if __name__ == "__main__":
    main()
