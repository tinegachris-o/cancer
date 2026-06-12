from collections import Counter

pdb_file = "1J3I.pdb"
heteroatoms = []
hetatm_residues = {}

with open(pdb_file, 'r') as f:
    for line in f:
        record = line[:6].strip()
        if record == "HETATM":
            atom_name  = line[12:16].strip()
            res_name   = line[17:20].strip()
            chain      = line[21].strip()
            res_seq    = line[22:26].strip()
            x          = line[30:38].strip()
            y          = line[38:46].strip()
            z          = line[46:54].strip()
            element    = line[76:78].strip() if len(line) > 76 else atom_name[0]
            heteroatoms.append({
                'atom':    atom_name,
                'residue': res_name,
                'chain':   chain,
                'res_seq': res_seq,
                'element': element,
                'coords':  (x, y, z)
            })
            key = f"{res_name}_{chain}_{res_seq}"
            if key not in hetatm_residues:
                hetatm_residues[key] = []
            hetatm_residues[key].append(atom_name)

print(f"PDB File: {pdb_file}")
print(f"Total HETATM atoms: {len(heteroatoms)}")
print(f"Unique HETATM groups: {len(hetatm_residues)}")
print()
print("=" * 65)
print("HETATM GROUPS (ligands, cofactors, waters, ions):")
print("=" * 65)
for key, atoms in hetatm_residues.items():
    res, chain, seq = key.split("_")
    print(f"  [{res}] Chain {chain} | ResSeq {seq:>4} | Atoms ({len(atoms)}): {', '.join(atoms)}")

print()
print("=" * 65)
print("ELEMENT SUMMARY (all HETATM):")
print("=" * 65)
elem_counts = Counter(h['element'] for h in heteroatoms if h['element'] not in ['C','H'])
for elem, count in sorted(elem_counts.items()):
    print(f"  {elem}: {count}")

print()
print("=" * 65)
print("BACKBONE HETEROATOMS IN PROTEIN RESIDUES (ATOM records):")
print("=" * 65)
backbone_hetero = Counter()
with open(pdb_file, 'r') as f:
    for line in f:
        if line[:4] == "ATOM":
            atom_name = line[12:16].strip()
            element   = line[76:78].strip() if len(line) > 76 else ''
            if atom_name in ['N', 'O', 'OXT'] or (element and element not in ['C','H']):
                backbone_hetero[atom_name] += 1
for atom, count in sorted(backbone_hetero.items()):
    print(f"  {atom}: {count}")
