"""
server.py – minimal LAGER web interface (Flask).

Start it from the LAGER folder with the conda environment active:
    conda activate mod_env
    python server.py
Then open http://localhost:5000 in your browser.

How it works:
  1. The page sends the target SMILES to /api/jobs.
  2. The server starts the search in a background thread and returns a job id
     (a search can take minutes – a normal web request would time out).
  3. The page asks /api/jobs/<id> every two seconds for status and log.
  4. When it's done, the page shows the pathway images and download links.
Results are kept in memory only, and forgotten after one hour.
"""

import io
import threading
import time
import uuid
import zipfile

from flask import Flask, abort, jsonify, render_template, request, send_file
from rdkit import Chem

from lager_runner import SearchTimeout, run_search

MAX_PARALLEL_SEARCHES = 2      # protects the computer from overload
KEEP_RESULTS_SECONDS = 60 * 60

app = Flask(__name__)
jobs = {}                      # job id -> dict with status, log, results
jobs_lock = threading.Lock()
search_slots = threading.Semaphore(MAX_PARALLEL_SEARCHES)


# ---------------------------------------------------------------------------
# Background work
# ---------------------------------------------------------------------------
def _run_job(job_id: str, smiles: str):
    job = jobs[job_id]
    with search_slots:                      # waits here if too many searches run
        job["status"] = "running"
        try:
            job["pathways"] = run_search(smiles, on_log=job["log"].append)
            job["status"] = "done" if job["pathways"] else "no_pathway"
        except SearchTimeout as e:
            job["status"], job["error"] = "error", str(e)
        except Exception as e:
            job["status"], job["error"] = "error", str(e)


def _forget_old_jobs():
    now = time.time()
    with jobs_lock:
        for jid in [j for j, d in jobs.items() if now - d["created"] > KEEP_RESULTS_SECONDS]:
            del jobs[jid]


def _get_job(job_id: str) -> dict:
    job = jobs.get(job_id)
    if job is None:
        abort(404)
    return job


# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/jobs")
def start_job():
    _forget_old_jobs()
    smiles = (request.get_json(silent=True) or {}).get("smiles", "").strip()
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return jsonify(error="Please enter or draw a valid molecule."), 400

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {"status": "queued", "smiles": smiles, "log": [],
                        "pathways": [], "error": None, "created": time.time()}
    threading.Thread(target=_run_job, args=(job_id, smiles), daemon=True).start()
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
    buf.seek(0)
    return send_file(buf, mimetype="application/zip",
                     download_name="lager_results.zip", as_attachment=True)


if __name__ == "__main__":
    # 127.0.0.1 = only reachable from this computer. On a server this changes.
    app.run(host="127.0.0.1", port=5000, debug=False)
