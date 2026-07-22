from save_tree import save_png, save_json, pathway_to_branched_tree_dict
from utils import (
    ACTIVATED_ACID_PATTERN,
    canonical_smiles, remove_stereo, remove_counterions, load_smiles_csv,
    generate_graphs, get_num_heavy_atoms, get_local_repetitiveness,
    calculate_h_score, count_functional_groups, calculate_side_reactions,
    detect_unprotected_AA
)
import argparse
import time
import os
import json
import heapq
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from mod import *


class AStarNode:
    def __init__(self, unsolved_smiles, g=0.0, h=0.0, parent=None, reaction_record=None):
        # intermediates that are still need to be decomposed/synthesized
        self.unsolved = tuple(sorted(unsolved_smiles))
        self.g = g  # Cost from target to this intermediate
        self.h = h  # Estimated cost to complete decomposition
        self.f = g + h  # Total estimated cost
        self.parent = parent

        # what reaction happened to get here; to draw the tree later
        self.reaction_record = reaction_record or {}

    # This allows heapq to compare nodes based on their f-score
    def __lt__(self, other):
        return self.f < other.f


def reconstruct_path(node):
    """Traces back the parent pointers to return the step-by-step pathway."""
    path = []

    # Trace backwards from the goal to the first child node
    while node.parent is not None:
        path.append({
            "unsolved_pool": [item[0] for item in node.unsolved],  # The total state of the board
            "reaction": node.reaction_record,  # WHAT reacted to get us here
            "g_score": round(node.g, 3),
            "h_score": round(node.h, 3),
            "f_score": round(node.f, 4)
        })
        node = node.parent

    # The root node (Target Molecule) has no parent and no prior reaction
    path.append({
        "unsolved_pool": [item[0] for item in node.unsolved],
        "reaction": None,
        "g_score": round(node.g, 3),
        "h_score": round(node.h, 3),
        "f_score": round(node.f, 4)
    })
    # Reverse it so it goes from Target -> Final Buyables
    return path[::-1]


