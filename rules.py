"""
rules.py – the reaction rules offered on the web page.

Two kinds of rules:
  * default rules: the files in inv_rules/ (retrosynthetic, *_inv.gml) and their
    forward versions in forward_rules/ (used to detect competing side reactions)
  * user rules: added through the web page and saved in USER_RULES_DIR
    (environment variable LAGER_USER_RULES, default: <repo>/user_rules).
    For each rule three files are stored:
        <name>_inv.gml   the retrosynthetic rule (used by the search)
        <name>.gml       the forward reaction (used for the side-reaction check)
        <name>.json      author, description, date

Every rule has an id: its file name without ".gml", e.g. "SN2_Cl_to_I_inv".
The search script uses this name, and treats some names specially
(e.g. names containing "protection" count as cheap helper steps).
"""

import json
import os
import re
import subprocess
import sys
import threading
from datetime import date
from pathlib import Path

import rule_gml

REPO = Path(__file__).resolve().parent
DEFAULT_INV_DIR = REPO / "inv_rules"
DEFAULT_FORWARD_DIR = REPO / "forward_rules"
USER_RULES_DIR = Path(os.environ.get("LAGER_USER_RULES", REPO / "user_rules"))
CHECK_SCRIPT = REPO / "data_prep" / "check_rule.py"

MAX_RULE_SIZE = 200_000          # characters; real rules are a few kB
NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-]{1,79}")

_save_lock = threading.Lock()


class RuleError(Exception):
    """A problem with a user's rule; the message is shown on the page."""


def display_name(rule_id: str) -> str:
    return rule_id.removesuffix("_inv").replace("_", " ").strip()


def _forward_name(inv_name: str) -> str:
    return inv_name.removesuffix("_inv")


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------
def list_rules() -> list[dict]:
    rules = []
    for path in sorted(DEFAULT_INV_DIR.glob("*.gml"), key=lambda p: p.name.lower()):
        rules.append({"id": path.stem, "name": display_name(path.stem), "source": "default"})

    if USER_RULES_DIR.exists():
        for path in sorted(USER_RULES_DIR.glob("*_inv.gml"), key=lambda p: p.name.lower()):
            meta = {}
            meta_file = path.with_name(_forward_name(path.stem) + ".json")
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                except ValueError:
                    pass
            rules.append({"id": path.stem, "name": display_name(path.stem), "source": "user",
                          "author": meta.get("author", ""), "description": meta.get("description", ""),
                          "created": meta.get("created", "")})
    return rules


def rule_path(rule_id: str) -> Path | None:
    """The inverse-rule file of a rule id, or None if there is no such rule."""
    # Looked up among the existing files only, so ids like "../x" can never escape
    for path in DEFAULT_INV_DIR.glob("*.gml"):
        if path.stem == rule_id:
            return path
    if USER_RULES_DIR.exists():
        for path in USER_RULES_DIR.glob("*_inv.gml"):
            if path.stem == rule_id:
                return path
    return None


def forward_path(rule_id: str) -> Path | None:
    """The forward rule that belongs to a retrosynthetic rule, if there is one."""
    inverse = rule_path(rule_id)
    if inverse is None:
        return None
    folder = DEFAULT_FORWARD_DIR if inverse.parent == DEFAULT_INV_DIR else USER_RULES_DIR
    path = folder / f"{_forward_name(rule_id)}.gml"
    return path if path.is_file() else None


def forward_rule_files() -> list[Path]:
    """All forward rules: default and user-added (always all, see lager_runner)."""
    files = sorted(DEFAULT_FORWARD_DIR.glob("*.gml"))
    if USER_RULES_DIR.exists():
        files += [p for p in sorted(USER_RULES_DIR.glob("*.gml")) if not p.stem.endswith("_inv")]
    return files


# ---------------------------------------------------------------------------
# Checking and saving user rules
# ---------------------------------------------------------------------------
def check_rule(gml: str, which: str = "The rule"):
    """Checks that MØD can read a rule; raises RuleError with MØD's message."""
    if not gml.strip():
        raise RuleError(f"{which} is empty.")
    if len(gml) > MAX_RULE_SIZE:
        raise RuleError(f"{which} is too large.")
    try:
        result = subprocess.run([sys.executable, str(CHECK_SCRIPT)], input=gml,
                                capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise RuleError("Checking the rule took too long.")
    try:
        data = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise RuleError(f"{which} could not be checked:\n" + (result.stderr or result.stdout)[-1000:])
    if not data.get("ok"):
        raise RuleError(f"MØD could not read {which[0].lower() + which[1:]}:\n"
                        + data.get("error", "unknown error"))


def turn_around(gml: str) -> dict:
    """Forward rule -> retrosynthetic rule (or back), with translated conditions."""
    if len(gml) > MAX_RULE_SIZE:
        raise RuleError("The rule is too large.")
    try:
        return rule_gml.turn_around(gml)
    except rule_gml.GMLError as e:
        raise RuleError(f"The rule cannot be read: {e}")


def normalize_name(name: str) -> str:
    """'My new rule' -> 'My_new_rule_inv' (the id used by the search)."""
    base = re.sub(r"\s+", "_", name.strip()).removesuffix(".gml").removesuffix("_inv")
    if not NAME_PATTERN.fullmatch(base):
        raise RuleError("Please use a name of 2–80 characters: letters, digits, '_' and '-' "
                        "(spaces become '_').")
    return base + "_inv"


def save_user_rule(name: str, forward_gml: str, inverse_gml: str,
                   author: str = "", description: str = "") -> dict:
    """
    Saves a rule pair: the forward reaction (used for the side-reaction check)
    and the retrosynthetic rule (used by the search), both checked by MØD.
    """
    rule_id = normalize_name(name)
    check_rule(forward_gml, "The forward rule")
    check_rule(inverse_gml, "The retrosynthetic rule")

    with _save_lock:
        existing = {r["id"].lower() for r in list_rules()}
        if rule_id.lower() in existing:
            raise RuleError(f"A rule called '{display_name(rule_id)}' already exists. "
                            "Please choose another name.")
        USER_RULES_DIR.mkdir(parents=True, exist_ok=True)
        forward = _forward_name(rule_id)
        (USER_RULES_DIR / f"{rule_id}.gml").write_text(inverse_gml, encoding="utf-8")
        (USER_RULES_DIR / f"{forward}.gml").write_text(forward_gml, encoding="utf-8")
        meta = {"author": author.strip()[:100], "description": description.strip()[:1000],
                "created": date.today().isoformat()}
        (USER_RULES_DIR / f"{forward}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"id": rule_id, "name": display_name(rule_id), "source": "user", **meta}


def delete_user_rule(rule_id: str):
    path = rule_path(rule_id)
    if path is None or path.parent.resolve() != USER_RULES_DIR.resolve():
        raise RuleError("Only rules added through the web page can be deleted.")
    forward = _forward_name(rule_id)
    with _save_lock:
        for p in (path, USER_RULES_DIR / f"{forward}.gml", USER_RULES_DIR / f"{forward}.json"):
            p.unlink(missing_ok=True)
