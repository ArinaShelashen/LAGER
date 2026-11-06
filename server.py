"""
server.py – LAGER web interface (Flask).

Start it from the LAGER folder with the conda environment active:
    conda activate mod_env
    python server.py
Then open http://localhost:5000 in your browser.

How it works:
  1. Optionally, the page uploads the user's reactants (CSV/SDF) to /api/reactants.
     They are read (SDF: RDKit, then PubChem for the rest) and cleaned in the
     background; the page asks /api/reactants/<id> for progress. The cleaned
     list is kept in memory under that id.
  2. The page sends the target SMILES (and that id) to /api/jobs.
  3. The server starts the search in a background thread and returns a job id
     (a search can take minutes – a normal web request would time out).
  4. The page asks /api/jobs/<id> every two seconds for status and log.
  5. When it's done, the page shows the pathway images and download links.
Everything is kept in memory only: results for one hour, reactant lists for
six hours after their last use.
"""

import hmac
import io
import threading
import time
import uuid
import zipfile

from flask import Flask, abort, jsonify, render_template, request, send_file
from rdkit import Chem

import os

import rules
from depict import molecule_svg as depict_molecule
from lager_runner import BUYABLES, SearchTimeout, run_search
from reactants import ReactantsError, count_molecules, prepare_reactants

# If set, deleting user-added rules needs this password (recommended on a shared server).
# On a personal computer it can stay unset.
ADMIN_PASSWORD = os.environ.get("LAGER_ADMIN_PASSWORD", "")

MAX_PARALLEL_SEARCHES = 2      # protects the computer from overload
KEEP_RESULTS_SECONDS = 60 * 60
KEEP_REACTANTS_SECONDS = 6 * 60 * 60
MAX_UPLOAD_MB = 100

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

jobs = {}                      # job id -> dict with status, log, results
reactant_sets = {}             # reactants id -> dict with cleaned CSV and report
store_lock = threading.Lock()
search_slots = threading.Semaphore(MAX_PARALLEL_SEARCHES)
DEFAULT_REACTANTS_COUNT = count_molecules(BUYABLES)


# ---------------------------------------------------------------------------
# Background work and housekeeping
# ---------------------------------------------------------------------------
def _run_job(job_id: str, smiles: str, buyables_csv: bytes | None, rule_files, forward_files):
    job = jobs[job_id]
    with search_slots:                      # waits here if too many searches run
        job["status"] = "running"
        try:
            job["pathways"] = run_search(smiles, on_log=job["log"].append,
                                         buyables_csv=buyables_csv,
                                         rule_files=rule_files, forward_files=forward_files)
            job["status"] = "done" if job["pathways"] else "no_pathway"
        except SearchTimeout as e:
            job["status"], job["error"] = "error", str(e)
        except Exception as e:
            job["status"], job["error"] = "error", str(e)


def _forget_old_data():
    now = time.time()
    with store_lock:
        for jid in [j for j, d in jobs.items() if now - d["created"] > KEEP_RESULTS_SECONDS]:
            del jobs[jid]
        for rid in [r for r, d in reactant_sets.items() if now - d["last_used"] > KEEP_REACTANTS_SECONDS]:
            del reactant_sets[rid]


def _get_job(job_id: str) -> dict:
    job = jobs.get(job_id)
    if job is None:
        abort(404)
    return job


@app.errorhandler(413)
def too_large(_):
    return jsonify(error=f"The files are too large (maximum {MAX_UPLOAD_MB} MB in total)."), 413


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html", default_name=BUYABLES.name,
                           default_count=DEFAULT_REACTANTS_COUNT)


# ---------------------------------------------------------------------------
# Reactants upload
# ---------------------------------------------------------------------------
def _prepare_job(reactants_id: str, uploads):
    entry = reactant_sets[reactants_id]

    def progress(message):
        entry["message"] = message

    try:
        entry["csv"], entry["report"], entry["removed_csv"] = prepare_reactants(
            uploads, on_progress=progress)
        entry["status"] = "done"
    except ReactantsError as e:
        entry["status"], entry["error"] = "error", str(e)
    except Exception as e:
        entry["status"], entry["error"] = "error", f"Unexpected error while reading the files: {e}"
    entry["last_used"] = time.time()


