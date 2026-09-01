import argparse
import time
import os
import pandas as pd
import json
from save_tree import pathway_to_branched_tree_dict, save_png

# Import the core A* functions from your main file (assuming it is named astar.py)
# If your file has a different name, change 'astar' below to match it.
from rs_a_star_branched import (
    load_smiles_csv,
    generate_graphs,
    canonical_smiles,
    a_star_search,
    Rule
)


def main():
    parser = argparse.ArgumentParser(description="Batch Retrosynthesis CLI for A* Search")
    parser.add_argument("--buyables", required=True, help="CSV with buyable SMILES")
    parser.add_argument("--side-products", required=True, help="CSV with side product SMILES")
    parser.add_argument("--rules", required=True, help="Folder with .gml rules")
    parser.add_argument("--forward-rules", required=True, help="Folder with forward .gml rules")
    parser.add_argument("--input-csv", required=True, help="CSV containing 'smiles' column to process")
    parser.add_argument("--output-csv", default="astar_batch_results.csv", help="Where to save the results")
    parser.add_argument("--max-iters", type=int, default=500, help="Max A* iterations")
    parser.add_argument("--h-weight", type=float, default=0.5, help="h(n) weight")
    parser.add_argument("--num-pathways", type=int, default=3, help="Number of pathways per molecule")
    parser.add_argument("--visualize", action=argparse.BooleanOptionalAction, default=False, help="Save PNG and JSON for the generated pathway (use --visualize or --no-visualize)")
    args = parser.parse_args()

    # 1. Load the chemistry environment
    print("Loading chemistry environment and compiling graph grammar rules...")
    buyables_set = load_smiles_csv(args.buyables)
    side_products_set = load_smiles_csv(args.side_products)
    side_graphs = generate_graphs(args.side_products, addHs=False)

    rules = [
        Rule.fromGMLFile(os.path.join(args.rules, f), name=f[:-4])
        for f in os.listdir(args.rules) if f.endswith(".gml")
    ]

    forward_rules = [
        Rule.fromGMLFile(os.path.join(args.forward_rules, f), name=f[:-4])
        for f in os.listdir(args.forward_rules) if f.endswith(".gml")
    ]

    weight_tag = f"{args.h_weight:.1f}".replace(".", "")
    base_dir = "results/LasBinhibitors_results"
    json_dir = os.path.join(base_dir, "pathway_JSONs", weight_tag)
    png_dir = os.path.join(base_dir, "pathway_PNGs", weight_tag)

    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)

    # 2. Load the input dataset
    df = pd.read_csv(args.input_csv)

    # Lists to store our metrics for the DataFrame
    results_found = []
    num_pathways_list = []
    total_iterations_list = []
    total_execution_times = []
    total_cache_hit_rates = []
    total_forw_cache_hit_rates = []

    # Per-rank metrics dictionaries
    max_ranks = args.num_pathways
    rank_iters = {r: [] for r in range(1, max_ranks + 1)}
    rank_times = {r: [] for r in range(1, max_ranks + 1)}
    rank_f_scores = {r: [] for r in range(1, max_ranks + 1)}
    rank_inv_hits = {r: [] for r in range(1, max_ranks + 1)}
    rank_forw_hits = {r: [] for r in range(1, max_ranks + 1)}

    print(f"\n--- Starting A* Batch Processing for {len(df)} molecules ---")
    print(f"Parameters: h_weight = {args.h_weight}, max_iterations = {args.max_iters}\n")

    # 3. Process each molecule
    for index, row in df.iterrows():
        raw_smiles = row['smiles']
        target_smiles = canonical_smiles(raw_smiles)

        # Guardrail for invalid SMILES strings
        if target_smiles is None:
            print(f"[{index + 1}/{len(df)}] ⚠️ Invalid SMILES skipped: {raw_smiles}")
            results_found.append(False)
            num_pathways_list.append(0)
            total_iterations_list.append(0)
            total_execution_times.append(0.0)
            total_cache_hit_rates.append(0.0)
            total_forw_cache_hit_rates.append(0.0)
            for r in range(1, max_ranks + 1):
                rank_iters[r].append(None)
                rank_times[r].append(None)
                rank_f_scores[r].append(None)
                rank_inv_hits[r].append(None)
                rank_forw_hits[r].append(None)
            continue

        print(f"[{index + 1}/{len(df)}] Processing: {target_smiles}...")

        # Run A* Search
        pathway_found, found_pathways, total_iters, final_stats, total_time = a_star_search(
            target_smiles=target_smiles,
            rules=rules,
            side_graphs=side_graphs,
            buyables_set=buyables_set,
            side_set=side_products_set,
            forward_rules=forward_rules,
            max_iterations=args.max_iters,
            h_weight=args.h_weight,
            stats=None,
            num_pathways=args.num_pathways
        )

        # --- CALCULATE CACHE HIT RATE ---
        inv_hits = final_stats.get("cache_hits", 0) if final_stats else 0
        inv_total = inv_hits + final_stats.get("cache_misses", 0) if final_stats else 0
        inv_hit_rate = (inv_hits / inv_total * 100) if inv_total > 0 else 0.0

        forw_hits = final_stats.get("forward_hits", 0) if final_stats else 0
        forw_total = forw_hits + final_stats.get("forward_misses", 0) if final_stats else 0
        forw_hit_rate = (forw_hits / forw_total * 100) if forw_total > 0 else 0.0

        # Append search-level metrics
        num_found = len(found_pathways) if pathway_found and found_pathways else 0
        results_found.append(pathway_found)
        num_pathways_list.append(num_found)
        total_iterations_list.append(total_iters)
        total_execution_times.append(total_time)
        total_cache_hit_rates.append(inv_hit_rate)
        total_forw_cache_hit_rates.append(forw_hit_rate)

        # Record per-rank metrics
        for r in range(1, max_ranks + 1):
            if pathway_found and len(found_pathways) >= r:
                info = found_pathways[r - 1]
                snap_stats = info["stats_snapshot"]

                r_inv_hits = snap_stats.get("cache_hits", 0)
                r_inv_total = r_inv_hits + snap_stats.get("cache_misses", 0)
                r_inv_rate = (r_inv_hits / r_inv_total * 100) if r_inv_total > 0 else 0.0

                r_forw_hits = snap_stats.get("forward_hits", 0)
                r_forw_total = r_forw_hits + snap_stats.get("forward_misses", 0)
                r_forw_rate = (r_forw_hits / r_forw_total * 100) if r_forw_total > 0 else 0.0

                rank_iters[r].append(info["iteration_found"])
                rank_times[r].append(info["time_found"])
                rank_f_scores[r].append(info["f_score"])
                rank_inv_hits[r].append(r_inv_rate)
                rank_forw_hits[r].append(r_forw_rate)
            else:
                rank_iters[r].append(None)
                rank_times[r].append(None)
                rank_f_scores[r].append(None)
                rank_inv_hits[r].append(None)
                rank_forw_hits[r].append(None)

        status_msg = f"✅ SUCCESS ({num_found} paths)" if pathway_found else "❌ FAILED"
        print(
            f"  -> {status_msg} | Iters: {total_iters} | Time: {total_time:.2f}s | Cache Hit Rate: {inv_hit_rate:.1f}%")

        # --- OUTPUT & VISUALIZATION FOR ALL TOP PATHWAYS ---
        if args.visualize and pathway_found and found_pathways:
            for rank_idx, path_info in enumerate(found_pathways, start=1):
                t_found = path_info["time_found"]
                pathway = path_info["pathway"]
                iter_found = path_info["iteration_found"]
                f_val = path_info["f_score"]
                snap_stats = path_info["stats_snapshot"]

                file_stem = f"{index:04d}_w{weight_tag}_rank{rank_idx}"

                # Save JSON (you can save just the pathway or the entire metadata record)
                json_output_file = os.path.join(json_dir, f"{file_stem}.json")
                with open(json_output_file, "w") as f:
                    json.dump(path_info, f, indent=4)

                # Save PNG visualization
                root_dict = pathway_to_branched_tree_dict(pathway, buyables_set, side_products_set)
                save_png(root_dict, output_filename=os.path.join(png_dir, f"{file_stem}.png"))

    # -------------------------------------------------------------
    # 4. Save results to the DataFrame
    # -------------------------------------------------------------
    df[f'{weight_tag}_path_found'] = results_found
    df[f'{weight_tag}_num_pathways'] = num_pathways_list
    df[f'{weight_tag}_batch_iterations'] = total_iterations_list
    df[f'{weight_tag}_batch_time'] = total_execution_times
    df[f'{weight_tag}_cache_hit_rate'] = total_cache_hit_rates
    df[f'{weight_tag}_forw_cache_hit_rate'] = total_forw_cache_hit_rates

    for r in range(1, max_ranks + 1):
        df[f'{weight_tag}_p{r}_iters'] = rank_iters[r]
        df[f'{weight_tag}_p{r}_time'] = rank_times[r]
        df[f'{weight_tag}_p{r}_f_score'] = rank_f_scores[r]
        df[f'{weight_tag}_p{r}_cache_hit_rate'] = rank_inv_hits[r]
        df[f'{weight_tag}_p{r}_forw_cache_hit_rate'] = rank_forw_hits[r]

    df.to_csv(args.output_csv, index=False)
    print(f"\n✅ Batch processing complete! Results saved to '{args.output_csv}'")


if __name__ == "__main__":
    main()