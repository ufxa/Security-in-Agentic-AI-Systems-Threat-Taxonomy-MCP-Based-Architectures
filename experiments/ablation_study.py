"""
Experiment: Ablation Study (Table III in the paper)
Evaluates AEGIS-MCP detection rate and FPR as layers are progressively added.
"""

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Paper-reported ablation results (Table III)
ABLATION_CONFIGS = [
    {"config": "L1 only",              "detection": 71.2, "fpr": 12.4, "latency": 1.8},
    {"config": "L1 + L3",             "detection": 82.6, "fpr": 9.1,  "latency": 4.2},
    {"config": "L1 + L2 + L3",        "detection": 88.4, "fpr": 6.8,  "latency": 5.1},
    {"config": "L1–L3 + L4",          "detection": 91.7, "fpr": 5.3,  "latency": 5.8},
    {"config": "Full AEGIS-MCP (L1–L5)", "detection": 94.7, "fpr": 2.8, "latency": 6.4},
]


def print_table(configs: list) -> None:
    header = f"{'Configuration':<28} {'Detection %':>12} {'FPR %':>8} {'Latency ms':>12}"
    print(header)
    print("-" * len(header))
    for c in configs:
        print(f"{c['config']:<28} {c['detection']:>12.1f} {c['fpr']:>8.1f} {c['latency']:>12.1f}")


def plot_ablation(configs: list, output_path: Path) -> None:
    labels = [c["config"] for c in configs]
    detection = [c["detection"] for c in configs]
    fpr = [c["fpr"] for c in configs]
    latency = [c["latency"] for c in configs]
    x = np.arange(len(labels))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

    # Detection rate
    bars = ax1.bar(x, detection, color="#3478BE", edgecolor="#1E5AA0", linewidth=1.2,
                   width=0.55, zorder=3, label="Detection Rate (%)")
    ax1_twin = ax1.twinx()
    ax1_twin.plot(x, fpr, "D--", color="#CC2222", linewidth=1.8, markersize=6,
                  label="False Positive Rate (%)", zorder=4)
    for i, (d, f) in enumerate(zip(detection, fpr)):
        ax1.text(i, d + 0.5, f"{d:.1f}%", ha="center", fontsize=8, fontweight="bold", color="#1E5AA0")
        ax1_twin.text(i, f + 0.3, f"{f:.1f}%", ha="center", fontsize=8, color="#CC2222")

    ax1.set_ylabel("Detection Rate (%)", fontsize=10, color="#3478BE")
    ax1_twin.set_ylabel("False Positive Rate (%)", fontsize=10, color="#CC2222")
    ax1.set_ylim(65, 100)
    ax1_twin.set_ylim(0, 16)
    ax1.yaxis.grid(True, linestyle="--", alpha=0.35, zorder=0)
    ax1.set_axisbelow(True)
    ax1.set_title("Ablation Study: AEGIS-MCP Layer Contribution", fontsize=11, fontweight="bold")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc="lower right")

    # Latency
    ax2.bar(x, latency, color="#78B4E8", edgecolor="#3478BE", linewidth=1.2,
            width=0.55, zorder=3)
    for i, v in enumerate(latency):
        ax2.text(i, v + 0.05, f"{v:.1f}ms", ha="center", fontsize=8, fontweight="bold")

    ax2.set_ylabel("End-to-End Latency (ms)", fontsize=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=8.5, rotation=10, ha="right")
    ax2.set_ylim(0, 8.5)
    ax2.yaxis.grid(True, linestyle="--", alpha=0.35, zorder=0)
    ax2.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    print("=== AEGIS-MCP Ablation Study (Table III) ===\n")
    print_table(ABLATION_CONFIGS)
    print(f"\nFull system improvement over L1 only:")
    full = ABLATION_CONFIGS[-1]
    l1 = ABLATION_CONFIGS[0]
    print(f"  Detection: +{full['detection']-l1['detection']:.1f}pp")
    print(f"  FPR reduction: {l1['fpr']-full['fpr']:.1f}pp")
    print(f"  Latency overhead: +{full['latency']-l1['latency']:.1f}ms")

    out_dir = ROOT / "figures"
    out_dir.mkdir(exist_ok=True)
    plot_ablation(ABLATION_CONFIGS, out_dir / "fig_ablation_study.pdf")
    plot_ablation(ABLATION_CONFIGS, out_dir / "fig_ablation_study.png")
