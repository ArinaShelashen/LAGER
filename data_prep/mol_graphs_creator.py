import argparse
import pandas as pd
from rdkit import Chem
from mod import *

def canonical_smiles(smiles: str, addHs=True) -> str | None:
    """
    Convert SMILES to RDKit canonical SMILES.
    Returns None if SMILES is invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    if addHs:
        mol = Chem.AddHs(mol)
    return Chem.MolToSmiles(mol, canonical=True)


def canonicalize_smiles_set(smiles_set, addHs=True):
    """
    Canonicalize a set of SMILES strings.
    Invalid SMILES are silently skipped.
    """
    canon = set()
    for s in smiles_set:
        cs = canonical_smiles(s, addHs)
        if cs is not None:
            canon.add(cs)
    return canon

def remove_counterions(smiles):
    mol = Chem.MolFromSmiles(smiles)
    frags = Chem.GetMolFrags(mol, asMols=True)
    largest = max(frags, key=lambda m: m.GetNumAtoms())

    Chem.SanitizeMol(largest)
    return Chem.MolToSmiles(largest)
    # return largest


def rdkit_to_mod_graph(mol, out_file):
    with open(out_file, "w") as f:
        f.write("graph [\n")

        for atom in mol.GetAtoms():
            f.write(f'  node [ id {atom.GetIdx()} label "{atom.GetSymbol()}" ]\n')

        for bond in mol.GetBonds():
            bond_map = {
                "SINGLE": "-",
                "DOUBLE": "=",
                "TRIPLE": "#",
                "AROMATIC": ":"
            }
            label = bond_map[str(bond.GetBondType())]
            f.write(
                f'  edge [ source {bond.GetBeginAtomIdx()} '
                f'target {bond.GetEndAtomIdx()} label "{label}" ]\n'
            )

        f.write("]\n")

def smiles_to_mod_graph(mol, out_file):
    mod_graph = Graph.fromSMILES(mol)
    gml_content = mod_graph.getGMLString()
    with open(out_file, "w") as f:
        f.write(gml_content)


def main(csv_file, output_dir, addHs=True):
    df = pd.read_csv(csv_file)

    for idx, row in df.iterrows():
        name = row["name"]
        smiles = row["smiles"]

        mol = remove_counterions(canonical_smiles(smiles, addHs))

        if mol is None:
            print(f"Failed to parse SMILES for {name}: {smiles}")
            continue

        out_file = f"{output_dir}/{name}.gml"
        # rdkit_to_mod_graph(mol, out_file)
        smiles_to_mod_graph(mol, out_file)
        # print(f"Saved {out_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert CSV of SMILES to MOD-compatible GML graphs."
    )
    parser.add_argument("csv_file", help="Input CSV file with 'name' and 'smiles' columns")
    parser.add_argument(
        "-o", "--output_dir", default=".", help="Directory to save GML files"
    )
    parser.add_argument(
        "-Hs", "--addHs", default="True", help="Add Hs to the molecules"
    )
    args = parser.parse_args()

    main(args.csv_file, args.output_dir, args.addHs)
