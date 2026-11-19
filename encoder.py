"""
encoder.py – creates draft reaction rules from example reactions, for the web page.

The work is done by data_prep/encode_reaction.py, which needs SynKit, SynRBL, RDKit
and MØD (all in environment.yml). It runs as a subprocess with the server's own Python.
To use another environment instead, set the environment variable LAGER_ENCODER_PYTHON, e.g.

    export LAGER_ENCODER_PYTHON=/path/to/conda/envs/other_env/bin/python
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
SCRIPT = REPO / "data_prep" / "encode_reaction.py"
PYTHON = os.environ.get("LAGER_ENCODER_PYTHON") or sys.executable
TIMEOUT_SECONDS = 180          # atom mapping has a time limit of 10 s per reaction

_available = None              # None = not checked yet, else (ok, message)


class EncoderError(Exception):
    pass


def run(request: dict) -> dict:
    """Send one request to encode_reaction.py and return its answer."""
    try:
        result = subprocess.run([PYTHON, str(SCRIPT)], input=json.dumps(request),
                                capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    except FileNotFoundError:
        raise EncoderError(f"The encoder Python was not found: {PYTHON}")
    except subprocess.TimeoutExpired:
        raise EncoderError(f"This took longer than {TIMEOUT_SECONDS // 60} minutes and was stopped. "
                           "Try smaller example molecules.")
    lines = result.stdout.strip().splitlines()
    try:
        answer = json.loads(lines[-1])
    except (IndexError, ValueError):
        raise EncoderError("The encoder stopped unexpectedly: "
                           + (result.stderr.strip().splitlines() or ["no output"])[-1])
    if "error" in answer:
        raise EncoderError(answer["error"])
    return answer


def available() -> tuple[bool, str]:
    """Is the encoder environment usable? Checked once, then remembered."""
    global _available
    if _available is None:
        try:
            run({"action": "env"})
            _available = (True, "")
        except EncoderError as e:
            _available = (False, f"{e} (Python: {PYTHON}). Install the environment from "
                                  "environment.yml (it has SynKit and SynRBL) and restart LAGER.")
    return _available
