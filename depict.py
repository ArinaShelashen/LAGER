"""
depict.py – draws molecules as SVG pictures with RDKit (used by the rule guide).

Atoms with an atom-map number (e.g. [C:3]) are highlighted, and the number is
written next to the atom. In the guide these numbers are the atom ids of the
reaction rule, so a picture, the rule's GML and the rule viewer all use the same
numbers. Atoms listed in `centre` (the reaction centre) get a stronger colour
than the other mapped atoms (the context).
"""

from functools import lru_cache

from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D

CENTRE_COLOUR = (1.0, 0.76, 0.45)       # orange: bonds change here
CONTEXT_COLOUR = (0.72, 0.84, 1.0)      # light blue: needed, but unchanged
MAX_SMILES = 400


@lru_cache(maxsize=512)
def molecule_svg(smiles: str, centre: tuple[int, ...] = (), width: int = 280, height: int = 200) -> str | None:
    if not smiles or len(smiles) > MAX_SMILES:
        return None
    params = Chem.SmilesParserParams()
    params.removeHs = False             # keep hydrogens that are part of the rule, e.g. [H:4]
    mol = Chem.MolFromSmiles(smiles, params)
    if mol is None:
        return None

    atom_colours = {}
    for atom in mol.GetAtoms():
        number = atom.GetAtomMapNum()
        if number:
            atom.SetProp("atomNote", str(number))
            atom.SetAtomMapNum(0)
            atom_colours[atom.GetIdx()] = CENTRE_COLOUR if number in centre else CONTEXT_COLOUR
    bond_colours = {}
    for bond in mol.GetBonds():
        a, b = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        if a in atom_colours and b in atom_colours:
            both_centre = atom_colours[a] is CENTRE_COLOUR and atom_colours[b] is CENTRE_COLOUR
            bond_colours[bond.GetIdx()] = CENTRE_COLOUR if both_centre else CONTEXT_COLOUR

    try:
        rdDepictor.SetPreferCoordGen(True)
    except AttributeError:
        pass
    rdDepictor.Compute2DCoords(mol)

    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    options = drawer.drawOptions()
    options.clearBackground = False
    options.annotationFontScale = 0.75
    options.padding = 0.12
    prepared = rdMolDraw2D.PrepareMolForDrawing(mol, kekulize=True)
    drawer.DrawMolecule(prepared,
                        highlightAtoms=list(atom_colours), highlightAtomColors=atom_colours,
                        highlightBonds=list(bond_colours), highlightBondColors=bond_colours)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()
