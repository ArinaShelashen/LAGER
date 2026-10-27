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
BUYABLES = REPO / "lab_reactants_clean.csv"
SIDE_PRODUCTS = REPO / "side_products_clean.csv"
INV_RULES = REPO / "inv_rules"
FORWARD_RULES = REPO / "forward_rules"
TIMEOUT_SECONDS = 15 * 60


class SearchTimeout(Exception):
    pass


def run_search(target_smiles: str, on_log=print) -> list[dict]:
    """
    Run the A* search for one target.
    on_log(line) is called for every line the script prints.
    Returns a list of pathways: [{"json": str, "png": bytes | None}, ...]
    (empty list = no pathway found). The temporary folder is always deleted.
    """
    run_dir = Path(tempfile.mkdtemp(prefix="lager_run_"))
    try:
        # The search script loads forward_rules/ from its working folder
        (run_dir / "forward_rules").symlink_to(FORWARD_RULES, target_is_directory=True)

        cmd = [
            sys.executable, str(SEARCH_SCRIPT),
            "--buyables", str(BUYABLES),
            "--side-products", str(SIDE_PRODUCTS),
            "--rules", str(INV_RULES),
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
