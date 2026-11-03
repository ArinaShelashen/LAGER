"""
Quick check of the salt conversion in reactants.py.
Run from the LAGER folder:  python check_salts.py
Every line should end with "OK".
"""
from rdkit import Chem

from reactants import RULE_ELEMENTS, has_foreign_elements, salt_to_ions

print("Elements used by the rules:", " ".join(sorted(RULE_ELEMENTS)))
print()

CASES = [
    # (name, input SMILES, expected result after conversion; None = removed)
    ("KCN (covalent)",        "N#C[K]",              "[C-]#N"),
    ("KCN (ionic)",           "[K+].[C-]#N",         "[C-]#N"),
    ("NaI",                   "[Na]I",               "[I-]"),
    ("KSCN",                  "N#CS[K]",             "N#C[S-]"),
    ("Na2SO3",                "O=S(O[Na])O[Na]",     "O=S([O-])[O-]"),
    ("NaOH",                  "O[Na]",               "[OH-]"),
    ("sodium acetate",        "CC(=O)O[Na]",         "CC(=O)[O-]"),
    ("K2CO3",                 "O=C(O[K])O[K]",       "O=C([O-])[O-]"),
    ("calcium acetate",       "CC(=O)O[Ca]OC(C)=O",  "CC(=O)[O-].CC(=O)[O-]"),
    ("sodium ion only",       "[Na+]",               None),
    ("HCl (no metal)",        "Cl",                  "Cl"),
    ("H2SO4 (no metal)",      "O=S(=O)(O)O",         "O=S(=O)(O)O"),
    ("triethylamine",         "CCN(CC)CC",           "CCN(CC)CC"),
    ("n-BuLi (unchanged)",    "CCCC[Li]",            "CCCC[Li]"),
    ("Grignard (unchanged)",  "C[Mg]Br",             "C[Mg]Br"),
]


def same(a, b):
    if a is None or b is None:
        return a is b
    ma, mb = Chem.MolFromSmiles(a), Chem.MolFromSmiles(b)
    return ma is not None and mb is not None and Chem.MolToSmiles(ma) == Chem.MolToSmiles(mb)


for name, smiles, expected in CASES:
    result = salt_to_ions(smiles)
    status = "OK" if same(result, expected) else f"DIFFERENT (expected {expected})"
    print(f"{name:24s} {smiles:22s} -> {str(result):24s} {status}")

print()
print("Removed as metal compounds (should both be True):",
      has_foreign_elements("CC(C)P(C)C.[Fe]"), has_foreign_elements("Cl[Pd]Cl"))
print("Kept (should both be False):",
      has_foreign_elements("OB(O)c1ccccc1"), has_foreign_elements("C[Mg]Br"))
