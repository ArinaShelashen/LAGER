"""
lager_runner.py – runs one LAGER search in a private, temporary folder.

This file knows nothing about the web. Any interface (Flask, Streamlit,
a script) can call run_search(). It calls rs_a_star_branched.py exactly
like you would in the terminal, with the script's own default settings.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
SEARCH_SCRIPT = REPO / "rs_a_star_branched.py"

# Defaults – change these if you want other standard inputs
# Default lists of starting materials: key -> (name on the web page, description, file)
DEFAULT_REACTANTS = {
    "small": ("Small inventory", "a subsample of the extended inventory", REPO / "small_inventory.csv"),
    "extended": ("Extended inventory", "building blocks from MolPort", REPO / "extended_inventory.csv"),
}
BUYABLES = DEFAULT_REACTANTS["small"][2]
SIDE_PRODUCTS = REPO / "side_products_clean.csv"
INV_RULES = REPO / "inv_rules"
FORWARD_RULES = REPO / "forward_rules"
TIMEOUT_SECONDS = 15 * 60


class SearchTimeout(Exception):
    pass


def run_search(target_smiles: str, on_log=print, buyables_csv: bytes | None = None,
               rule_files: list[Path] | None = None,
               forward_files: list[Path] | None = None, default_list: str = "small") -> list[dict]:
    """
    Run the A* search for one target.
    on_log(line) is called for every line the script prints.
    buyables_csv: the user's cleaned reactants list (CSV content);
    None = use the default list named by default_list (a key of DEFAULT_REACTANTS).
    rule_files: the retrosynthetic rules to use (.gml files); None = all default rules.
    forward_files: forward rules for the side-reaction check; None = all default ones.
    Returns a list of pathways: [{"json": str, "png": bytes | None}, ...]
    (empty list = no pathway found). The temporary folder is always deleted.
    """
    run_dir = Path(tempfile.mkdtemp(prefix="lager_run_"))
    try:
        # The search script loads forward_rules/ from its working folder.
        # Forward rules are always ALL rules (including ones the user switched off):
        # a reaction the user does not want to use can still happen as a side reaction.
        forward_dir = run_dir / "forward_rules"
        forward_dir.mkdir()
        for path in forward_files if forward_files is not None else sorted(FORWARD_RULES.glob("*.gml")):
            (forward_dir / path.name).symlink_to(path.resolve())

        # The selected retrosynthetic rules, as links in this run's own folder
        if rule_files is not None:
            if not rule_files:
                raise ValueError("No reaction rules selected.")
            rules_dir = run_dir / "inv_rules"
            rules_dir.mkdir()
            for path in rule_files:
                (rules_dir / path.name).symlink_to(path.resolve())
        else:
            rules_dir = INV_RULES
        # generate_graphs() writes a "<name>_graphs" folder next to the side-products
        # CSV. A private copy keeps those files inside this run's folder, so parallel
        # runs never write into the same place.
        shutil.copy(SIDE_PRODUCTS, run_dir / SIDE_PRODUCTS.name)

        if buyables_csv is not None:
            buyables = run_dir / "user_reactants.csv"
            buyables.write_bytes(buyables_csv)
        else:
            buyables = DEFAULT_REACTANTS[default_list][2]

        cmd = [
            sys.executable, str(SEARCH_SCRIPT),
            "--buyables", str(buyables),
            "--side-products", SIDE_PRODUCTS.name,
            "--rules", str(rules_dir),
            "--target", target_smiles,
        ]
        env = dict(os.environ, PYTHONUNBUFFERED="1")  # print() lines arrive immediately
        proc = subprocess.Popen(cmd, cwd=run_dir, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        start = time.time()
        for line in proc.stdout:
            on_log(line.rstrip())
            if time.time() - start > TIMEOUT_SECONDS:
                proc.kill()
                proc.wait()
                raise SearchTimeout(f"Search stopped after {TIMEOUT_SECONDS // 60} minutes.")
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError("The search script stopped with an error (see log).")

        return _collect_results(run_dir / "results")
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)  # nothing stays on disk


def _collect_results(res_dir: Path) -> list[dict]:
    pathways = []
    i = 1
    while (res_dir / f"optimal_pathway_{i}.json").exists():
        png = res_dir / f"pathway_{i}.png"
        pathways.append({
            "json": (res_dir / f"optimal_pathway_{i}.json").read_text(),
            "png": png.read_bytes() if png.exists() else None,
        })
        i += 1
    return pathways
