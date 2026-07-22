import argparse
import os
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import canonical_smiles, remove_stereo, remove_counterions


def cleaning_pipeline(s):
    """Wraps the pipeline and safely handles NaN/float values from Pandas."""
    if not isinstance(s, str):
        return None
    try:
        return remove_counterions(canonical_smiles(remove_stereo(s)))
    except Exception:
        return None


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
    # Create a temporary column with the cleaned SMILES
    df["clean_smiles"] = df["smiles"].apply(cleaning_pipeline)

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
    print(f"✅ Done! Shrunk from {original_count} to {final_count} unique, valid molecules. All metadata preserved.")


if __name__ == "__main__":
    main()