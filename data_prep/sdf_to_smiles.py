"""
sdf_to_smiles.py – convert SDF files (e.g. a lab's chemical inventory) into a CSV
with a 'smiles' column, ready for clean_molecules.py.

1. Every structure is read with RDKit.
2. Entries RDKit cannot read (no structure drawn, invalid valences, broken
   records) are looked up on PubChem by their CAS number, then by their name.
   This needs internet and the package `pubchempy`. Without internet, these
   entries are marked FAILED.

Command line:
    python data_prep/sdf_to_smiles.py Chemicals_list1.sdf -o reactants1.csv
    python data_prep/sdf_to_smiles.py Chemicals_list1.sdf -o reactants1.csv --no-pubchem

From Python (used by the LAGER web interface):
    from data_prep.sdf_to_smiles import sdf_to_rows
    rows = sdf_to_rows("Chemicals_list1.sdf")

The 'source' column says where each structure came from: RDKit, CAS, NAME or FAILED.
"""

import argparse
import re
import socket
import time
import urllib.error

from rdkit import Chem


# -------------------------------------------------------
# Read one SDF record at a time
# -------------------------------------------------------

def sdf_reader(filename, encoding="cp1252"):
    """
    Generator that yields complete SDF records while preserving
    the mol block formatting exactly.
    """
    with open(filename, "r", encoding=encoding, errors="replace") as f:

        lines = []

        for line in f:
            if line.startswith("$$$$"):
                if lines:
                    yield "".join(lines)
                    lines = []
            else:
                lines.append(line)

        if lines:
            yield "".join(lines)


# -------------------------------------------------------
# Parse property block
# -------------------------------------------------------

def parse_properties(text):

    props = {}

    current_key = None
    current_value = []

    for line in text.splitlines():

        m = re.match(r'>\s*<(.+?)>', line)

        if m:
            if current_key is not None:
                props[current_key] = "\n".join(current_value).strip()

            current_key = m.group(1).strip()
            current_value = []

        else:
            if current_key is not None:
                current_value.append(line)

    if current_key is not None:
        props[current_key] = "\n".join(current_value).strip()

    return props


# -------------------------------------------------------
# PubChem lookup (via pubchempy)
# -------------------------------------------------------

PUBCHEM_PAUSE = 0.25        # PubChem allows at most 5 requests per second
PUBCHEM_TIMEOUT = 15        # seconds until a request counts as "no connection"


class PubChemUnreachable(Exception):
    """No connection to PubChem (offline, firewall, ...)."""


def pubchem_lookup(query):
    """
    Returns the SMILES of the first PubChem compound matching a name or CAS
    number, or None if PubChem knows no such compound.
    Raises PubChemUnreachable if PubChem cannot be reached.
    """
    if not query:
        return None

    import pubchempy as pcp

    # pubchempy itself has no timeout; this sets one for its connections
    socket.setdefaulttimeout(PUBCHEM_TIMEOUT)

    for attempt in range(3):
        time.sleep(PUBCHEM_PAUSE)
        try:
            compounds = pcp.get_compounds(query, "name")
        except pcp.PubChemHTTPError as e:
            if "busy" in str(e).lower() and attempt < 2:   # PubChem overloaded: wait, retry
                time.sleep(2)
                continue
            return None                                      # e.g. not found, bad request
        except (urllib.error.URLError, OSError) as e:        # no connection / timeout
            raise PubChemUnreachable(str(e)) from e

        if not compounds:
            return None
        # PubChem renamed its SMILES fields in 2025 ("CanonicalSMILES" is now
        # "ConnectivitySMILES"). Newer pubchempy versions offer the new names;
        # older ones may return None for canonical_smiles.
        for attribute in ("connectivity_smiles", "canonical_smiles", "smiles"):
            try:
                smiles = getattr(compounds[0], attribute, None)
            except Exception:
                smiles = None
            if smiles:
                return smiles
        return None
    return None


