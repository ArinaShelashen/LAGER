"""
clean_molecules.py – cleans a list of available reactants (CSV with a 'smiles' column).

For every entry:
  * stereochemistry and isotope labels are removed (deuterated compounds become the
    normal compound: LAGER uses the label 2H as the activator marker, see side_products_clean.csv,
    so do NOT run this script on the side-product list)
  * every part of a salt or mixture becomes its own entry, e.g. an amine hydrochloride
    gives the amine and HCl, a TFA salt the amine and TFA. Bare metal cations ([Na+], ...)
    are dropped; anions ([I-], [Cl-], ...) are kept because some rules use them.
  * protonated amines are neutralized (R-NH3+ -> R-NH2), zwitterions become the neutral
    amino acid
  * a carboxylate (R-COO-) is kept as the anion AND as the acid (R-COOH): a chemist can
    use either
Then duplicates are removed. All other columns are kept (of the first occurrence).
"""
import argparse
import os
import pandas as pd
from rdkit import Chem

# Protonated nitrogen with H (ammonium, pyridinium-H), not N+ bonded to a negative atom (nitro, N-oxide)
PROTONATED_N = Chem.MolFromSmarts("[#7+;!H0;!$([#7+]~[#8-,#7-,#16-,#6-])]")
CARBOXYLATE_O = Chem.MolFromSmarts("[CX3](=O)[O-]")
NON_METALS = {"H", "He", "B", "C", "N", "O", "F", "Ne", "Si", "P", "S", "Cl", "Ar", "As", "Se",
              "Br", "Kr", "Te", "I", "Xe", "At", "Rn"}


def _add_h(atom, change):
    """Changes the charge of an atom by `change` and its hydrogens by the same amount (+H+ / -H+)."""
    atom.SetNumExplicitHs(max(0, atom.GetTotalNumHs() + change))
    atom.SetNoImplicit(True)
    atom.SetFormalCharge(atom.GetFormalCharge() + change)


def _smiles(mol):
    try:
        Chem.SanitizeMol(mol)
        return Chem.MolToSmiles(mol, canonical=True) or None
    except Exception:
        return None


def clean_entry(s):
    """One input SMILES -> list of cleaned SMILES (see the top of the file). [] if unreadable."""
    if not isinstance(s, str):
        return []
    mol = Chem.MolFromSmiles(s)
    if mol is None:
        return []
    Chem.RemoveStereochemistry(mol)
    for atom in mol.GetAtoms():
        atom.SetIsotope(0)
    mol = Chem.RemoveHs(mol)                      # former [2H] atoms become implicit H

    results = []
    for fragment in Chem.GetMolFrags(mol, asMols=True):
        if fragment.GetNumAtoms() == 1:
            atom = fragment.GetAtomWithIdx(0)
            if atom.GetFormalCharge() > 0 and atom.GetSymbol() not in NON_METALS:
                continue                          # bare metal cation, e.g. [Na+]
        fragment = Chem.RWMol(fragment)
        protonated = [m[0] for m in fragment.GetSubstructMatches(PROTONATED_N)]
        carboxylate = [m[2] for m in fragment.GetSubstructMatches(CARBOXYLATE_O)]
        for idx in protonated:
            _add_h(fragment.GetAtomWithIdx(idx), -1)
        if protonated and carboxylate:            # zwitterion -> neutral amino acid only
            for idx in carboxylate:
                _add_h(fragment.GetAtomWithIdx(idx), +1)
            carboxylate = []
        smiles = _smiles(fragment)
        if smiles:
            results.append(smiles)
        if carboxylate:                           # also the acid
            acid = Chem.RWMol(fragment)
            for idx in carboxylate:
                _add_h(acid.GetAtomWithIdx(idx), +1)
            acid_smiles = _smiles(acid)
            if acid_smiles:
                results.append(acid_smiles)
    return results


def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Clean, canonicalize, and deduplicate SMILES strings in a CSV file."
    )

    # Add a required positional argument for the input file
    parser.add_argument(
        "input_csv",
        help="Path to the input CSV file containing a 'smiles' column."
    )

    # Add an optional argument for the output file name
    parser.add_argument(
        "-o", "--output",
        help="Path for the output CSV file (defaults to appending '_clean' to the input name).",
        default=None
    )

    args = parser.parse_args()
    input_file = args.input_csv

    # Safety check, whether the file exist
    if not os.path.exists(input_file):
        print(f"❌ Error: The file '{input_file}' does not exist.")
        return

    # Determine output filename if not provided
    if args.output:
        output_file = args.output
    else:
        base_name, ext = os.path.splitext(input_file)
        output_file = f"{base_name}_clean{ext}"

    print(f"📂 Loading dataset: {input_file}")
    df = pd.read_csv(input_file)

    # Safety check: does the column exist?
    if "smiles" not in df.columns:
        print("❌ Error: The CSV file must contain a 'smiles' column.")
        return

    original_count = len(df)

    print("🧪 Cleaning and canonicalizing SMILES...")
    # Create a temporary column with the cleaned SMILES; one row per part of a salt or mixture
    df["clean_smiles"] = df["smiles"].apply(clean_entry)
    df = df.explode("clean_smiles")

    print("🧹 Removing invalid molecules and duplicates...")
    # 1. Drop rows where RDKit failed to parse the SMILES
    df = df.dropna(subset=["clean_smiles"])

    # 2. Drop duplicates. Keeps the first one and its metadata, dropping the rest.
    df = df.drop_duplicates(subset=["clean_smiles"])

    # 3. Replace the old SMILES column with our clean one, and drop the temp column
    df["smiles"] = df["clean_smiles"]
    df = df.drop(columns=["clean_smiles"])

    print(f"💾 Saving cleaned dataset to '{output_file}'...")
    df.to_csv(output_file, index=False)

    final_count = len(df)
    print(f"✅ Done! {original_count} entries gave {final_count} unique, valid molecules. All metadata preserved.")


if __name__ == "__main__":
    main()