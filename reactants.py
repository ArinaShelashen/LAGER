"""
reactants.py – turns uploaded files into a cleaned list of available reactants.

Accepted files:
  * CSV with a column 'smiles' (comma- or semicolon-separated, e.g. from Excel)
  * SDF (e.g. exported from a chemical inventory); structures are read with RDKit,
    and entries RDKit cannot read are looked up on PubChem by CAS number or name

All files are combined, alkali/alkaline-earth salts are converted into their anion
(see below), and the rest is run through data_prep/clean_molecules.py (split salts
into their parts, neutralize, remove stereochemistry and isotopes, remove duplicates),
exactly like on the command line. Molecules with any element are kept (organometallics,
metal reagents): available molecules are only compared with the search's molecules.
Nothing is kept on disk.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
from rdkit import Chem

from data_prep.sdf_to_smiles import sdf_to_rows

REPO = Path(__file__).resolve().parent
CLEAN_SCRIPT = REPO / "data_prep" / "clean_molecules.py"

CSV_TYPES = {".csv"}
SDF_TYPES = {".sdf", ".sd"}
MAX_LISTED = 50

# Elements the reaction rules use as atom labels. Metals that a rule uses itself are
# not split into ions below.
INV_RULES = REPO / "inv_rules"
FALLBACK_ELEMENTS = {"H", "B", "C", "N", "O", "F", "Si", "P", "S", "Cl", "Br", "I", "Mg"}


def elements_in_rules(rules_dir: Path = INV_RULES) -> set[str]:
    """All element symbols that appear as atom labels (e.g. "C", "Br-", "Mg") in the .gml rules."""
    elements = set()
    for rule_file in rules_dir.glob("*.gml"):
        text = rule_file.read_text(encoding="utf-8", errors="replace")
        for label in re.findall(r'label\s+"([^"]*)"', text):
            match = re.fullmatch(r"([A-Z][a-z]?)\d*[+-]*\d*", label)
            if match:
                elements.add(match.group(1))
    return (elements | {"H"}) if elements else FALLBACK_ELEMENTS


RULE_ELEMENTS = elements_in_rules()

# Metals whose salts are ionic. Inventories often draw them as covalent molecules
# (KCN as N#C[K], NaI as [Na]I). The rules need the anion ([C-]#N, [I-], ...),
# so these bonds are broken into ions and the metal ion is dropped.
# Mg is not included: Grignard reagents must stay covalent (C-Mg-Br).
# Metals that a rule uses itself are left untouched.
IONIC_METALS = {"Li", "Na", "K", "Rb", "Cs", "Ca", "Sr", "Ba"} - RULE_ELEMENTS
METAL_IONS = IONIC_METALS | {"Mg", "Zn"}


def salt_to_ions(smiles: str) -> str | None:
    """
    Converts alkali/alkaline-earth metal salts into their anion, e.g.
    N#C[K] -> [C-]#N, [Na]I -> [I-], CC(=O)O[Na] -> CC(=O)[O-].
    Returns None if the entry consists only of metal ions (e.g. [Na+]).
    Other molecules are returned unchanged.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return smiles                   # invalid SMILES are removed by the cleaning step

    # 1. Bonds between an ionic metal and a non-metal become ions
    to_break = []
    for bond in mol.GetBonds():
        if bond.GetBondType() != Chem.BondType.SINGLE:
            continue
        a, b = bond.GetBeginAtom(), bond.GetEndAtom()
        for metal, partner in ((a, b), (b, a)):
            if metal.GetSymbol() in IONIC_METALS and partner.GetSymbol() not in METAL_IONS:
                if metal.GetSymbol() == "Li" and partner.GetSymbol() == "C":
                    continue            # organolithium reagents stay as they are
                to_break.append((metal.GetIdx(), partner.GetIdx()))

    rw = Chem.RWMol(mol)
    for metal_idx, partner_idx in to_break:
        rw.RemoveBond(metal_idx, partner_idx)
        metal = rw.GetAtomWithIdx(metal_idx)
        partner = rw.GetAtomWithIdx(partner_idx)
        metal.SetFormalCharge(metal.GetFormalCharge() + 1)
        metal.SetNoImplicit(True)
        partner.SetFormalCharge(partner.GetFormalCharge() - 1)
    try:
        Chem.SanitizeMol(rw)
    except Exception:
        return smiles                   # leave anything unusual to the other steps

    # 2. Drop metal cations that sit next to other fragments
    fragments = Chem.GetMolFrags(rw, asMols=True, sanitizeFrags=False)
    keep = [f for f in fragments
            if not (f.GetNumAtoms() == 1
                    and f.GetAtomWithIdx(0).GetSymbol() in METAL_IONS
                    and f.GetAtomWithIdx(0).GetFormalCharge() > 0)]
    if not keep:
        return None
    if len(keep) == len(fragments) and not to_break:
        return smiles                   # nothing changed
    return ".".join(Chem.MolToSmiles(f) for f in keep)


def _label(row) -> str:
    for column in ("name", "Name", "CAS", "ID"):
        value = row.get(column)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(row["smiles"])


class ReactantsError(Exception):
    """A problem with the user's files; the message is shown on the page."""