@app.post("/api/reactants")
def upload_reactants():
    _forget_old_data()
    uploads = [(f.filename, f.read()) for f in request.files.getlist("files") if f.filename]
    if not uploads:
        return jsonify(error="Please choose at least one .csv or .sdf file."), 400

    # Reading SDF files with PubChem lookups can take minutes, so it runs in the
    # background and the page asks for the status (like a search)
    reactants_id = uuid.uuid4().hex
    with store_lock:
        reactant_sets[reactants_id] = {"status": "running", "message": "Uploading…",
                                       "csv": None, "report": None, "error": None,
                                       "last_used": time.time()}
    threading.Thread(target=_prepare_job, args=(reactants_id, uploads), daemon=True).start()
    return jsonify(reactants_id=reactants_id), 202


@app.get("/api/reactants/<reactants_id>")
def reactants_status(reactants_id):
    entry = reactant_sets.get(reactants_id)
    if entry is None:
        abort(404)
    if entry["status"] == "done":
        return jsonify(status="done", reactants_id=reactants_id, **entry["report"])
    return jsonify(status=entry["status"], message=entry.get("message"), error=entry["error"])


@app.get("/api/reactants/<reactants_id>/removed.csv")
def download_removed(reactants_id):
    entry = reactant_sets.get(reactants_id)
    if entry is None or entry.get("removed_csv") is None:
        abort(404)
    return send_file(io.BytesIO(entry["removed_csv"]), mimetype="text/csv",
                     download_name="reactants_removed.csv", as_attachment=True)


@app.get("/api/reactants/<reactants_id>.csv")
def download_reactants(reactants_id):
    entry = reactant_sets.get(reactants_id)
    if entry is None or entry["csv"] is None:
        abort(404)
    return send_file(io.BytesIO(entry["csv"]), mimetype="text/csv",
                     download_name="reactants_clean.csv", as_attachment=True)


# ---------------------------------------------------------------------------
# Molecule pictures (rule guide)
# ---------------------------------------------------------------------------
@app.get("/api/depict")
def depict():
    smiles = request.args.get("smiles", "")
    try:
        centre = tuple(sorted(int(x) for x in request.args.get("centre", "").split(",") if x.strip()))
    except ValueError:
        centre = ()
    svg = depict_molecule(smiles, centre)
    if svg is None:
        abort(400)
    response = app.response_class(svg, mimetype="image/svg+xml")
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response


# ---------------------------------------------------------------------------
# Reaction rules
# ---------------------------------------------------------------------------
@app.get("/api/rules")
def list_rules():
    return jsonify(rules=rules.list_rules(), delete_needs_password=bool(ADMIN_PASSWORD))


@app.get("/api/rules/<rule_id>/gml")
def rule_gml(rule_id):
    forward = request.args.get("direction") == "forward"
    path = rules.forward_path(rule_id) if forward else rules.rule_path(rule_id)
    if path is None:
        abort(404)
    return send_file(path, mimetype="text/plain", download_name=path.name,
                     as_attachment=request.args.get("download") == "1")


@app.post("/api/rules/turn-around")
def turn_around_rule():
    """Forward rule -> proposed retrosynthetic rule (or the other way round)."""
    gml = (request.get_json(silent=True) or {}).get("gml", "")
    try:
        return jsonify(rules.turn_around(gml))
    except rules.RuleError as e:
        return jsonify(error=str(e)), 400


@app.post("/api/rules/check")
def check_rule():
    """Checks one or both rules of a pair with MØD."""
    data = request.get_json(silent=True) or {}
    try:
        for key, which in (("forward_gml", "The forward rule"), ("inverse_gml", "The retrosynthetic rule")):
            if key in data:
                rules.check_rule(data[key], which)
    except rules.RuleError as e:
        return jsonify(ok=False, error=str(e)), 400
    return jsonify(ok=True)


@app.post("/api/rules")
def add_rule():
    data = request.get_json(silent=True) or {}
    try:
        rule = rules.save_user_rule(data.get("name", ""), data.get("forward_gml", ""),
                                    data.get("inverse_gml", ""),
                                    author=data.get("author", ""),
                                    description=data.get("description", ""))
    except rules.RuleError as e:
        return jsonify(error=str(e)), 400
    return jsonify(rule=rule), 201


@app.delete("/api/rules/<rule_id>")
def delete_rule(rule_id):
    given = request.headers.get("X-Admin-Password", "")
    if ADMIN_PASSWORD and not hmac.compare_digest(given.encode(), ADMIN_PASSWORD.encode()):
        return jsonify(error="Wrong password."), 403
    try:
        rules.delete_user_rule(rule_id)
    except rules.RuleError as e:
        return jsonify(error=str(e)), 400
    return jsonify(ok=True)


