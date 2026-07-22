"""
Experiment: Vulnerability Severity Distribution
Visualizes the VulnerableMCP dataset by CVSS severity and attack vector.
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

SEVERITY_COLORS = {
    "CRITICAL": "#CC2222",
    "HIGH": "#E07020",
    "MEDIUM": "#E0C010",
    "LOW": "#40A040",
}


def load_dataset() -> pd.DataFrame:
    csv_path = ROOT / "data" / "vulnerablemcp_dataset.csv"
    return pd.read_csv(csv_path)


def plot_severity_by_vector(df: pd.DataFrame, output_path: Path) -> None:
    vectors = ["TI", "MP", "PM", "TC", "SC", "AA"]
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    counts = {}
    for vec in vectors:
        subset = df[df["attack_vector"] == vec]
        counts[vec] = {sev: (subset["cvss_severity"] == sev).sum() for sev in severities}

    x = np.arange(len(vectors))
    width = 0.18
    offsets = np.array([-1.5, -0.5, 0.5, 1.5]) * width

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, sev in enumerate(severities):
        vals = [counts[v][sev] for v in vectors]
        ax.bar(x + offsets[i], vals, width, label=sev, color=SEVERITY_COLORS[sev],
               edgecolor="white", linewidth=0.8, zorder=3)
        for j, val in enumerate(vals):
            if val > 0:
                ax.text(x[j] + offsets[i], val + 0.05, str(val),
                        ha="center", fontsize=7, fontweight="bold")

    ax.set_xlabel("Attack Vector (MCP-TaxSec)", fontsize=10)
    ax.set_ylabel("Vulnerability Count", fontsize=10)
    ax.set_title("VulnerableMCP Dataset: Severity Distribution by Attack Vector\n"
                 "(n=50 vulnerabilities, 24 CVEs + 26 zero-days)", fontsize=10, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(vectors)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.15)

    patches = [mpatches.Patch(color=SEVERITY_COLORS[s], label=s) for s in severities]
    ax.legend(handles=patches, fontsize=9, loc="upper right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_cvss_histogram(df: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))

    bins = np.arange(0, 11, 0.5)
    ax.hist(df["cvss_score"], bins=bins, color="#3478BE", edgecolor="#1E5AA0",
            linewidth=0.8, zorder=3, alpha=0.85)

    for sev, (lo, hi, col) in {"LOW": (0, 4, "#40A040"), "MEDIUM": (4, 7, "#E0C010"),
                                "HIGH": (7, 9, "#E07020"), "CRITICAL": (9, 10.1, "#CC2222")}.items():
        ax.axvspan(lo, hi, alpha=0.07, color=col, zorder=0)
        ax.text((lo + hi) / 2, ax.get_ylim()[1] * 0.85 if ax.get_ylim()[1] else 5,
                sev, ha="center", fontsize=8, color=col, fontweight="bold")

    ax.axvline(df["cvss_score"].mean(), color="red", linewidth=1.3, linestyle="--",
               label=f"μ={df['cvss_score'].mean():.2f}")
    ax.axvline(df["cvss_score"].median(), color="navy", linewidth=1.3, linestyle=":",
               label=f"median={df['cvss_score'].median():.2f}")

    ax.set_xlabel("CVSS v3.1 Score", fontsize=10)
    ax.set_ylabel("Count", fontsize=10)
    ax.set_title("CVSS Score Distribution — VulnerableMCP Dataset (n=50)", fontsize=10, fontweight="bold")
    ax.legend(fontsize=9)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    df = load_dataset()
    print(f"Dataset loaded: {len(df)} rows")
    print(df["cvss_severity"].value_counts().to_string())

    out_dir = ROOT / "figures"
    out_dir.mkdir(exist_ok=True)
    plot_severity_by_vector(df, out_dir / "fig_severity_by_vector.pdf")
    plot_severity_by_vector(df, out_dir / "fig_severity_by_vector.png")
    plot_cvss_histogram(df, out_dir / "fig_cvss_histogram.pdf")
    plot_cvss_histogram(df, out_dir / "fig_cvss_histogram.png")