def a_star_search(target_smiles, rules, side_graphs,
                  buyables_set, side_set,
                  forward_rules, max_iterations=500, h_weight=0.5,
                  stats=None):
    """
    Executes the A* search.
    """

    # Start state: Only the target molecule needs to be solved
    start_h = calculate_h_score(target_smiles, h_weight)
    start_node = AStarNode(unsolved_smiles=((target_smiles, 0,None),), g=0.0, h=start_h)


    open_set = []  # Priority queue
    heapq.heappush(open_set, start_node)

    closed_set = set()  # Keeps track of visited intermediates to avoid infinite loops
    iterations = 0
    reaction_cache = {}  # Dictionary to store MØD results
    forward_reaction_cache = {} # Dictionary to store MØD results for side reactions

    # statistics for the cache usage
    if stats is None:
        stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "forward_hits": 0,
            "forward_misses": 0
        }

    while open_set and iterations < max_iterations:

        # 1. Pop the most promising (f(n) low scored) intermediate
        current_node = heapq.heappop(open_set)
        iterations += 1

        # 2. Check if we hit the goal (the tuple of unsolved molecules is empty)
        if len(current_node.unsolved) == 0:
            print(f"DONE Retrosynthesis pathway found in {iterations} iterations.")
            return True, reconstruct_path(current_node), iterations, stats

        current_smiles_only = tuple(sorted(item[0] for item in current_node.unsolved))
        # Avoid revisiting the exact same overall state
        if current_smiles_only in closed_set:
            continue
        closed_set.add(current_smiles_only)

        # 3. Pick ONE molecule (largest) from the unsolved pool to apply rules to.
        target_tuple = max(current_node.unsolved, key=lambda x: get_num_heavy_atoms(x[0]))
        target_smiles, current_depth, last_rule_name = target_tuple
        last_rule_name = last_rule_name.lower() if last_rule_name else ''

        # --- THE LOCAL SYMMETRY GUARDRAIL ---
        atoms = get_num_heavy_atoms(target_smiles)
        rep_ratio = get_local_repetitiveness(target_smiles)

        # If the molecule is large AND highly repetitive locally, MØD will freeze
        if atoms > 50 and rep_ratio > 2.0:  # You can tune this 2.0 threshold!
            print(f"Blocked Polymer! {atoms} heavy atoms, Repetitiveness: {rep_ratio:.2f}. SMILES: {target_smiles}")
            continue

        # Check if we have already calculated the reactions for this exact SMILES
        if target_smiles in reaction_cache:
            generated_precursors = reaction_cache[target_smiles]
            stats["cache_hits"] += 1
        else:
            stats["cache_misses"] += 1

            # 4. Apply MØD rules ONLY to this molecule
            target_graph = Graph.fromSMILES(target_smiles)
            dg = DG(graphDatabase=[target_graph, *side_graphs])
            strat = addUniverse(*side_graphs) >> addSubset(target_graph) >> rules

            with dg.build() as builder:
                builder.execute(strat)

            generated_precursors = []

            # 5. Evaluate generated reactions
            for i, e in enumerate(dg.edges): # hyperedges: ordered pairs of multisets of vertices, the sources and the targets
                rule_name = list(e.rules)[0].name.lower() if e.rules else "UnknownRule"

                precursors = []
                for v in e.targets:
                    cs = canonical_smiles(v.graph.smiles)
                    if cs: precursors.append(cs)
                generated_precursors.append((precursors, rule_name))

            # Save the results to the cache so we NEVER have to run MØD on this molecule again
            reaction_cache[target_smiles] = generated_precursors

        for precursors, rule_name in generated_precursors:

            rule_name = rule_name.lower()
            # Separate products into buyables and remaining intermediates
            buyables_produced = [p for p in precursors if p in buyables_set or p in side_set]
            new_intermediates = [p for p in precursors if p not in buyables_set and p not in side_set]

            # 5.1 Calculate g(n) Step Cost: Inverse of cleaved buyable size
            depth_penalty = current_depth * 0.05
            step_cost = None

            requires_activation = False
            # with the following conditions we ensure that acid part of the condensation reaction
            # is activated right before the condensation reaction (one-pot process)
            if last_rule_name == "condensation_rule_inv":
                mol = Chem.MolFromSmiles(target_smiles)
                if mol and mol.HasSubstructMatch(ACTIVATED_ACID_PATTERN):
                    requires_activation = True
            if requires_activation:
                if rule_name != "cooh_activation_inv":
                    continue  # Veto all other branches
                elif rule_name == "cooh_activation_inv":
                    precursor_key = tuple(sorted(precursors))
                    if precursor_key not in forward_reaction_cache:
                        forward_reaction_cache[precursor_key] = calculate_side_reactions(
                            precursors=precursors,
                            rule_name=rule_name,
                            forward_rules=forward_rules,
                            forward_reaction_cache=forward_reaction_cache
                        )
                        stats["forward_misses"] += 1
                    else:
                        stats["forward_hits"] += 1
                    num_forward_reactions = forward_reaction_cache[precursor_key]
                    competing_side_reactions = max(0, num_forward_reactions - 1)
                    step_cost = 0.3 + competing_side_reactions * 2
                    depth_penalty = 0

            elif "protection" in rule_name:
                # if we repeat the same reaction, it happens in one pot, we don't need additional efforts => cost=0
                if (rule_name == last_rule_name) or ('deprotection_base' in rule_name and 'deprotection_base' in last_rule_name):
                    step_cost = 0.0
                    depth_penalty = 0
                else:
                    # following protection/deprotection reactions for the same group are forbidden (have no sense)
                    curr_is_de = "deprotection" in rule_name
                    last_is_de = "deprotection" in last_rule_name
                    curr_prefix = rule_name.replace("deprotection", "protection").split("protection")[0]
                    last_prefix = last_rule_name.replace("deprotection", "protection").split("protection")[0]

                    if (curr_prefix == last_prefix) and (curr_is_de != last_is_de):
                        continue

                    precursor_key = tuple(sorted(precursors))
                    if precursor_key not in forward_reaction_cache:
                        forward_reaction_cache[precursor_key] = calculate_side_reactions(
                            precursors=precursors,
                            rule_name=rule_name,
                            forward_rules=forward_rules,
                            forward_reaction_cache=forward_reaction_cache
                        )
                    num_forward_reactions = forward_reaction_cache[precursor_key]
                    competing_side_reactions = max(0, num_forward_reactions - 1)
                    step_cost = 0.3 + competing_side_reactions * 2 + depth_penalty

            else:
                precursor_key = tuple(sorted(precursors))
                if precursor_key not in forward_reaction_cache:
                    forward_reaction_cache[precursor_key] = calculate_side_reactions(
                        precursors=precursors,
                        rule_name=rule_name,
                        forward_rules=forward_rules,
                        forward_reaction_cache=forward_reaction_cache
                    )
                num_forward_reactions = forward_reaction_cache[precursor_key]

                competing_side_reactions = max(0, num_forward_reactions - 1)
                chemoselectivity_penalty = competing_side_reactions * 2
                base_step_cost = 1
                step_cost = base_step_cost + chemoselectivity_penalty + depth_penalty

            new_depth = current_depth + step_cost

            # if in parallel branch of the same pathway g score is already higher,
            # we take this value for the current branch as well, as a cost of the synthesis overall;
            # depth of the current branch is however saved separately
            g_new = max(current_node.g, new_depth)

            # 5.2 Build the NEW state of unsolved molecules
            # A. Take all currently unsolved molecules
            next_unsolved_list = list(current_node.unsolved)
            # B. Remove the one we just reacted
            next_unsolved_list.remove(target_tuple)
            # C. Add any NEW non-buyable fragments created by this reaction
            for int_smiles in new_intermediates:
                next_unsolved_list.append((int_smiles, new_depth, rule_name))

            # 5.3 Calculate the new heuristic: Sum of SA scores for all remaining unsolved molecules
            if next_unsolved_list:
                # we take max of the all possible "distances to the goal" as the limiting state for the overall synthesis
                h_new = max(calculate_h_score(s[0],h_weight) for s in next_unsolved_list)
            else:
                h_new = 0.0

            # 5.4 Keep a record of what just happened for the visualization tree
            reaction_record = {
                "parent_mol": target_smiles,
                "buyables_cleaved": buyables_produced,
                "new_intermediates": new_intermediates,
                "rule_name": rule_name,
            }

            new_node = AStarNode(
                unsolved_smiles=next_unsolved_list,
                g=g_new,
                h=h_new,
                parent=current_node,
                reaction_record=reaction_record
            )
            heapq.heappush(open_set, new_node)

    print(f"FAILED Search terminated after {iterations} iterations. No pathway found.")

    return False, reconstruct_path(current_node), iterations, stats


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Retrosynthesis CLI using A* Search")
    parser.add_argument("--buyables", required=True, help="CSV with buyable SMILES")
    parser.add_argument("--side-products", required=True, help="CSV with side product SMILES")
    parser.add_argument("--rules", required=True, help="Folder with .gml rules")
    parser.add_argument("--target", required=True, help="Target SMILES")
    parser.add_argument("--max-iters", type=int, default=60, help="Max A* iterations to prevent infinite loops")
    parser.add_argument("--h-weight", type=float, default=0.5, help="h(n) weight")
    args = parser.parse_args()
    start_time = time.perf_counter()

    # Load SMILES (should be canonicalized in advance)
    buyables_set = load_smiles_csv(args.buyables)

    side_products_set = load_smiles_csv(args.side_products)

    side_graphs = generate_graphs(args.side_products, addHs=False)

    # Load rules
    rules = [
        Rule.fromGMLFile(os.path.join(args.rules, f), name=f[:-4])
        for f in os.listdir(args.rules) if f.endswith(".gml")
    ]

    forward_rules = [
        Rule.fromGMLFile(os.path.join("forward_rules", f), name=f[:-4])
        for f in os.listdir("forward_rules") if f.endswith(".gml")
    ]

    target_smiles = canonical_smiles(args.target)
    if target_smiles is None:
        raise ValueError("Invalid target SMILES")

    # Run A* Search
    pathway_found, optimal_pathway, iterations, stats = a_star_search(
        target_smiles=target_smiles,
        rules=rules,
        side_graphs=side_graphs,
        buyables_set=buyables_set,
        side_set=side_products_set,
        forward_rules=forward_rules,
        max_iterations=args.max_iters,
        h_weight=args.h_weight,
        stats=None
    )

    # Output the result
    if pathway_found:
        output_file = "results/optimal_pathway.json"
        with open(output_file, "w") as f:
            json.dump(optimal_pathway, f, indent=4)
        print(f"Saved pathway to {output_file}")

        # Convert the flat path into the dictionary structure
        root_dict = pathway_to_branched_tree_dict(optimal_pathway, buyables_set, side_products_set)

        # Generate the Graphviz dot file + PNGs

        save_png(root_dict,output_filename="results/pathway.png")

    else:
        print("Failed to find a complete retrosynthetic pathway.")

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"\n⏱️ Total execution time:{elapsed_time:.3f} s")


if __name__ == "__main__":
    main()
