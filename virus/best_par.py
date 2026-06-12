#!/usr/bin/env python3
"""
AutoDock4 DLG Parser
====================
Extracts and summarizes best docking parameters from a .dlg file.

Usage:
    python best_par.py 1.dlg
    python best_par.py 1.dlg --top 10
    python best_par.py 1.dlg --save results.csv
"""

import re
import sys
import argparse
from pathlib import Path


def parse_dlg(dlg_file):
    results = []
    current_run = {}

    with open(dlg_file, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if line.strip().startswith("DOCKED: MODEL"):
            current_run = {}
            try:
                current_run['model'] = int(line.split()[-1])
            except:
                current_run['model'] = None

        if "DOCKED: USER    Run =" in line:
            try:
                current_run['run'] = int(line.split("=")[-1].strip())
            except:
                pass

        if "Estimated Free Energy of Binding" in line and "DOCKED" in line:
            try:
                current_run['binding_energy'] = float(re.search(r'=\s*([-\d.]+)', line).group(1))
            except:
                pass

        if "Estimated Inhibition Constant, Ki" in line and "DOCKED" in line:
            try:
                match = re.search(r'=\s*([\d.]+)\s+(\w+)', line)
                if match:
                    current_run['ki_value'] = float(match.group(1))
                    current_run['ki_unit'] = match.group(2)
            except:
                pass

        if "Final Intermolecular Energy" in line and "DOCKED" in line:
            try:
                current_run['intermolecular_energy'] = float(re.search(r'=\s*([-\d.]+)', line).group(1))
            except:
                pass

        if "vdW + Hbond + desolv Energy" in line and "DOCKED" in line:
            try:
                current_run['vdw_hbond_desolv'] = float(re.search(r'=\s*([-\d.]+)', line).group(1))
            except:
                pass

        if "Electrostatic Energy" in line and "DOCKED" in line:
            try:
                current_run['electrostatic_energy'] = float(re.search(r'=\s*([-\d.]+)', line).group(1))
            except:
                pass

        if "Torsional Free Energy" in line and "DOCKED" in line:
            try:
                current_run['torsional_energy'] = float(re.search(r'=\s*([-\d.]+)', line).group(1))
            except:
                pass

        if "Final Total Internal Energy" in line and "DOCKED" in line:
            try:
                current_run['internal_energy'] = float(re.search(r'=\s*([-\d.]+)', line).group(1))
            except:
                pass

        if line.strip() == "DOCKED: ENDMDL" and current_run:
            results.append(current_run.copy())
            current_run = {}

    return results


def parse_clusters(dlg_file):
    clusters = []
    in_cluster_section = False
    cluster_pattern = re.compile(r'\s*(\d+)\s*\|\s*([-\d.]+)\s*\|\s*(\d+)\s*\|\s*([-\d.]+)\s*\|\s*(\d+)\s*\|')

    with open(dlg_file, 'r') as f:
        for line in f:
            if "CLUSTERING HISTOGRAM" in line:
                in_cluster_section = True
            if in_cluster_section:
                match = cluster_pattern.match(line)
                if match:
                    clusters.append({
                        'rank': int(match.group(1)),
                        'lowest_energy': float(match.group(2)),
                        'best_run': int(match.group(3)),
                        'mean_energy': float(match.group(4)),
                        'num_in_cluster': int(match.group(5)),
                    })
            if "Number of multi-member" in line:
                in_cluster_section = False

    return clusters


def print_summary(results, clusters, top_n=10):
    print("\n" + "="*70)
    print("       AutoDock4 DLG ANALYSIS SUMMARY")
    print("="*70)

    if not results:
        print("No results found.")
        return

    sorted_results = sorted(results, key=lambda x: x.get('binding_energy', 0))

    print(f"\n Total runs parsed : {len(results)}")
    print(f" Showing top       : {min(top_n, len(sorted_results))} poses\n")

    print(f"{'Rank':<5} {'Run':<5} {'Binding E':>12} {'Ki':>16} {'Intermol E':>12} {'Elec E':>10} {'Torsion E':>11}")
    print(f"{'':5} {'':5} {'(kcal/mol)':>12} {'':>16} {'(kcal/mol)':>12} {'(kcal/mol)':>10} {'(kcal/mol)':>11}")
    print("-"*75)

    for rank, r in enumerate(sorted_results[:top_n], 1):
        ki_str = f"{r.get('ki_value','?')} {r.get('ki_unit','')}"
        print(f"{rank:<5} {r.get('run','?'):<5} {r.get('binding_energy',0):>12.2f} {ki_str:>16} {r.get('intermolecular_energy',0):>12.2f} {r.get('electrostatic_energy',0):>10.2f} {r.get('torsional_energy',0):>11.2f}")

    best = sorted_results[0]
    print("\n" + "="*70)
    print("  BEST POSE DETAILS")
    print("="*70)
    print(f"  Run Number          : {best.get('run', 'N/A')}")
    print(f"  Binding Energy      : {best.get('binding_energy', 'N/A')} kcal/mol")
    print(f"  Inhibition Const Ki : {best.get('ki_value', 'N/A')} {best.get('ki_unit', '')}")
    print(f"  Intermolecular E    : {best.get('intermolecular_energy', 'N/A')} kcal/mol")
    print(f"  vdW+Hbond+Desolv    : {best.get('vdw_hbond_desolv', 'N/A')} kcal/mol")
    print(f"  Electrostatic E     : {best.get('electrostatic_energy', 'N/A')} kcal/mol")
    print(f"  Torsional Free E    : {best.get('torsional_energy', 'N/A')} kcal/mol")
    print(f"  Internal Energy     : {best.get('internal_energy', 'N/A')} kcal/mol")

    if clusters:
        print("\n" + "="*70)
        print("  CLUSTER ANALYSIS")
        print("="*70)
        print(f"  {'Rank':<6} {'Lowest E':>10} {'Best Run':>9} {'Mean E':>10} {'Count':>7} {'% Runs':>8}")
        print("  " + "-"*55)
        total_runs = len(results)
        for c in clusters:
            pct = (c['num_in_cluster'] / total_runs) * 100
            print(f"  {c['rank']:<6} {c['lowest_energy']:>10.2f} {c['best_run']:>9} {c['mean_energy']:>10.2f} {c['num_in_cluster']:>7} {pct:>7.1f}%")
        best_cluster = clusters[0]
        pct_best = (best_cluster['num_in_cluster'] / total_runs) * 100
        print(f"\n  Best cluster contains {best_cluster['num_in_cluster']}/{total_runs} runs ({pct_best:.1f}%)")
        if pct_best >= 50:
            print("  RESULT: HIGH convergence — RELIABLE")
        elif pct_best >= 25:
            print("  RESULT: MODERATE convergence — acceptable")
        else:
            print("  RESULT: LOW convergence — consider more GA runs")

    energies = [r.get('binding_energy', 0) for r in results]
    print("\n" + "="*70)
    print("  ENERGY STATISTICS")
    print("="*70)
    print(f"  Best  energy : {min(energies):.2f} kcal/mol")
    print(f"  Worst energy : {max(energies):.2f} kcal/mol")
    print(f"  Range        : {max(energies)-min(energies):.2f} kcal/mol")
    print(f"  Average      : {sum(energies)/len(energies):.2f} kcal/mol")

    best_e = min(energies)
    print("\n" + "="*70)
    print("  BINDING POTENCY")
    print("="*70)
    if best_e <= -12:
        grade = "EXCELLENT — Very strong binder"
    elif best_e <= -10:
        grade = "VERY GOOD — Strong binder"
    elif best_e <= -8:
        grade = "GOOD — Moderate binder"
    elif best_e <= -6:
        grade = "FAIR — Weak binder"
    else:
        grade = "POOR — Very weak binder"
    print(f"  {best_e:.2f} kcal/mol → {grade}")
    print("="*70 + "\n")


def save_csv(results, output_file):
    import csv
    fields = ['run', 'binding_energy', 'ki_value', 'ki_unit',
              'intermolecular_energy', 'vdw_hbond_desolv',
              'electrostatic_energy', 'torsional_energy', 'internal_energy']
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for r in sorted(results, key=lambda x: x.get('binding_energy', 0)):
            writer.writerow(r)
    print(f"  Saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Parse AutoDock4 DLG file')
    parser.add_argument('dlg_file', help='Path to .dlg file')
    parser.add_argument('--top', type=int, default=10, help='Top N poses (default: 10)')
    parser.add_argument('--save', type=str, default=None, help='Save to CSV')
    args = parser.parse_args()

    dlg_path = Path(args.dlg_file)
    if not dlg_path.exists():
        print(f"Error: '{args.dlg_file}' not found.")
        sys.exit(1)

    print(f"\n  Parsing: {dlg_path.name}")
    results = parse_dlg(args.dlg_file)
    clusters = parse_clusters(args.dlg_file)

    if not results:
        print("  No docking results found.")
        sys.exit(1)

    print_summary(results, clusters, top_n=args.top)

    if args.save:
        save_csv(results, args.save)


if __name__ == "__main__":
    main()
