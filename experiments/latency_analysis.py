"""
Experiment: Latency Analysis (Figure 4b in the paper)
Measures AEGIS-MCP per-layer processing latency under realistic load.
"""

import sys
import time
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from aegis_mcp import AEGISMCP
from aegis_mcp.layer3_trust import (CryptographicEvidence, ReputationEvidence,
                                     BehavioralEvidence, AttestationEvidence)

# Paper reported mean latencies per layer (ms)
PAPER_LATENCIES = {
    "L1 Protocol\nInterception": 1.8,
    "L2 Policy\nEnforcement": 0.9,
    "L3 Trust\nAttestation": 2.4,
    "L4 Forensic\nAudit": 0.7,
    "L5 Alert\nResponse": 0.6,
    "Total\nOverhead": 6.4,
}

SAMPLE_MSG = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"read_file","arguments":{"path":"/home/user/doc.txt"}},"id":1}'


def measure_latencies(n: int = 100, seed: int = 42) -> dict[str, list]:
    """Time each AEGIS-MCP layer individually on n message evaluations."""
    rng = np.random.default_rng(seed)
    aegis = AEGISMCP()

    layer_times: dict[str, list] = {k: [] for k in ["L1", "L2", "L3", "L4", "L5", "Total"]}

    for i in range(n):
        rep = ReputationEvidence(community_score=rng.uniform(0.5, 1.0),
                                 registry_age_days=int(rng.integers(60, 1000)),
                                 verified_publisher=rng.random() > 0.5)
        beh = BehavioralEvidence(prior_violations=int(rng.integers(0, 2)))
        att = AttestationEvidence(proof_of_non_malicious=rng.random() > 0.2)

        t0 = time.perf_counter()

        # Time L1
        t_l1 = time.perf_counter()
        l1 = aegis.layer1.validate(SAMPLE_MSG)
        layer_times["L1"].append((time.perf_counter() - t_l1) * 1000)

        # Time L3
        t_l3 = time.perf_counter()
        ats = aegis.layer3.compute(f"a{i}", CryptographicEvidence(), rep, beh, att)
        layer_times["L3"].append((time.perf_counter() - t_l3) * 1000)

        # Time L2
        t_l2 = time.perf_counter()
        if f"a{i}" not in aegis.layer2._policies:
            aegis.layer2.register_policy(aegis.layer2.get_default_policy(f"a{i}", ats.ats))
        aegis.layer2.evaluate(f"a{i}", "read_file", len(SAMPLE_MSG))
        layer_times["L2"].append((time.perf_counter() - t_l2) * 1000)

        # Time L4
        t_l4 = time.perf_counter()
        aegis.layer4.log("TEST", f"a{i}", "allowed", 0.0)
        layer_times["L4"].append((time.perf_counter() - t_l4) * 1000)

        # Time L5
        t_l5 = time.perf_counter()
        aegis.layer5.process(f"a{i}", "test", 0.2)
        layer_times["L5"].append((time.perf_counter() - t_l5) * 1000)

        layer_times["Total"].append((time.perf_counter() - t0) * 1000)

    return layer_times


def plot_latency(measured: dict, output_path: Path) -> None:
    labels = list(PAPER_LATENCIES.keys())
    paper_vals = list(PAPER_LATENCIES.values())

    map_keys = {"L1 Protocol\nInterception": "L1", "L2 Policy\nEnforcement": "L2",
                "L3 Trust\nAttestation": "L3", "L4 Forensic\nAudit": "L4",
                "L5 Alert\nResponse": "L5", "Total\nOverhead": "Total"}
    measured_means = [np.mean(measured[map_keys[l]]) for l in labels]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    bars_p = ax.bar(x - width / 2, paper_vals, width, label="Paper (reported)", color="#3478BE",
                    edgecolor="#1E5AA0", linewidth=1.2, zorder=3)
    bars_m = ax.bar(x + width / 2, measured_means, width, label="Reproduced (measured)",
                    color="#78B4E8", edgecolor="#3478BE", linewidth=1.2, zorder=3)

    for b, v in zip(bars_p, paper_vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f"{v:.1f}", ha="center",
                fontsize=7.5, fontweight="bold")
    for b, v in zip(bars_m, measured_means):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f"{v:.1f}", ha="center",
                fontsize=7.5)

    ax.set_xlabel("AEGIS-MCP Layer", fontsize=10)
    ax.set_ylabel("Latency (ms)", fontsize=10)
    ax.set_title("Processing Latency per Layer", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.legend(fontsize=9)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    print("Measuring latency across 100 evaluations...")
    measured = measure_latencies(n=100)
    print("\nLatency Summary (ms):")
    for layer, times in measured.items():
        arr = np.array(times)
        paper_key = {v: k for k, v in {"L1 Protocol\nInterception": "L1",
                                        "L2 Policy\nEnforcement": "L2",
                                        "L3 Trust\nAttestation": "L3",
                                        "L4 Forensic\nAudit": "L4",
                                        "L5 Alert\nResponse": "L5",
                                        "Total\nOverhead": "Total"}.items()}[layer]
        print(f"  {layer}: mean={arr.mean():.2f}ms  paper={PAPER_LATENCIES[paper_key]:.1f}ms  "
              f"p95={np.percentile(arr, 95):.2f}ms")

    out_dir = ROOT / "figures"
    out_dir.mkdir(exist_ok=True)
    plot_latency(measured, out_dir / "fig_latency_analysis.pdf")
    plot_latency(measured, out_dir / "fig_latency_analysis.png")
