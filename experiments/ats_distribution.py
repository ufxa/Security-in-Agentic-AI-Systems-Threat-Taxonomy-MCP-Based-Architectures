"""
Experiment: ATS Distribution (Figure 4 in the paper)
Agent Trust Score distribution across 200 sampled MCP servers.
"""

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from aegis_mcp.layer3_trust import (TrustAttestationEngine, CryptographicEvidence,
                                     ReputationEvidence, BehavioralEvidence, AttestationEvidence)


def sample_mcp_servers(n: int = 200, seed: int = 42) -> list[float]:
    """Sample ATS scores for n MCP servers across enterprise/open-source mix."""
    rng = np.random.default_rng(seed)
    engine = TrustAttestationEngine()
    ats_scores = []

    for i in range(n):
        server_type = rng.choice(["enterprise", "community", "unknown", "malicious"],
                                 p=[0.35, 0.30, 0.20, 0.15])

        if server_type == "enterprise":
            crypto = CryptographicEvidence(cert_valid=True, cert_not_expired=True,
                                           signature_verified=True, tls_version="TLSv1.3",
                                           cert_age_days=int(rng.integers(90, 730)))
            rep = ReputationEvidence(known_cve_count=0, registry_age_days=int(rng.integers(365, 2000)),
                                     community_score=rng.uniform(0.8, 1.0), verified_publisher=True,
                                     downloads_last_30d=int(rng.integers(5000, 50000)))
            beh = BehavioralEvidence(prior_violations=0)
            att = AttestationEvidence(proof_of_non_malicious=True, zk_proof_valid=True,
                                      attestation_age_hours=rng.uniform(0, 8))

        elif server_type == "community":
            crypto = CryptographicEvidence(cert_valid=rng.random() > 0.2,
                                           cert_not_expired=rng.random() > 0.1,
                                           signature_verified=rng.random() > 0.3,
                                           tls_version="TLSv1.3" if rng.random() > 0.4 else "TLSv1.2")
            rep = ReputationEvidence(known_cve_count=int(rng.integers(0, 2)),
                                     registry_age_days=int(rng.integers(60, 1000)),
                                     community_score=rng.uniform(0.5, 0.85),
                                     verified_publisher=rng.random() > 0.6,
                                     downloads_last_30d=int(rng.integers(200, 5000)))
            beh = BehavioralEvidence(prior_violations=int(rng.integers(0, 2)))
            att = AttestationEvidence(proof_of_non_malicious=rng.random() > 0.3)

        elif server_type == "unknown":
            crypto = CryptographicEvidence(cert_valid=rng.random() > 0.5,
                                           signature_verified=rng.random() > 0.6,
                                           tls_version="TLSv1.2")
            rep = ReputationEvidence(known_cve_count=int(rng.integers(0, 3)),
                                     registry_age_days=int(rng.integers(1, 120)),
                                     community_score=rng.uniform(0.2, 0.6),
                                     verified_publisher=False)
            beh = BehavioralEvidence(request_rate_anomaly=rng.random() > 0.7,
                                     prior_violations=int(rng.integers(0, 3)))
            att = AttestationEvidence(proof_of_non_malicious=rng.random() > 0.7)

        else:  # malicious
            crypto = CryptographicEvidence(cert_valid=rng.random() > 0.6,
                                           signature_verified=False, tls_version="TLSv1.2")
            rep = ReputationEvidence(known_cve_count=int(rng.integers(1, 5)),
                                     registry_age_days=int(rng.integers(1, 30)),
                                     community_score=rng.uniform(0.0, 0.3),
                                     verified_publisher=False)
            beh = BehavioralEvidence(request_rate_anomaly=True, unusual_tool_sequence=True,
                                     prior_violations=int(rng.integers(2, 6)))
            att = AttestationEvidence(proof_of_non_malicious=False)

        result = engine.compute(f"server-{i:03d}", crypto, rep, beh, att)
        ats_scores.append(result.ats)

    return ats_scores


def plot_ats_distribution(scores: list[float], output_path: Path) -> None:
    arr = np.array(scores)
    quarantined = (arr < 0.50).sum()
    restricted = ((arr >= 0.50) & (arr < 0.75)).sum()
    trusted = (arr >= 0.75).sum()
    n = len(arr)

    kde = gaussian_kde(arr, bw_method=0.15)
    x = np.linspace(0, 1, 500)
    density = kde(x)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.fill_between(x[x < 0.50], density[x < 0.50], alpha=0.18, color="red")
    ax.fill_between(x[(x >= 0.50) & (x < 0.75)], density[(x >= 0.50) & (x < 0.75)],
                    alpha=0.18, color="orange")
    ax.fill_between(x[x >= 0.75], density[x >= 0.75], alpha=0.18, color="green")

    ax.plot(x, density, color="#1E50B0", linewidth=2.2)

    ax.axvline(0.50, color="red", linewidth=1.2, linestyle="--", alpha=0.8)
    ax.axvline(0.75, color="orange", linewidth=1.2, linestyle="--", alpha=0.8)
    ax.axvline(arr.mean(), color="#1E50B0", linewidth=1.5, linestyle=":", alpha=0.8,
               label=f"μ={arr.mean():.2f}")

    ax.text(0.25, density.max() * 0.92,
            f"Quarantined\n{quarantined/n*100:.0f}%", ha="center", fontsize=9, color="red")
    ax.text(0.625, density.max() * 0.92,
            f"Restricted\n{restricted/n*100:.0f}%", ha="center", fontsize=9, color="darkorange")
    ax.text(0.875, density.max() * 0.92,
            f"Trusted\n{trusted/n*100:.0f}%", ha="center", fontsize=9, color="green")

    ax.set_xlabel("Agent Trust Score (ATS)", fontsize=11)
    ax.set_ylabel("Density (KDE)", fontsize=11)
    ax.set_title(f"ATS Distribution — {n} MCP Servers", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, None)
    ax.grid(True, alpha=0.2, linestyle="--")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    scores = sample_mcp_servers(n=200)
    arr = np.array(scores)
    print(f"n=200 MCP servers | mean ATS={arr.mean():.3f} (paper: 0.72)")
    print(f"  Quarantined (<0.50): {(arr<0.50).sum()} ({(arr<0.50).mean()*100:.0f}%)")
    print(f"  Restricted (0.50-0.75): {((arr>=0.50)&(arr<0.75)).sum()} ({((arr>=0.50)&(arr<0.75)).mean()*100:.0f}%)")
    print(f"  Trusted (>=0.75): {(arr>=0.75).sum()} ({(arr>=0.75).mean()*100:.0f}%)")

    out_dir = ROOT / "figures"
    out_dir.mkdir(exist_ok=True)
    plot_ats_distribution(scores, out_dir / "fig4_ats_distribution.pdf")
    plot_ats_distribution(scores, out_dir / "fig4_ats_distribution.png")