def _read_csv(path: Path, name: str) -> pd.DataFrame:
    df = None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            # sep=None detects ',' or ';' automatically
            df = pd.read_csv(path, sep=None, engine="python", encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise ReactantsError(f"{name}: the file could not be read as CSV ({e}).")
    if df is None:
        raise ReactantsError(f"{name}: unknown text encoding. Please save it as UTF-8 CSV.")

    columns = {str(c).strip().lower(): c for c in df.columns}
    if "smiles" not in columns:
        found = ", ".join(str(c) for c in df.columns[:10])
        raise ReactantsError(f"{name}: no column called 'smiles' (found: {found}).")
    return df.rename(columns={columns["smiles"]: "smiles"})


def _read_sdf(path: Path, name: str, report: dict, removed: list, on_progress) -> pd.DataFrame:
    def pubchem_progress(done, total):
        on_progress(f"{name}: looking up structures on PubChem ({done} of {total})…")

    on_progress(f"{name}: reading structures…")
    rows, reachable = sdf_to_rows(path, use_pubchem=True, on_progress=pubchem_progress)
    if not rows:
        raise ReactantsError(f"{name}: no molecules found in this SDF file.")
    if not reachable:
        report["pubchem_unreachable"] = True

    df = pd.DataFrame(rows)
    for source, column in (("RDKit", "n_rdkit"), ("CAS", "n_pubchem"), ("NAME", "n_pubchem")):
        report[column] += int((df["source"] == source).sum())
    unreadable = df[df["smiles"] == ""].copy()
    for row in unreadable.to_dict("records"):
        report["unreadable"].append(row["name"] or row["CAS"] or row["ID"] or "(no name)")
    unreadable["source_file"] = name
    unreadable["reason"] = "no structure found (RDKit and PubChem)"
    removed.append(unreadable)
    return df[df["smiles"] != ""]


def prepare_reactants(uploads: list[tuple[str, bytes]],
                      on_progress=lambda message: None) -> tuple[bytes, dict, bytes]:
    """
    uploads: list of (file name, file content).
    on_progress(message) is called with short status texts for the page.
    Returns the cleaned CSV, a report for the page, and a CSV of all removed
    entries with the reason (bytes).
    """
    tmp = Path(tempfile.mkdtemp(prefix="lager_reactants_"))
    report = {"files": [], "unreadable": [], "n_unreadable": 0,
              "metal_complexes": [], "n_metal_complexes": 0,
              "n_rdkit": 0, "n_pubchem": 0, "n_salts": 0, "pubchem_unreachable": False}
    removed = []                        # DataFrames of removed entries, with a "reason" column
    try:
        frames = []
        for i, (name, data) in enumerate(uploads):
            ext = Path(name).suffix.lower()
            path = tmp / f"upload_{i}{ext}"
            path.write_bytes(data)

            if ext in CSV_TYPES:
                on_progress(f"{name}: reading…")
                df = _read_csv(path, name)
            elif ext in SDF_TYPES:
                df = _read_sdf(path, name, report, removed, on_progress)
            else:
                raise ReactantsError(f"{name}: unsupported file type. Please upload .csv or .sdf files.")

            df["source_file"] = name
            report["files"].append({"name": name, "molecules": len(df)})
            frames.append(df)

        on_progress("Cleaning the molecules (salts, charges, stereochemistry, duplicates)…")

        combined = pd.concat(frames, ignore_index=True)
        if combined.empty:
            raise ReactantsError("None of the uploaded molecules could be read.")
        n_read = len(combined)

        # 1. Salts of Na, K, Cs, Ca, ... -> their anion (KCN -> [C-]#N, NaI -> [I-])
        combined["smiles"] = combined["smiles"].astype(str).str.strip()
        combined["original_smiles"] = combined["smiles"]
        combined["smiles"] = combined["smiles"].apply(salt_to_ions)
        only_ions = combined["smiles"].isna()
        report["n_salts"] = int((~only_ions & (combined["smiles"] != combined["original_smiles"])).sum())
        report["metal_complexes"] = sorted({_label(r) for r in combined[only_ions].to_dict("records")})
        report["n_metal_complexes"] = int(only_ions.sum())
        removed.append(combined[only_ions].assign(reason="only metal ions, no usable part"))
        combined = combined[~only_ions].drop(columns=["original_smiles"])
        if combined.empty:
            raise ReactantsError("The uploaded entries contain only metal ions.")

        raw_csv, clean_csv = tmp / "combined.csv", tmp / "clean.csv"
        combined.to_csv(raw_csv, index=False)
        result = subprocess.run(
            [sys.executable, str(CLEAN_SCRIPT), str(raw_csv), "-o", str(clean_csv)],
            cwd=tmp, capture_output=True, text=True,
        )
        if result.returncode != 0 or not clean_csv.exists():
            raise ReactantsError("Cleaning the molecules failed:\n"
                                 + (result.stdout + result.stderr)[-1500:])

        n_final = len(pd.read_csv(clean_csv))
        if n_final == 0:
            raise ReactantsError("None of the uploaded molecules could be read.")

        report["n_read"] = n_read
        report["n_final"] = n_final
        report["n_unreadable"] = len(report["unreadable"])
        report["unreadable"] = report["unreadable"][:MAX_LISTED]
        report["metal_complexes"] = report["metal_complexes"][:MAX_LISTED]

        # Full list of removed entries, for checking in Excel
        columns = [c for c in ("reason", "name", "CAS", "ID", "original_smiles", "smiles",
                               "source", "source_file") if any(c in r.columns for r in removed)]
        removed_df = pd.concat([r for r in removed if len(r)] or [pd.DataFrame(columns=columns)],
                               ignore_index=True).reindex(columns=columns)
        report["n_removed_listed"] = len(removed_df)
        return clean_csv.read_bytes(), report, removed_df.to_csv(index=False).encode()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def count_molecules(csv_path: Path) -> int:
    try:
        return len(pd.read_csv(csv_path))
    except Exception:
        return 0