# -------------------------------------------------------
# RDKit structure -> SMILES
# -------------------------------------------------------

def mol_to_smiles(mol):

    if mol is None:
        return None

    # Inventory entries without a drawn structure (e.g. mixtures, resins) have
    # 0 atoms; RDKit turns them into an empty SMILES "" – treat that as "not found"
    if mol.GetNumAtoms() == 0:
        return None

    try:
        Chem.SanitizeMol(mol)
        return Chem.MolToSmiles(mol, canonical=True) or None
    except Exception:
        return None


# -------------------------------------------------------
# Convert one record with RDKit
# -------------------------------------------------------

def record_to_row(record):
    """Returns a dict with ID, CAS, name, smiles, source – or None for a record without a mol block."""

    idx = record.find("M  END")

    if idx == -1:
        return None

    molblock = record[:idx + len("M  END")] + "\n"
    propblock = record[idx + len("M  END"):]

    # Parse structure
    mol = Chem.MolFromMolBlock(
        molblock,
        sanitize=False,
        removeHs=False,
        strictParsing=False,
    )

    props = parse_properties(propblock)

    ID = props.get("ID", "")

    CAS = (
        props.get("DDOP CAS number", "")
        or props.get("CAS", "")
    )

    NAME = (
        props.get("DDOP Chembase name", "")
        or props.get("Name", "")
        or props.get("DDOP Synonyms", "")
    )

    smiles = mol_to_smiles(mol)

    return {
        "ID": ID,
        "CAS": CAS,
        "name": NAME,
        "smiles": smiles or "",
        "source": "RDKit" if smiles else "FAILED"
    }


# -------------------------------------------------------
# Convert a whole file
# -------------------------------------------------------

def sdf_to_rows(sdf_file, use_pubchem=True, on_progress=None, progress_bar=False):
    """
    Converts all records of an SDF file.

    on_progress(done, total) is called during the PubChem lookups.
    Returns (rows, pubchem_reachable). Rows that could not be converted
    have smiles == '' and source == 'FAILED'.
    """

    # 1. RDKit for every record
    rows = [row for row in map(record_to_row, sdf_reader(sdf_file)) if row is not None]

    # 2. PubChem for the rest
    missing = [row for row in rows if row["source"] == "FAILED"]
    if not use_pubchem or not missing:
        return rows, True

    cache = {}  # the same CAS or name often appears several times in an inventory

    def cached_lookup(query):
        if query not in cache:
            cache[query] = pubchem_lookup(query)
        return cache[query]

    iterator = missing
    if progress_bar:
        from tqdm import tqdm
        iterator = tqdm(missing, desc="PubChem lookups")

    try:
        for i, row in enumerate(iterator, start=1):
            for query, source in ((row["CAS"], "CAS"), (row["name"], "NAME")):
                smiles = cached_lookup(query) if query else None
                if smiles:
                    row["smiles"], row["source"] = smiles, source
                    break
            if on_progress:
                on_progress(i, len(missing))
    except PubChemUnreachable:
        return rows, False

    return rows, True


def convert_sdf(sdf_file, output_csv, use_pubchem=True):

    import pandas as pd

    rows, reachable = sdf_to_rows(sdf_file, use_pubchem=use_pubchem, progress_bar=True)
    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)

    if not reachable:
        print("⚠️ PubChem could not be reached; structures RDKit could not read are marked FAILED.")
    print(f"Saved {len(df)} molecules to {output_csv}")
    if len(df):
        print(df["source"].value_counts().to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert an SDF file into a CSV with a 'smiles' column.")
    parser.add_argument("input_sdf", help="Path to the SDF file")
    parser.add_argument("-o", "--output", required=True, help="Path for the output CSV file")
    parser.add_argument("--no-pubchem", action="store_true",
                        help="Do not look up failed structures on PubChem (works offline)")
    args = parser.parse_args()

    convert_sdf(args.input_sdf, args.output, use_pubchem=not args.no_pubchem)
