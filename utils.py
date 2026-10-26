import sys
if 'mod' in sys.modules and 'rdkit.Chem.rdMolDraw2D' not in sys.modules:
    raise ImportError(
        "\n" + "="*80 + "\n"
        "🚨 CRITICAL IMPORT ERROR: MØD was loaded before RDKit!\n\n"
        "Because both use Boost.Python, loading MØD first permanently corrupts RDKit's C++ registry.\n"
        "To fix this, please ensure you import 'utils' and 'save_tree' BEFORE 'mod'.\n"
        + "="*80 + "\n"
    )
import os
import subprocess
from functools import lru_cache
from rdkit import Chem
from rdkit.Chem import RDConfig, rdFingerprintGenerator
sys.path.append(os.path.join(RDConfig.RDContribDir, 'SA_Score'))
import sascorer
import concurrent.futures
from mod import *
import multiprocessing as mp


# Common sensitive functional groups
FG_SMARTS = {
    "OH": Chem.MolFromSmarts("[#6,#15,#16;!$(C=O)][OX2H]"),  # Aliphatic/Aromatic OH (excludes water/acids)
    "SH": Chem.MolFromSmarts("[#6][SX2H]"),  # Aliphatic/Aromatic SH
    "NH": Chem.MolFromSmarts("[NX3;H2,H1;!$(NC=O)]"),  # Primary/Secondary amines (STRICTLY excludes amides)
    "COOH": Chem.MolFromSmarts("[CX3](=O)[OX2H1]"),  # Carboxylic acids
    # Carbon bound to Cl, Br, or I (excludes Fluorine, excludes inorganic salts like HCl)
    "HALOGEN": Chem.MolFromSmarts("[#6][Cl,Br,I]"),

    # Aldehydes and Ketones: Carbon double-bonded to Oxygen,
    # but STRICTLY NOT bonded to another O, N, or S (excludes esters, amides, acids, thioesters)
    "CARBONYL": Chem.MolFromSmarts("[CX3;!$(C(=O)[O,N,S])](=[OX1])"),

    # Terminal alkynes (Carbon triple bonded to a Carbon with a Hydrogen)
    "TERMINAL_ALKYNE": Chem.MolFromSmarts("[CX2H]#[CX2]"),

    # Boronic acids and esters: Carbon bound to a Boron that has two Oxygens attached
    "BORONIC": Chem.MolFromSmarts("[#6][BX3]([O])[O]")
}
AMINE_PATTERN = Chem.MolFromSmarts("[NX3;H1,H2;!$(NC=O)]")
COOH_PATTERN = Chem.MolFromSmarts("C(=O)[OH]")
ESTER_PATTERN = Chem.MolFromSmarts("C(=O)O[C]")
# Matches [2H] activated acid
ACTIVATED_ACID_PATTERN = Chem.MolFromSmarts("C(=O)O[2H]")


def canonical_smiles(smiles: str) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol, canonical=True)


def remove_stereo(smiles: str) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    for atom in mol.GetAtoms():
        atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    for bond in mol.GetBonds():
        bond.SetStereo(Chem.BondStereo.STEREONONE)
    return Chem.MolToSmiles(mol, canonical=True)

def remove_counterions(smiles):
    if smiles is None: return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None: return None
    frags = Chem.GetMolFrags(mol, asMols=True)
    largest = max(frags, key=lambda m: m.GetNumAtoms())
    return Chem.MolToSmiles(largest, canonical=True)


def load_smiles_csv(file_path):
    import pandas as pd
    df = pd.read_csv(file_path)
    smiles = df["smiles"].dropna().tolist()
    # return set(filter(None, (remove_counterions(canonical_smiles(remove_stereo(s))) for s in smiles)))
    return set(df["smiles"].dropna().tolist())


def generate_graphs(csv_file, addHs=True):
    output_file = csv_file.replace(".csv", "_graphs")
    os.makedirs(output_file, exist_ok=True)
    cmd = ["python", "data_prep/mol_graphs_creator.py", csv_file, "-o", output_file, "-Hs", str(addHs)]
    subprocess.run(cmd, check=True)
    gml_files = [os.path.join(output_file, f) for f in os.listdir(output_file) if f.endswith(".gml")]
    return [Graph.fromGMLFile(f) for f in gml_files]


def get_num_heavy_atoms(smiles: str) -> int:
    mol = Chem.MolFromSmiles(smiles)
    return mol.GetNumHeavyAtoms() if mol else 0


