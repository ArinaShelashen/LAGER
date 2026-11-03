"""
rule_gml.py – reads and writes MØD rules in GML and turns a rule around
(forward reaction <-> retrosynthetic rule), including its conditions.

Why not MØD's makeInverse? It refuses rules with conditions ("constraints") and
renumbers the atoms. Turning a rule around just swaps its left and right sides
(the context stays), so we do that directly and keep the atom ids – the
conditions can then still refer to the same atoms.

Conditions are checked on the LEFT side of a rule. After swapping, the left side
is the other molecule, so each condition is translated:

  constrainAdj (number of neighbours of an atom):
      Atoms outside the rule are never changed, so the number of neighbours on
      the new left side = old number + the change caused by the rule's own bonds.
      The condition is therefore translated exactly by shifting its count,
      e.g. "C has exactly 2 O neighbours" (acid) -> "exactly 1" (amide).
      If a neighbour inside the rule has a wildcard label (e.g. "_X"), it is
      unclear whether it counts, so the condition is left for review.
  constrainLabelAny (allowed values of a wildcard label): copied, if the
      wildcard still occurs on the new left side.
  all other conditions (e.g. constrainShortestPath): left for review.
"""

import re

# ---------------------------------------------------------------------------
# GML text <-> nested lists of [key, value]
# ---------------------------------------------------------------------------
_TOKEN = re.compile(r'\s+|#[^\n]*|\[|\]|"(?:\\.|[^"\\])*"|[^\s\[\]"]+')
_NUMBER = re.compile(r"-?\d+(\.\d+)?")


class GMLError(ValueError):
    pass


def _tokens(text):
    pos = 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise GMLError('A text in quotes ("…") is not closed.')
        tok = m.group(0)
        pos = m.end()
        if tok.isspace() or tok.startswith("#"):
            continue
        yield tok


def parse(text):
    """GML text -> list of [key, value]; value is str, int, float or a list."""
    toks = list(_tokens(text))
    i = 0

    def parse_list(top):
        nonlocal i
        items = []
        while i < len(toks):
            t = toks[i]
            if t == "]":
                if top:
                    raise GMLError("There is a ']' without a matching '['.")
                i += 1
                return items
            if t == "[" or t.startswith('"'):
                raise GMLError(f"Expected a key, found {t}.")
            i += 1
            if i >= len(toks):
                raise GMLError(f'The key "{t}" has no value.')
            v = toks[i]
            i += 1
            if v == "[":
                items.append([t, parse_list(False)])
            elif v.startswith('"'):
                items.append([t, v[1:-1].replace('\\"', '"').replace("\\\\", "\\")])
            elif _NUMBER.fullmatch(v):
                items.append([t, float(v) if "." in v else int(v)])
            else:
                raise GMLError(f'The key "{t}" has an invalid value "{v}".')
        if not top:
            raise GMLError("A '[' is not closed with ']'.")
        return items

    return parse_list(True)


def _value(v, indent):
    if isinstance(v, list):
        if not any(isinstance(x, list) for _, x in v):        # short list: one line
            return "[ " + " ".join(f"{k} {_value(x, indent)}" for k, x in v) + " ]"
        inner = "".join(f"{indent}\t{k} {_value(x, indent + chr(9))}\n" for k, x in v)
        return "[\n" + inner + indent + "]"
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return str(v)


def dump(items):
    """list of [key, value] -> GML text in MØD's usual layout."""
    return "".join(f"{k} {_value(v, '')}\n" for k, v in items)


def _get(items, key, default=None):
    for k, v in items:
        if k == key:
            return v
    return default


def _all(items, key):
    return [v for k, v in items if k == key]


def _labels(items):
    return [str(v) for k, v in (items or []) if k == "label"]


# ---------------------------------------------------------------------------
# Turning a rule around
# ---------------------------------------------------------------------------
def _side_graph(body, part):
    """Atom labels and bonds of one side (left or right), including the context."""
    labels, bonds = {}, []
    for section in ("context", part):
        content = _get(body, section) or []
        for node in _all(content, "node"):
            labels[_get(node, "id")] = str(_get(node, "label", ""))
        for edge in _all(content, "edge"):
            bonds.append((_get(edge, "source"), _get(edge, "target"), str(_get(edge, "label", ""))))
    return labels, bonds


def _neighbour_count(side, atom, node_labels, edge_labels):
    """
    Number of rule bonds of `atom` on one side that a constrainAdj counts.
    Returns None if a wildcard label makes it impossible to tell.
    """
    labels, bonds = side
    count = 0
    for s, t, bond in bonds:
        if atom not in (s, t):
            continue
        other = t if s == atom else s
        if edge_labels:
            if bond.startswith("_"):
                return None
            if bond not in edge_labels:
                continue
        if node_labels:
            label = labels.get(other, "")
            if label.startswith("_"):
                return None
            if label not in node_labels:
                continue
        count += 1
    return count


def _snippet(key, value):
    return dump([[key, value]]).strip()


def turn_around(text):
    """
    Swaps a rule's direction. Returns a dict:
        gml       the turned-around rule (with the translated conditions)
        copied    conditions copied unchanged            (GML snippets)
        adjusted  conditions with a translated count     ({"from", "to"} snippets)
        review    conditions that could not be translated (GML snippets)
    Raises GMLError for text that is not a readable rule.
    """
    top = parse(text)
    body = _get(top, "rule")
    if not isinstance(body, list):
        raise GMLError('The text must contain "rule [ … ]".')

    old_left = _side_graph(body, "left")       # checked by the old rule
    new_left = _side_graph(body, "right")      # checked by the new rule

    result = {"copied": [], "adjusted": [], "review": []}
    head, constraints, rest = [], [], []
    left = _get(body, "left")
    right = _get(body, "right")
    for key, value in body:
        if key in ("left", "context", "right"):
            continue
        if key.startswith("constrain"):
            constraints.append([key, value])
        elif key in ("ruleID", "labelType"):
            head.append([key, value])
        else:
            rest.append([key, value])

    new_body = list(head)
    if right is not None:
        new_body.append(["left", right])
    if _get(body, "context") is not None:
        new_body.append(["context", _get(body, "context")])
    if left is not None:
        new_body.append(["right", left])
    new_body += rest

    new_left_labels = set(new_left[0].values()) | {b for _, _, b in new_left[1]}
    for key, value in constraints:
        original = _snippet(key, value)
        if key == "constrainAdj" and isinstance(value, list):
            atom = _get(value, "id")
            node_labels = _labels(_get(value, "nodeLabels"))
            edge_labels = _labels(_get(value, "edgeLabels"))
            count = _get(value, "count")
            before = _neighbour_count(old_left, atom, node_labels, edge_labels)
            after = _neighbour_count(new_left, atom, node_labels, edge_labels)
            if atom not in new_left[0] or before is None or after is None or not isinstance(count, int):
                result["review"].append(original)
                continue
            new_count = count + (after - before)
            if new_count < 0:
                result["review"].append(original)
                continue
            if new_count == count:
                new_body.append([key, value])
                result["copied"].append(original)
            else:
                translated = [[k, new_count if k == "count" else v] for k, v in value]
                new_body.append([key, translated])
                result["adjusted"].append({"from": original, "to": _snippet(key, translated)})
        elif key == "constrainLabelAny" and isinstance(value, list):
            if str(_get(value, "label", "")) in new_left_labels:
                new_body.append([key, value])
                result["copied"].append(original)
            else:
                result["review"].append(original)
        else:
            result["review"].append(original)

    new_top = [[k, v] for k, v in top if k != "rule"]
    result["gml"] = dump([["rule", new_body]] + new_top)
    return result
