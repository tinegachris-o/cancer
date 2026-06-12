from pdbfixer import PDBFixer
from openmm.app import PDBFile

fixer = PDBFixer(filename='4QO8.pdb')
fixer.findMissingResidues()
fixer.findMissingAtoms()
fixer.addMissingAtoms()
fixer.addMissingHydrogens(7.4)  # physiological pH
PDBFile.writeFile(fixer.topology, fixer.positions, open('4QO8_fixed.pdb', 'w'))
print('Fixed!')
