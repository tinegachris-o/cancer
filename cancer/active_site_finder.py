#!/usr/bin/env python3
import sys
import argparse
from collections import defaultdict

def parse_hetatm(pdb_file):
    ligands = defaultdict(list)
    with open(pdb_file, "r") as f:
        for line in f:
            if not line.startswith("HETATM"):
                continue
            try:
                atom_name = line[12:16].strip()
                resname   = line[17:20].strip()
                chain     = line[21].strip()
                resseq    = line[22:26].strip()
                x         = float(line[30:38])
                y         = float(line[38:46])
                z         = float(line[46:54])
            except (ValueError, IndexError):
                continue
            if resname in ("HOH", "WAT", "DOD"):
                continue
            key = (resname, chain if chain else "?", resseq)
            ligands[key].append((x, y, z, atom_name))
    return ligands

def compute_centroid(atoms):
    xs = [a[0] for a in atoms]
    ys = [a[1] for a in atoms]
    zs = [a[2] for a in atoms]
    return sum(xs)/len(xs), sum(ys)/len(ys), sum(zs)/len(zs)

def compute_extent(atoms):
    xs = [a[0] for a in atoms]
    ys = [a[1] for a in atoms]
    zs = [a[2] for a in atoms]
    return max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)

def suggest_grid_size(dx, dy, dz, padding=10.0):
    import math
    def round_up(v, base=2):
        return int(math.ceil((v + padding) / base) * base)
    return round_up(dx), round_up(dy), round_up(dz)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdb")
    parser.add_argument("--ligand", "-l", default=None)
    args = parser.parse_args()
    try:
        ligands = parse_hetatm(args.pdb)
    except FileNotFoundError:
        print(f"ERROR: File not found -> {args.pdb}"); sys.exit(1)
    if not ligands:
        print("No HETATM records found (excluding water)."); sys.exit(1)
    print("-" * 55)
    print(f"  PDB: {args.pdb}  |  Ligands found:")
    print("-" * 55)
    key_list = sorted(ligands.keys())
    for i, (resname, chain, resseq) in enumerate(key_list):
        natoms = len(ligands[(resname, chain, resseq)])
        print(f"  [{i+1}]  {resname:<6}  chain={chain}  resseq={resseq:<5}  atoms={natoms}")
    print("-" * 55)
    chosen_key = None
    if args.ligand:
        matches = [k for k in key_list if k[0].upper() == args.ligand.upper()]
        if not matches:
            print(f"Ligand '{args.ligand}' not found."); sys.exit(1)
        chosen_key = matches[0]
    elif len(key_list) == 1:
        chosen_key = key_list[0]
        print(f"  One ligand found — using {chosen_key[0]} automatically.")
    else:
        choice = int(input("  Select ligand number: ").strip())
        chosen_key = key_list[choice - 1]
    resname, chain, resseq = chosen_key
    atoms = ligands[chosen_key]
    cx, cy, cz = compute_centroid(atoms)
    dx, dy, dz = compute_extent(atoms)
    sx, sy, sz = suggest_grid_size(dx, dy, dz)
    print(f"\n  Ligand : {resname}  chain={chain}  resseq={resseq}  ({len(atoms)} atoms)")
    print(f"\n  ACTIVE SITE CENTER:")
    print(f"    center_x = {cx:.3f}")
    print(f"    center_y = {cy:.3f}")
    print(f"    center_z = {cz:.3f}")
    print(f"\n  SUGGESTED GRID SIZE (extent + 10A padding):")
    print(f"    npts_x = {sx}")
    print(f"    npts_y = {sy}")
    print(f"    npts_z = {sz}")
    print(f"\n  FULL prepare_gpf4.py COMMAND:")
    print(f'  ~/Downloads/mgltools/bin/pythonsh \\')
    print(f'    ~/Downloads/mgltools/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_gpf4.py \\')
    print(f'    -r receptor.pdbqt -l ligand_final.pdbqt \\')
    print(f'    -p gridcenter="{cx:.3f},{cy:.3f},{cz:.3f}" \\')
    print(f'    -p npts="{sx},{sy},{sz}" \\')
    print(f'    -o grid.gpf')
    print("-" * 55)
    print(f"  PyMOL verify:  select lig, resn {resname}  |  zoom lig")
    print("-" * 55)

if __name__ == "__main__":
    main()
