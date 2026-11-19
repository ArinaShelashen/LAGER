"""
encode_reaction.py – turns 1–4 example reactions into a draft MØD rule (forward direction).

Needs SynKit, SynRBL, RDKit and MØD (all in environment.yml; SynRBL needs Python >= 3.11).
The web server runs it as a subprocess
(see encoder.py). It reads one JSON request from stdin and prints one JSON answer:

  {"action": "env"}
  {"action": "prepare", "reactions": ["CC(=O)O.CO>>CC(=O)OC", ...]}
      -> per reaction: canonical SMILES, balanced or not, SynRBL's proposal
  {"action": "map", "reactions": ["<balanced rsmi>", ...]}
      -> per reaction: the possible atom mappings (SynKit), each with its bond changes
  {"action": "build", "mapped": ["<chosen mapped rsmi>", ...], "radius": 1, "context_h": false}
      -> forward rule (GML), notes on how the examples differ, suggested
         constrainAdj conditions, and a test of the rule on the examples
  {"action": "test", "gml": "...", "reactions": ["<rsmi>", ...]}
      -> does the rule turn the reactants of each example into its products?

Errors are answered as {"error": "..."}.

Rule atoms keep the atom-map numbers of the FIRST example as ids, so conditions
can refer to them. Hydrogens are explicit (MØD graphs have explicit H).
"""
import json
import sys
from collections import Counter

from rdkit import Chem  # noqa: F401  – RDKit must be loaded before MØD (Boost.Python)

MAX_CANDIDATES = 6            # atom mappings shown per reaction
BOND_LABELS = {1.0: "-", 1.5: ":", 2.0: "=", 3.0: "#"}
BOND_NAMES = {1.0: "single", 1.5: "aromatic", 2.0: "double", 3.0: "triple"}


class EncodeError(Exception):
    pass


# ---------------------------------------------------------------------------
# Reaction SMILES
# ---------------------------------------------------------------------------
def parse_reaction(rsmi: str) -> str:
    """Canonical 'reactants>>products' without atom maps; agents (R>A>P) are dropped."""
    from rdkit import Chem

    parts = rsmi.strip().split(">")
    if len(parts) != 3 or not parts[0] or not parts[2]:
        raise EncodeError("This is not a reaction SMILES. Write it as reactants>>products, "
                          "e.g. CC(=O)O.CO>>CC(=O)OC.O")

    def canon(side):
        smiles = []
        for s in side.split("."):
            mol = Chem.MolFromSmiles(s)
            if mol is None:
                raise EncodeError(f"RDKit cannot read the molecule {s}")
            for atom in mol.GetAtoms():
                atom.SetAtomMapNum(0)
            smiles.append(Chem.MolToSmiles(mol))
        return ".".join(smiles)

    return f"{canon(parts[0])}>>{canon(parts[2])}"


def element_balance(rsmi: str):
    """(balanced, {element: products - reactants}, charge difference)"""
    from rdkit import Chem

    def count(side):
        atoms, charge = Counter(), 0
        for s in side.split("."):
            mol = Chem.AddHs(Chem.MolFromSmiles(s))
            atoms.update(a.GetSymbol() for a in mol.GetAtoms())
            charge += Chem.GetFormalCharge(mol)
        return atoms, charge

    reac, prod = rsmi.split(">>")
    cr, qr = count(reac)
    cp, qp = count(prod)
    diff = {e: cp[e] - cr[e] for e in sorted(set(cr) | set(cp)) if cp[e] != cr[e]}
    return not diff and qr == qp, diff, qp - qr


