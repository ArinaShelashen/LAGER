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
    parser.add_argument("--visualize", type=bool, default=False, help="Save PNG and JSON for the generated pathway")
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

    os.makedirs("results", exist_ok=True)
    os.makedirs("../LasBinhibitors_results/pathway_JSONs", exist_ok=True)
    os.makedirs("../LasBinhibitors_results/pathway_PNGs", exist_ok=True)
    # 2. Load the input dataset
    df = pd.read_csv(args.input_csv)

    # Lists to store our metrics for the DataFrame
    results_found = []
    iterations_list = []
    execution_times = []
    cache_hit_rates = []
    forw_cache_hit_rates = []

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
            iterations_list.append(0)
            execution_times.append(0.0)
            cache_hit_rates.append(0.0)
            forw_cache_hit_rates.append(0.0)
            continue

        print(f"[{index + 1}/{len(df)}] Processing: {target_smiles}...")

        # Run A* Search
        start_time = time.perf_counter()

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

        elapsed_time = time.perf_counter() - start_time

        # --- CALCULATE CACHE HIT RATE ---
        inv_hits = stats["cache_hits"]
        inv_misses = stats["cache_misses"]
        inv_total_lookups = inv_hits + inv_misses

        if inv_total_lookups > 0:
            inv_hit_rate = (inv_hits / inv_total_lookups) * 100
        else:
            inv_hit_rate = 0.0  # Failsafe if it errors out immediately

        forw_hits = stats["forward_hits"]
        forw_misses = stats["forward_misses"]
        forw_total_lookups = forw_hits + forw_misses

        if forw_total_lookups > 0:
            forw_hit_rate = (forw_hits / forw_total_lookups) * 100
        else:
            forw_hit_rate = 0.0  # Failsafe if it errors out immediately
        # Append metrics
        results_found.append(pathway_found)
        iterations_list.append(iterations)
        execution_times.append(elapsed_time)
        cache_hit_rates.append(inv_hit_rate)
        forw_cache_hit_rates.append(forw_hit_rate)

        status_msg = "✅ SUCCESS" if pathway_found else "❌ FAILED"
        print(f"  -> {status_msg} | Iters: {iterations} | Time: {elapsed_time:.2f}s | Cache Hit Rate: {inv_hit_rate:.1f}%")

        w_str = str(args.h_weight).replace('.', '')
        # Output the result
        if args.visualize:
            if pathway_found:
                output_file = f"../LasBinhibitors_results/pathway_JSONs/weight_{w_str}/{index:04d}_w{w_str}.json"
                with open(output_file, "w") as f:
                    json.dump(optimal_pathway, f, indent=4)

                # Convert the flat path into the dictionary structure
                root_dict = pathway_to_branched_tree_dict(optimal_pathway, buyables_set, side_products_set)

                save_png(root_dict, output_filename=f"../LasBinhibitors_results/pathway_PNGs/weight_{w_str}/{index:04d}_w{w_str}.png")

    # 4. Save results to the DataFrame
    # Using dynamic column names so you can easily append data for different weights later


    df[f'{w_str}_path_found'] = results_found
    df[f'{w_str}_batch_iterations'] = iterations_list
    df[f'{w_str}_batch_time'] = execution_times
    df[f'{w_str}_cache_hit_rate'] = cache_hit_rates
    df[f'{w_str}_forw_cache_hit_rate'] = forw_cache_hit_rates

    df.to_csv(args.output_csv, index=False)
    print(f"\n✅ Batch processing complete! Results saved to '{args.output_csv}'")


if __name__ == "__main__":
    main()