# ---------------------------------------------------------------------------
# Searches
# ---------------------------------------------------------------------------
@app.post("/api/jobs")
def start_job():
    _forget_old_data()
    data = request.get_json(silent=True) or {}
    smiles = data.get("smiles", "").strip()
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return jsonify(error="Please enter or draw a valid molecule."), 400

    buyables_csv = None
    reactants_id = data.get("reactants_id")
    if reactants_id:
        entry = reactant_sets.get(reactants_id)
        if entry is None or entry["csv"] is None:
            return jsonify(error="Your uploaded reactants list has expired. "
                                 "Please upload it again."), 400
        entry["last_used"] = time.time()
        buyables_csv = entry["csv"]

    # Reaction rules: all rules except the ones the user switched off
    disabled = set(data.get("disabled_rules") or [])
    used = [r for r in rules.list_rules() if r["id"] not in disabled]
    if not used:
        return jsonify(error="Please select at least one reaction rule."), 400
    rule_files = [rules.rule_path(r["id"]) for r in used]
    forward_files = rules.forward_rule_files()

    job_id = uuid.uuid4().hex
    with store_lock:
        jobs[job_id] = {"status": "queued", "smiles": smiles, "log": [],
                        "pathways": [], "error": None, "created": time.time(),
                        "buyables_csv": buyables_csv, "rules_used": used,
                        "user_rule_files": [p for r, p in zip(used, rule_files) if r["source"] == "user"]}
    threading.Thread(target=_run_job, args=(job_id, smiles, buyables_csv, rule_files, forward_files),
                     daemon=True).start()
    return jsonify(job_id=job_id), 202


@app.get("/api/jobs/<job_id>")
def job_status(job_id):
    job = _get_job(job_id)
    return jsonify(
        status=job["status"],
        error=job["error"],
        log=job["log"][-30:],                 # last 30 lines are enough for the page
        n_pathways=len(job["pathways"]),
        has_png=[p["png"] is not None for p in job["pathways"]],
    )


@app.get("/api/jobs/<job_id>/pathway/<int:n>.png")
def pathway_png(job_id, n):
    pathways = _get_job(job_id)["pathways"]
    if not 1 <= n <= len(pathways) or pathways[n - 1]["png"] is None:
        abort(404)
    return send_file(io.BytesIO(pathways[n - 1]["png"]), mimetype="image/png",
                     download_name=f"pathway_{n}.png",
                     as_attachment=request.args.get("download") == "1")


@app.get("/api/jobs/<job_id>/pathway/<int:n>.json")
def pathway_json(job_id, n):
    pathways = _get_job(job_id)["pathways"]
    if not 1 <= n <= len(pathways):
        abort(404)
    return send_file(io.BytesIO(pathways[n - 1]["json"].encode()),
                     mimetype="application/json",
                     download_name=f"optimal_pathway_{n}.json", as_attachment=True)


@app.get("/api/jobs/<job_id>/all.zip")
def all_zip(job_id):
    job = _get_job(job_id)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n, p in enumerate(job["pathways"], start=1):
            z.writestr(f"optimal_pathway_{n}.json", p["json"])
            if p["png"]:
                z.writestr(f"pathway_{n}.png", p["png"])
        z.writestr("search_log.txt", "\n".join(job["log"]))
        # Record which starting materials were used, so the result is reproducible
        if job["buyables_csv"] is not None:
            z.writestr("reactants_used.csv", job["buyables_csv"])
        else:
            z.writestr("reactants_used.txt", f"Default list: {BUYABLES.name}\n")
        # ... and which reaction rules (user-added ones are included as files)
        z.writestr("rules_used.txt", "\n".join(
            f"{r['id']}" + ("   (user-added)" if r["source"] == "user" else "")
            for r in job["rules_used"]) + "\n")
        for path in job["user_rule_files"]:
            if path.exists():
                z.writestr(f"user_rules/{path.name}", path.read_text(encoding="utf-8"))
    buf.seek(0)
    return send_file(buf, mimetype="application/zip",
                     download_name="lager_results.zip", as_attachment=True)


if __name__ == "__main__":
    # 127.0.0.1 = only reachable from this computer. On a server this changes.
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