def synrbl_balance(rsmi: str):
    """SynRBL's balanced reaction and the molecules it added, or (None, [])."""
    from synrbl import Balancer

    result = Balancer(n_jobs=1).rebalance(reactions=[rsmi], output_dict=True)[0]
    # the key name differs between SynRBL versions
    balanced = next((result[k] for k in ("reaction", "standardized_reactions", "rebalanced_reaction")
                     if isinstance(result.get(k), str) and ">>" in result[k]), None)
    if balanced is None:
        return None, []
    balanced = parse_reaction(balanced)
    if not element_balance(balanced)[0]:        # SynRBL found no solution
        return None, []

    def molecules(r):
        reac, prod = r.split(">>")
        return Counter(reac.split(".") + prod.split("."))

    added = list((molecules(balanced) - molecules(rsmi)).elements())
    return balanced, added


def prepare(reactions):
    out = []
    for raw in reactions:
        entry = {"input": raw}
        try:
            rsmi = parse_reaction(raw)
            ok, diff, dq = element_balance(rsmi)
            entry.update(rsmi=rsmi, balanced=ok, difference=diff, charge_difference=dq)
            if not ok:
                entry["proposal"], entry["added"] = synrbl_balance(rsmi)
        except EncodeError as e:
            entry["error"] = str(e)
        out.append(entry)
    return {"reactions": out}


# ---------------------------------------------------------------------------
# ITS graph (SynKit): node attribute typesGH = (before, after) with the charge at
# index 3 and the neighbour elements at index 4; edge attribute order = (before, after)
# ---------------------------------------------------------------------------
def its_graph(mapped: str):
    from synkit.IO import rsmi_to_its
    return rsmi_to_its(mapped, core=False)


def charges(its, n):
    before, after = its.nodes[n]["typesGH"]
    return before[3], after[3]


def atom_label(element: str, charge: int) -> str:
    if not charge:
        return element
    return f"{element}{abs(charge) if abs(charge) > 1 else ''}{'+' if charge > 0 else '-'}"


def atom_name(its, n) -> str:
    return f"{its.nodes[n]['element']}{n}"


def core_nodes(its) -> set:
    """Atoms whose bonds or charge change."""
    nodes = {n for u, v, d in its.edges(data=True) if d["order"][0] != d["order"][1] for n in (u, v)}
    return nodes | {n for n in its.nodes if charges(its, n)[0] != charges(its, n)[1]}


def rule_nodes(its, radius: int, context_h: bool) -> set:
    nodes = core_nodes(its)
    for _ in range(radius):
        nodes |= {nb for n in nodes for nb in its.neighbors(n)
                  if context_h or its.nodes[nb]["element"] != "H"}
    return nodes


def changes(its) -> list[str]:
    """The bond and charge changes as sentences, e.g. 'C2–O4 single bond broken'."""
    out = []
    for u, v, d in sorted(its.edges(data=True), key=lambda e: (min(e[0], e[1]), max(e[0], e[1]))):
        a, b = d["order"]
        bond = f"{atom_name(its, min(u, v))}–{atom_name(its, max(u, v))}"
        if a == b:
            continue
        if not b:
            out.append(f"{bond} {BOND_NAMES.get(a, a)} bond broken")
        elif not a:
            out.append(f"{bond} {BOND_NAMES.get(b, b)} bond formed")
        else:
            out.append(f"{bond} {BOND_NAMES.get(a, a)} → {BOND_NAMES.get(b, b)} bond")
    for n in sorted(core_nodes(its)):
        a, b = charges(its, n)
        if a != b:
            out.append(f"{atom_name(its, n)} charge {a:+d} → {b:+d}")
    return out


