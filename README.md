# LAGER
## Localized Graph-grammar-based Engine for Retrosynthesis

This repository contains a computational **retrosynthesis engine** that uses 
- an A* search algorithm
- MØD-based graph transformations [1]
- SAscore based heuristics [2]

This is a brief instruction on installation and usage of the LAGER tool.
If you need a more detailed guidance, please visit [Detailed Instruction for LAGER installation](https://github.com/ArinaShelashen/LAGER/blob/main/instruction.md).
### Table of Contents
- [About LAGER](#about-lager)
- [Requirements](#requirements)
- [Installation](#installation)
- [Test Run](#test-run)
- [Algorithm Description](#algorithm-description)
- [Scripts overview](#overview-of-scripts)
- [Data and Results from the Paper](#data-and-results-from-the-paper)
- [How to Cite](#how-to-cite)
---
### About LAGER
LAGER is an open-source framework for computer-assisted synthesis planning (CASP).

**Original Paper**\
Preprint: [Efficient Customizable Synthesis Planning with Graph Grammars, with an application to Elastase B inhibitor candidates](https://chemrxiv.org/doi/full/10.26434/chemrxiv.15010079/v1) \
(manuscript under review) \
See [How to Cite](#how-to-cite)

**Key Features**\
🔸 **Graph-Grammar Core:** Built on double-pushout (DPO) graph-transformation reaction rules using the MØD engine.\
🔸 **Heuristic Exploration:** Dynamically constructs and traverses synthesis pathway trees utilizing the A* algorithm.\
🔸 **Deterministic Logic:** Relies on chemically based scoring and explicit expert rules rather than ML/AI models, ensuring 100% explainable pathways free from hallucinations.

**Strengths**\
🔹 **User-Controlled Action Space:** The exact set of allowed reactions and starting materials is fully customizable, eliminating exotic, hazardous, or prohibitively expensive synthesis steps.\
🔹 **High Reliability:** Hand-coded reaction rules ensure rigorous chemical validity within the defined scope.

**Limitations**\
🔻 **Reaction Scope:** Limited to the size of the curated expert reaction rule set.\
🔻 **Context-Insensitivity:** Current reaction rules do not fully evaluate structural environments outside the immediate reaction center.\
🔻 **Synthesis Constraints:** Does not explicitly predict or optimize reaction conditions (e.g., catalysts, solvents, temperatures).

---
### Requirements
* **Python 3.10**
* **RDKit:** For cheminformatics, canonicalization, and SAscore calculations.
* **MØD:** The C++ graph-rewriting engine executing the `.gml` rules.
* **Graphviz:** Required for rendering the final pathway `.dot` files into `.png` images.
<br>See `environment.yml`

**Input Files Required:**
* A `.csv` of available reactants (must contain valid, canonicalized SMILES; column `smiles`).
<br>**Example file:** `lab_reactants_clean.csv`
* A `.csv` of expected side products (e.g., $H_2O$, $NH_4Cl$, $NaCl$ as SMILES; column `smiles`).
<br>**Example file:** `side_products_clean.csv`
* A folder containing valid MØD `.gml` graph grammar rules (for inverse reactions).
<br>**Example folder:** `inv_rules`
* A folder with the corresponding forward rules, used to detect competing side reactions.
<br>**Example folder:** `forward_rules`
---
### Installation

⚠️ **Operating System Note**: This tool relies heavily on MØD and Boost C++ libraries, which are natively compiled for Linux (linux-64). 
If you are on **Windows**, you must use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
Use [Detailed Instruction](https://github.com/ArinaShelashen/LAGER/blob/main/instruction.md) for more information.

We prepared a Conda environment for your convenience. 
If you need to install Conda first, you can use [Detailed Instruction](https://github.com/ArinaShelashen/LAGER/blob/main/instruction.md).

To install LAGER:
1. **Clone the Repository**

Download the project from GitHub to your local machine:
```bash
git clone https://github.com/ArinaShelashen/LAGER.git
cd LAGER
```
2. **Create and activate the Conda Environment**
```bash
conda env create -f environment.yml
conda activate mod_env
```
---
### Test Run
1. **Prepare Your Data**

You need a `CSV` file with the reactants available to you. 
It should have a column called `smiles` with SMILES for each available reactant. 
Sample file: `data/zinc_with_precursors.csv`.

Before running the main A* search, your input `CSV` file must be canonicalized and stripped of salts/stereochemistry.
Use the provided cleaning utility:
```bash
python data_prep/clean_molecules.py PATH_TO_YOUR_FILE/YOUR_FILENAME.csv -o YOUR_FILENAME_clean.csv
```

>**Example:** Cleaning the sample reactants dataset
> 
>```python data_prep/clean_molecules.py data/zinc_with_precursors.csv -o zinc_with_precursors_clean.csv```

This step might take some time depending on the number of compounds in your file.

2. **Run the Retrosynthesis Engine**

Example command:
```bash
python rs_a_star_branched.py \
  --buyables zinc_with_precursors_clean.csv \
  --side-products side_products_clean.csv \
  --rules inv_rules/ \
  --max-iters 50000 \
  --target "Clc1c(Cl)cc(NC(=O)CC(=O)NO)cc1" \
  --h-weight 0.1 \
  --num-pathways 3
```

3. **Check the output**

When a pathway is successfully found, the engine will generate 
- `results/optimal_pathway_N.json` A structured, step-by-step record of the reactions and flask states; human and machine readable.
- `results/pathway_N.png` Visualization of the generated retrosynthesis pathways.
- `results/pathways_combined.png` All the N generated pathways merged together.
(N = number of generated pathways `--num-pathways`)
---
## Algorithm Description
### The A* Heuristics 
### $f(n) = g(n) + w_{h} \cdot h(n)$

To efficiently navigate the massive chemical space, we use A* Search guided by the following cost functions:

### Cost Function: $g(n)$ (Step Cost)
$g(n)$ represents the "chemical cost" incurred so far per step.

$$\text{Cost}_{\text{step}} = \text{Cost}_{\text{base}} + \text{Penalty}_{\text{chemo}} + \text{Penalty}_{\text{depth}}$$ 

* $\text{Cost}_{\text{base}}$: a baseline amount for a step cost ($1.0$ for usual reactions, $0.3$ for "helping" protection/deprotection/activation reactions).
* $\text{Penalty}_{\text{chemo}}$: Chemoselectivity Penalty; 2 * No. of side reactions (evaluated with MØD for produced precursors).
* $\text{Penalty}_{\text{depth}}$: Dynamic Depth Penalty to give an advantage
to branched pathways with a parallel synthesis of fragments instead of a linear pathway.

### Heuristic Function: $h(n)$ (Estimated Distance to Goal)
$h(n)$ represents how far the intermediate is from being a "buyable" starting material.
We map the distance to the goal using the **Synthetic Accessibility (SA) Score**, 
operating under the assumption that a low structural complexity score serves as a reliable proxy for commercial availability.

---
## Overview of Scripts
### A* Search (`rs_a_star_branched.py`)
This script allows for **convergent synthesis**.
* **Algorithm:** State-based A* Search.
* **Behavior:** Instead of tracking a single molecule, it tracks a "pool" of unsolved intermediates. If a reaction cleaves a molecule into two complex, non-buyable fragments, the algorithm will systematically synthesize *both* of them independently.
* **Output:** A linear or, if possible, branched tree visualizing the independent assembly of the molecule's core components `results\pathway_N.png`, `results\optimal_pathway_N.json`,and `results\pathways_combined.png`.
* **Usage:**
  ```bash
  python rs_a_star_branched.py --buyables lab_reactants_clean.csv --side-products side_products_clean.csv --rules inv_rules --target "SMILES" --max-iters 250 --h-weight 0.1 --num-pathways 3
  ```
  
### Batch A* Search (`rs_a_star_batch.py`)
Runs the A* search for every molecule in a `CSV` file and collects search statistics. This script was used for the benchmark in the paper.
* **Input:** A `CSV` with a column `smiles` containing the target molecules.
* **Output:** A copy of the input `CSV` with added columns per $w_h$ value (pathway found, number of pathways, iterations, time, f-scores, cache hit rates). With `--visualize`, the JSON and PNG of every pathway are saved to `results/LasBinhibitors_results/pathway_JSONs/<w_h>/` and `.../pathway_PNGs/<w_h>/`.
* **Usage:**
  ```bash
  python rs_a_star_batch.py --buyables lab_reactants_clean.csv --side-products side_products_clean.csv --rules inv_rules --forward-rules forward_rules --input-csv targets.csv --output-csv astar_batch_results.csv --max-iters 500 --h-weight 0.5 --num-pathways 3 --visualize
  ```
### Exhaustive Tree Search (`rs.py`)
This script performs a depth-limited exhaustive search, generating **all possible valid retrosynthetic pathways** up to a certain depth.
* **Algorithm:** Exhaustive expansion (Breadth/Depth).
* **Behavior:** Applies rules to all generated intermediates until the max depth is reached. 
* **Output:** A complete tree showing every possible route, color marking each node with its status (Buyable, Side-Product, or Unavailable) `pathway.png`.
* **Best for:** Small molecules or highly constrained rule sets where exploring the entire chemical space is computationally feasible; rule testing.
* **Usage:**
  ```bash
  python rs.py --buyables lab_reactants_clean.csv --side-products side_products_clean.csv --rules inv_rules --target "SMILES" --depth 3
  ```

### Data preparation (`data_prep/clean_molecules.py`)
It is recommended to preprocess all the SMILES before using them in the Retrosynthesis tool.
The `smiles` column of the `CSV` file can be canonicalized and stripped of salts/stereochemistry using `clean_molecules.py`.
* **Output:** A `CSV` file with a column `smiles` containing preprocessed SMILES.
* **Usage:**
```bash
python data_prep/clean_molecules.py PATH_TO_YOUR_FILE/YOUR_FILENAME.csv -o YOUR_FILENAME_clean.csv
```
---
## Data and Results from the Paper
The folder `LasBinhibitors_results` contains the LasB inhibitor benchmark reported in the paper:
* `LasB_inhibitors_results.csv` Target molecules, literature references and search statistics for each $w_h$ value.
* `pathway_JSONs/` and `pathway_PNGs/` Pathways found for each $w_h$ value (subfolders `00`, `01`, `05`, `10` for $w_h$ = 0.0, 0.1, 0.5, 1.0), plus `literature_reported_pathways`.

---
## How to Cite
If you use LAGER in your work, please cite:

> Shelashen, A.; Gatter, T.; O'Donnell, C. R.; Vgenopoulou, A.; Hirsch, A. K. H.; Stadler, P. F. Efficient Customizable Synthesis Planning with Graph Grammars, with an Application to Elastase B Inhibitor Candidates. *ChemRxiv* **2026**. https://doi.org/10.26434/chemrxiv.15010079/v1

```bibtex
@article{shelashen2026lager,
  author  = {Shelashen, Arina and Gatter, Thomas and O'Donnell, Charlotte R. and
             Vgenopoulou, Angeliki and Hirsch, Anna K. H. and Stadler, Peter F.},
  title   = {Efficient Customizable Synthesis Planning with Graph Grammars,
             with an Application to Elastase B Inhibitor Candidates},
  journal = {ChemRxiv},
  year    = {2026},
  doi     = {10.26434/chemrxiv.15010079/v1},
  note    = {Preprint}
}
```
### 📄 References
* **[1]** Andersen, J.L., Flamm, C., Merkle, D., Stadler, P.F. (2016). A Software Package for Chemically Inspired Graph Transformation. In: Echahed, R., Minas, M. (eds) Graph Transformation. ICGT 2016. Lecture Notes in Computer Science(), vol 9761. Springer, Cham. https://doi.org/10.1007/978-3-319-40530-8_5
* **[2]** Ertl P, Schuffenhauer A. Estimation of synthetic accessibility score of drug-like molecules based on molecular complexity and fragment contributions. J Cheminform. 2009 Jun 10;1(1):8. doi: 10.1186/1758-2946-1-8. PMID: 20298526; PMCID: PMC3225829.
