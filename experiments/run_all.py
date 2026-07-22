"""
run_all.py — Master script to reproduce all paper figures and tables.

Usage:
    python experiments/run_all.py

All figures are saved to figures/ in both PDF and PNG formats.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXPERIMENTS = [
    "experiments/detection_performance.py",
    "experiments/roc_analysis.py",
    "experiments/ats_distribution.py",
    "experiments/latency_analysis.py",
    "experiments/severity_distribution.py",
    "experiments/propagation_timeline.py",
    "experiments/ablation_study.py",
]


def run(script: str) -> bool:
    print(f"\n{'='*60}")
    print(f"Running: {script}")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, str(ROOT / script)],
        capture_output=False,
        cwd=str(ROOT),
    )
    return result.returncode == 0


def main() -> None:
    out_dir = ROOT / "figures"
    out_dir.mkdir(exist_ok=True)

    failed = []
    for script in EXPERIMENTS:
        if not run(script):
            failed.append(script)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = len(EXPERIMENTS)
    passed = total - len(failed)
    print(f"  Passed: {passed}/{total}")
    if failed:
        print("  Failed:")
        for f in failed:
            print(f"    - {f}")
    else:
        print("  All experiments completed successfully.")
    print(f"\nFigures saved to: {out_dir}/")


if __name__ == "__main__":
    main()