def to_gml(its, nodes, wildcards=None) -> str:
    """
    Forward rule from the ITS atoms 'nodes' (ids = atom-map numbers).
    wildcards: {atom: [allowed labels]} – these context atoms get the label "_X<atom>"
    and a constrainLabelAny with the allowed labels.
    """
    wildcards = wildcards or {}
    left, context, right = [], [], []
    for n in sorted(nodes):
        element = its.nodes[n]["element"]
        a, b = (atom_label(element, q) for q in charges(its, n))
        if n in wildcards:
            context.append(f'node [ id {n} label "_X{n}" ]')
        elif a == b:
            context.append(f'node [ id {n} label "{a}" ]')
        else:
            left.append(f'node [ id {n} label "{a}" ]')
            right.append(f'node [ id {n} label "{b}" ]')
    for u, v, d in sorted(its.subgraph(nodes).edges(data=True), key=lambda e: (min(e[0], e[1]), max(e[0], e[1]))):
        u, v = min(u, v), max(u, v)
        a, b = d["order"]
        if a == b:
            context.append(f'edge [ source {u} target {v} label "{BOND_LABELS[a]}" ]')
            continue
        if a:
            left.append(f'edge [ source {u} target {v} label "{BOND_LABELS[a]}" ]')
        if b:
            right.append(f'edge [ source {u} target {v} label "{BOND_LABELS[b]}" ]')

    def block(name, lines):
        return f"\t{name} [\n" + "".join(f"\t\t{line}\n" for line in lines) + "\t]\n"

    conditions = "".join(f'\tconstrainLabelAny [ label "_X{n}" labels [ '
                         + " ".join(f'label "{label}"' for label in labels) + " ] ]\n"
                         for n, labels in sorted(wildcards.items()))
    return ('rule [\n\tlabelType "term"\n' + block("left", left) + block("context", context)
            + block("right", right) + conditions + "]\n")


# ---------------------------------------------------------------------------
# Comparing examples
# ---------------------------------------------------------------------------
def _same_atom(its_a, a, its_b, b) -> bool:
    return its_a.nodes[a]["element"] == its_b.nodes[b]["element"] and charges(its_a, a) == charges(its_b, b)


def core_matches(its_a, its_b, limit=200):
    """Isomorphisms between the reaction centres of two ITS graphs (atom a -> atom b)."""
    from networkx.algorithms.isomorphism import GraphMatcher

    ca, cb = its_a.subgraph(core_nodes(its_a)), its_b.subgraph(core_nodes(its_b))
    if ca.number_of_nodes() != cb.number_of_nodes():
        return []
    matcher = GraphMatcher(ca, cb,
                           node_match=lambda x, y: x["element"] == y["element"]
                           and x["typesGH"][0][3] == y["typesGH"][0][3]
                           and x["typesGH"][1][3] == y["typesGH"][1][3],
                           edge_match=lambda x, y: tuple(x["order"]) == tuple(y["order"]))
    out = []
    for iso in matcher.isomorphisms_iter():
        out.append(iso)
        if len(out) >= limit:
            break
    return out


def anchor(ref, keep: set, other):
    """
    Map the rule atoms 'keep' of the reference ITS onto another example: reaction
    centre to reaction centre, then outwards through bonds with the same order,
    preferring atoms with the same element. An atom outside the reaction centre may
    be mapped to a different element (e.g. Cl -> Br); the rule then gets a wildcard
    there. Returns the largest mapping (fewest different elements first), or None
    if the reaction centres differ.
    """
    best, best_score = None, None
    for iso in core_matches(ref, other):
        mapping, used = dict(iso), set(iso.values())
        frontier = list(iso)
        while frontier:
            n = frontier.pop()
            for rn in ref.neighbors(n):
                if rn not in keep or rn in mapping:
                    continue
                order = tuple(ref.edges[n, rn]["order"])
                options = [on for on in other.neighbors(mapping[n])
                           if on not in used and tuple(other.edges[mapping[n], on]["order"]) == order]
                match = next((on for on in options if _same_atom(ref, rn, other, on)),
                             options[0] if options else None)
                if match is not None:
                    mapping[rn] = match
                    used.add(match)
                    frontier.append(rn)
        different = sum(not _same_atom(ref, n, other, m) for n, m in mapping.items())
        score = (len(mapping), -different)
        if best is None or score > best_score:
            best, best_score = mapping, score
    return best


def node_label(its, n) -> str:
    """Label of an atom outside the reaction centre (its charge does not change)."""
    return atom_label(its.nodes[n]["element"], charges(its, n)[0])


