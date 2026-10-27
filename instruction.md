## Detailed Instruction for A* Retrosynthesis Engine
This repository contains a computational **retrosynthesis engine** that uses 
- an A* search algorithm
- MØD based graph transformations
- SAscore based heuristics 

to find optimal chemical pathways. It dynamically avoids incompatible functional groups and penalizes unwanted side-products.

⚠️ **Operating System Note**: This tool relies heavily on MØD and Boost C++ libraries, which are natively compiled for Linux (linux-64). 
If you are on **Windows**, you must use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
Use [Step 0](#step-0-install-wsl-on-windows) for the Instructions.


### Table of Contents
- Step 0: [Install WSL on Windows](#step-0-install-wsl-on-windows)
- Step 1: [Install Conda (Miniconda)](#-step-1-install-conda-miniconda)
- Step 2: [Clone the Repository](#-step-2-clone-the-repository)
- Step 3: [Create the Conda Environment](#-step-3-create-the-conda-environment)
- Step 4: [Prepare Your Data](#-step-4-prepare-your-data)
- Step 5: [Run the Retrosynthesis Engine](#-step-5-run-the-retrosynthesis-engine)
- [Outputs](#-outputs)
- [Troubleshooting](#-troubleshooting)

### Step 0: Install WSL on Windows
WSL allows Windows users to run a fully functional Linux operating system natively alongside regular Windows apps 
without needing a bulky virtual machine or a dual-boot setup.
For this project, you should have at least 5 to 7 GB of free space on your C:\ drive. 
- WSL itself takes about 2 GB
- installing Miniconda and the environment will consume another 2 GB
- additionally you might want to upload/store heavy data files

You should NOT install WSL if:
- You don't have Administrator rights: Corporate or university laptops often block WSL installation and disable BIOS virtualization (which WSL requires to run).
- Your C:\ drive is almost full: WSL creates a virtual hard drive that expands automatically but is notoriously annoying to shrink back down.
- You already have access to a Linux server: If you can just SSH into a university computing cluster or use a cloud service, it is much easier to run the tool there than to force Windows to run Linux locally!

If you meet these criteria here is the instruction for you:
1. Click your Windows Start menu, type `PowerShell`, right-click it, 
and select `Run as administrator`.
2. Paste this command and press Enter to install WSL:
`wsl --install`
3. Restart your computer after the completion of the download and installation.
4. Repeat Step 1 (Open PowerShell with Administrator rights)
5. Paste this command and press Enter:
`wsl.exe --install -d Ubuntu`
6. It will ask you to create a **username** and a **password**. Do it!
7. Close PowerShell. 
8. Run the App WSL (can be found in Start menu with a Penguin icon).
Use the WSL app to proceed with Steps 1-5 to use the Retrosynthesis tool.

### 🛠️ Step 1: Install Conda (Miniconda)
To manage the dependencies, this project uses **Conda**. If you already have Conda installed, you can skip to **Step 2**.

To install Miniconda on Linux (or WSL), open your terminal and run the following commands:
#### 1. Download the installer
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
``` 
*(Optional)* If your terminal throws a "command not found" error when trying to run `wget` or `clone` commands in the next steps, 
run this command to install the missing tools:
```bash
sudo apt update && sudo apt install -y git wget build-essential
```
#### 2. Run the installer (follow the prompts and type 'yes' to initialize)
```bash
bash miniconda.sh
```

#### 3. Restart your terminal, OR run the following command to source your bashrc to apply changes
```bash
source ~/.bashrc
```

### 📥 Step 2: Clone the Repository
Download the project from GitHub to your local machine:
```bash
git clone https://github.com/ArinaShelashen/Retrosynthesis.git
cd Retrosynthesis/RS
```

### 📦 Step 3: Create the Conda Environment

We have pre-configured an `environment.yml` file that perfectly resolves the  conflicts between MØD and RDKit.
Run this command to build the environment (this may take a few minutes):
```bash
conda env create -f environment.yml
```
(Enter `a` every time it asks to accept Terms)

Activate the environment:
```bash
conda activate mod_env
```
(You must run `conda activate mod_env` every time you open a new terminal to use this tool!)

### 🧹 Step 4: Prepare Your Data
To use the tool you need a `CSV` file with the reactants available to you. 
It should have a column called `smiles` with SMILES for each available reactant. 
If you don’t have such a file, feel free to use sample file `data/zinc_with_precursors.csv`.

Before running the main A* search, your input `CSV` file must be canonicalized and stripped of salts/stereochemistry.
Use the provided cleaning utility:
```bash
python data_prep/clean_molecules.py PATH_TO_YOUR_FILE/YOUR_FILENAME.csv -o YOUR_FILENAME_clean.csv
```

>**Example:** Cleaning the sample reactants dataset
> 
>```python data_prep/clean_molecules.py data/zinc_with_precursors.csv -o zinc_with_precursors_clean.csv```

This step might take some time depending on the number of compounds in your file.

### 🚀 Step 5: Run the Retrosynthesis Engine
With your environment activated and data cleaned, you are ready to run the search!
Here is an example command:
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
Command Line Arguments:
- **--buyables**: Path to your cleaned CSV of available starting materials.
- **--side-products**: Path to  cleaned CSV of known side-products like H2O or HCl (feel free to update the list if needed, but don’t forget to ‘clean’ it before (Step4)).
- **--rules**: Directory containing your custom MØD .gml inverted reaction rules.
- **--max-iters**: Maximum number of search nodes to explore before giving up (prevents infinite loops on impossible molecules).
- **--target**: The SMILES string of the molecule you want to synthesize.
- **--h-weight**: The weight factor for the heuristic (SA Score).
- **--num-pathways**: The number of synthesis pathways to be generated.
 
### 📊 Outputs
When a pathway is successfully found, the engine will generate 
- `results/optimal_pathway_N.json` A structured, step-by-step record of the reactions and flask states; human and machine readable.
- `results/pathway_N.png` Visualization of the generated retrosynthesis pathway.
- `results/pathways_combined.png` All the N generated pathways merged together.

For WSL users:
To see the output files:
1. Open your normal Windows **File Explorer**.
2. Look at the left-hand navigation sidebar (where your C: drive, Desktop, and Downloads are). 
Scroll all the way down to the bottom. You should see an icon with a **Penguin labeled Linux**. 
3. Click it, select `Ubuntu`), and navigate to your project folder (usually inside `home/your-wsl-username/Retrosynthesis/RS`).


### ❓ Troubleshooting
- #### Error: `Boost.Python.ArgumentError` or `did not match C++ signature` 

This means the C++ bindings got corrupted because MØD was imported before RDKit. 
Make sure you are using the provided `environment.yml` and haven't altered the import order at the top of the main script!

- #### Error: ModuleNotFoundError
Ensure you have activated the environment by running `conda activate mod_env` first.