@lru_cache(maxsize=None)
def get_local_repetitiveness(smiles: str) -> float:
    """
    Measures LOCAL repetitiveness by counting unique Morgan environments.
    A ratio close to 1.0 means complex/asymmetric (like Paclitaxel).
    A higher ratio (e.g., > 2.0) means highly repetitive (like a polymer).
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return 1.0

    heavy_atoms = mol.GetNumHeavyAtoms()

    # We only care about large molecules crashing the engine
    if heavy_atoms < 20:
        return 1.0

    # --- NEW RDKIT GENERATOR API ---
    # 1. Initialize the Morgan Generator with radius 2
    mfp_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2)

    # 2. Create the AdditionalOutput object and allocate memory for the BitInfoMap
    ao = rdFingerprintGenerator.AdditionalOutput()
    ao.AllocateBitInfoMap()

    # 3. Generate the fingerprint and pass the AdditionalOutput object to catch the data
    mfp_gen.GetCountFingerprint(mol, additionalOutput=ao)

    # 4. Retrieve the dictionary mapping bits to (atom_index, radius)
    info = ao.GetBitInfoMap()

    # Count how many unique 2-bond neighborhoods exist in the molecule
    # We filter for radius == 2 to ignore single atoms/bonds which are common everywhere
    rad2_environments = [bit for bit, occurrences in info.items() if any(rad == 2 for _, rad in occurrences)]
    unique_envs = len(rad2_environments)

    if unique_envs == 0:
        return 1.0

    return heavy_atoms / unique_envs


def calculate_h_score(smiles: str, weight: float = 5.0) -> float:
    """
        Calculates h(n) using the Synthetic Accessibility (SA) Score.
        Scale is roughly 1.0 (easy/buyable) to 10.0 (hard/complex).
        """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 10.0  # Massive penalty if MØD generates an invalid SMILES

    # Calculate and return the SA score directly
    return sascorer.calculateScore(mol) * weight

def count_functional_groups(smiles: str) -> int:
    """Counts the total number of free OH, SH, NH, and COOH groups in a molecule."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0

    total_fgs = 0
    for fg_name, smarts_pattern in FG_SMARTS.items():
        # GetSubstructMatches returns a tuple of tuples containing atom indices
        matches = mol.GetSubstructMatches(smarts_pattern)
        total_fgs += len(matches)

    return total_fgs

def _forward_worker(unique_precursors, conn, forward_rules):
    """Runs in a forked child process — inherits `mod`/forward_rules via fork."""
    try:
        precursors_graphs = [Graph.fromSMILES(p) for p in unique_precursors]
        dg_side = DG(
            graphDatabase=precursors_graphs,
            labelSettings=LabelSettings(LabelType.Term, LabelRelation.Unification),
        )
        strat_side = addSubset(*precursors_graphs) >> forward_rules
        with dg_side.build() as builder:
            builder.execute(strat_side)

        reaction_names = [
            list(e.rules)[0].name.lower() if e.rules else "UnknownRule"
            for e in dg_side.edges
        ]
        conn.send(("ok", dg_side.numEdges, reaction_names))
    except Exception as e:
        conn.send(("error", str(e)))
    finally:
        conn.close()


def calculate_side_reactions(precursors, rule_name, forward_rules, forward_reaction_cache, timeout_seconds=30):
    """
    Simulates forward reactions to calculate side-product penalties.
    Runs MOD in a subprocess so a hang can be forcibly killed (signal-based
    timeouts don't work here: MOD is a C++ extension that never yields
    control back to the Python interpreter loop while it's stuck).
    """
    precursor_key = tuple(sorted(precursors))

    if precursor_key in forward_reaction_cache:
        return forward_reaction_cache[precursor_key]

    unique_precursors = set(precursors)

    parent_conn, child_conn = mp.Pipe()
    proc = mp.Process(target=_forward_worker, args=(unique_precursors, child_conn, forward_rules))
    proc.start()
    child_conn.close()  # parent doesn't need its copy of the child's end

    proc.join(timeout_seconds)

    if proc.is_alive():
        print(f"⚠️ MØD forward check timed out (> {timeout_seconds}s) on {unique_precursors}. Killing worker.")
        proc.terminate()      # SIGTERM first
        proc.join(2)
        if proc.is_alive():
            proc.kill()        # SIGKILL if it ignored SIGTERM
            proc.join()
        num_forward_reactions = 1
        side_reactions_names = [rule_name, "timeout_on_competing_reactions_manual_check_needed"]

    elif parent_conn.poll():
        status, *payload = parent_conn.recv()
        if status == "ok":
            num_forward_reactions, side_reactions_names = payload
        else:
            print(f"⚠️ Error during forward check: {payload[0]}. Applying fallback.")
            num_forward_reactions = 1
            side_reactions_names = [rule_name, "execution_error_penalty"]
    else:
        # process died without sending anything (e.g. segfault inside MOD)
        print(f"⚠️ MØD worker died unexpectedly on {unique_precursors}. Applying fallback.")
        num_forward_reactions = 1
        side_reactions_names = [rule_name, "execution_error_penalty"]

    if "reductive_amination" in rule_name:
        for side_rn in list(side_reactions_names):
            if "reduction" in side_rn:
                side_reactions_names.remove(side_rn)
                num_forward_reactions -= 1

    forward_reaction_cache[precursor_key] = (num_forward_reactions, side_reactions_names)
    return forward_reaction_cache[precursor_key]


def detect_unprotected_AA(unsolved_pool_smiles):
    """
    Scans the flask for incompatible functional groups.
    Returns True if the flask will violently self-react.
    """
    has_active_acid = False
    has_free_amine = False

    for smiles in unsolved_pool_smiles:
        mol = Chem.MolFromSmiles(smiles)
        if not mol: continue

        # Check for active acid
        if not has_active_acid and mol.HasSubstructMatch(ACTIVATED_ACID_PATTERN):
            has_active_acid = True

        # Check for free amine
        if not has_free_amine and mol.HasSubstructMatch(AMINE_PATTERN):
            has_free_amine = True

        # FAST FAIL: If the flask has both, it's a doomed branch. Kill it.
        if has_active_acid and has_free_amine:
            return True

    return False