def map_reactions(reactions):
    from synkit.Chem.Mapper import map_reaction

    out = []
    for rsmi in reactions:
        entry = {"rsmi": rsmi, "candidates": []}
        try:
            rsmi = parse_reaction(rsmi)
            if not element_balance(rsmi)[0]:
                raise EncodeError("The reaction is not balanced.")
            result = map_reaction(rsmi, hydrogen="explicit", balance="strict")
            if not result.complete:
                entry["warning"] = ("The mapping search stopped early (time limit), "
                                    "so other mappings may exist.")
            mapped_all = list(result.mapped_reactions)
            if len(mapped_all) > MAX_CANDIDATES:
                entry["warning"] = f"{len(mapped_all)} mappings found; only the first {MAX_CANDIDATES} are shown."
            for mapped in mapped_all[:MAX_CANDIDATES]:
                its = its_graph(mapped)
                entry["candidates"].append({"mapped": mapped, "changes": changes(its),
                                            "gml": to_gml(its, rule_nodes(its, 1, False))})
            if not entry["candidates"]:
                raise EncodeError("SynKit found no atom mapping for this reaction.")
        except EncodeError as e:
            entry["error"] = str(e)
        except Exception as e:                       # SynKit errors
            entry["error"] = f"Atom mapping failed: {e}"
        out.append(entry)

    # With several examples: mark mappings whose reaction centre also occurs in every
    # other example – those describe the same transformation
    graphs = [[its_graph(c["mapped"]) for c in e["candidates"]] for e in out]
    if len(out) > 1 and all(graphs):
        for i, entry in enumerate(out):
            for c, g in zip(entry["candidates"], graphs[i]):
                c["consistent"] = all(any(core_matches(g, h, limit=1) for h in graphs[j])
                                      for j in range(len(out)) if j != i)
    return {"reactions": out}


# ---------------------------------------------------------------------------
# Building the rule
# ---------------------------------------------------------------------------
def suggest_conditions(ref, others, mappings) -> list[dict]:
    """
    constrainAdj conditions that hold in every example: for each heavy atom of the
    reaction centre, the number of neighbours of each element in the reactants
    (e.g. 'C2 has exactly 2 O neighbours' = carboxylic acid, not ester).
    """
    def neighbour_count(its, n, element):
        return its.nodes[n]["typesGH"][0][4].count(element)

    out = []
    for n in sorted(core_nodes(ref)):
        if ref.nodes[n]["element"] == "H":
            continue
        elements = set(ref.nodes[n]["typesGH"][0][4]) | {"H"}
        for its, mapping in zip(others, mappings):
            elements |= set(its.nodes[mapping[n]]["typesGH"][0][4])
        for element in sorted(elements):
            count = neighbour_count(ref, n, element)
            if any(neighbour_count(its, mapping[n], element) != count
                   for its, mapping in zip(others, mappings)):
                continue
            where = "in all examples" if others else "in the example"
            plural = "" if count == 1 else "s"
            out.append({
                "text": f"{atom_name(ref, n)} has exactly {count} {element} neighbour{plural} {where}",
                "gml": f'constrainAdj [\n\tid {n}\n\top "="\n\tcount {count}\n'
                       f'\tnodeLabels [ label "{element}" ]\n]',
            })
    return out


def build(mapped, radius=1, context_h=False):
    if not mapped:
        raise EncodeError("No reactions given.")
    ref = its_graph(mapped[0])
    keep = rule_nodes(ref, radius, context_h)
    others, mappings, notes = [], [], []
    for i, m in enumerate(mapped[1:], start=2):
        its = its_graph(m)
        mapping = anchor(ref, keep, its)
        if mapping is None:
            raise EncodeError(f"Reaction {i} has a different reaction centre from reaction 1 "
                              "(different bonds change). Choose another atom mapping, or use "
                              "examples of the same reaction type.")
        dropped = sorted(keep - set(mapping))
        if dropped:
            notes.append(f"Reaction {i} differs from reaction 1 at "
                         f"{', '.join(atom_name(ref, n) for n in dropped)}, so "
                         f"{'this atom was' if len(dropped) == 1 else 'these atoms were'} "
                         "left out of the rule.")
            keep -= set(dropped)
        others.append(its)
        mappings.append(mapping)
    mappings = [{n: m[n] for n in keep} for m in mappings]

    # Atoms that are different elements in the examples become wildcards
    wildcards = {}
    for n in sorted(keep):
        labels = {node_label(ref, n)} | {node_label(its, m[n]) for its, m in zip(others, mappings)}
        if len(labels) > 1:
            wildcards[n] = sorted(labels)
            notes.append(f"{atom_name(ref, n)} is {' or '.join(sorted(labels))} in the examples, so it "
                         f"became the wildcard _X{n} (allowed: {', '.join(sorted(labels))}). "
                         "You can allow more elements in step 1 (constrainLabelAny).")
    gml = to_gml(ref, keep, wildcards)
    reactions = [plain_reaction(m) for m in mapped]
    return {"gml": gml, "notes": notes, "changes": changes(ref),
            "suggestions": suggest_conditions(ref, others, mappings),
            "tests": test_rule(gml, reactions)}


def plain_reaction(mapped: str) -> str:
    from synkit.Chem.Reaction import remove_explicit_H_from_rsmi
    return parse_reaction(remove_explicit_H_from_rsmi(mapped))


# ---------------------------------------------------------------------------
# Testing the rule with MØD (forward direction)
# ---------------------------------------------------------------------------
def test_rule(gml: str, reactions) -> list[dict]:
    import mod

    try:
        rule = mod.Rule.fromGMLString(gml, add=False)
    except Exception as e:
        raise EncodeError(f"MØD cannot read the rule: {e}")
    out = []
    for rsmi in reactions:
        reac, prod = parse_reaction(rsmi).split(">>")
        start = [mod.Graph.fromSMILES(s, add=False) for s in reac.split(".")]
        targets = [mod.Graph.fromSMILES(s, add=False) for s in prod.split(".")]
        # Term labels like the search. The search uses Unification, which newer MØD
        # versions refuse here. Specialisation matches the same for these rules (their
        # wildcards like _X4 match any atom label of the molecules).
        dg = mod.DG(graphDatabase=start,
                    labelSettings=mod.LabelSettings(mod.LabelType.Term, mod.LabelRelation.Specialisation))
        with dg.build() as b:
            b.execute(mod.addSubset(start) >> rule)
        produced = [v.graph for v in dg.vertices]
        missing = [t.smiles for t in targets if not any(t.isomorphism(p) > 0 for p in produced)]
        out.append({"reaction": rsmi, "ok": not missing, "missing": missing})
    return out


# ---------------------------------------------------------------------------
def handle(request: dict) -> dict:
    action = request.get("action")
    if action == "env":
        import mod, synkit, synrbl  # noqa: F401  (fails if something is missing)
        return {"ok": True, "synkit": getattr(synkit, "__version__", "?")}
    if action == "prepare":
        return prepare(request.get("reactions") or [])
    if action == "map":
        return map_reactions(request.get("reactions") or [])
    if action == "build":
        return build(request.get("mapped") or [], int(request.get("radius", 1)),
                     bool(request.get("context_h", False)))
    if action == "test":
        return {"tests": test_rule(request.get("gml", ""), request.get("reactions") or [])}
    raise EncodeError(f"Unknown action {action!r}")


def main():
    answer_to = sys.stdout
    sys.stdout = sys.stderr            # SynRBL, SynKit and MØD print; keep stdout for the answer
    try:
        answer = handle(json.loads(sys.stdin.read() or "{}"))
    except EncodeError as e:
        answer = {"error": str(e)}
    except ImportError as e:
        answer = {"error": f"A package is missing in the encoder environment: {e}"}
    except Exception as e:
        answer = {"error": f"{type(e).__name__}: {e}"}
    answer_to.write(json.dumps(answer) + "\n")


if __name__ == "__main__":
    main()
