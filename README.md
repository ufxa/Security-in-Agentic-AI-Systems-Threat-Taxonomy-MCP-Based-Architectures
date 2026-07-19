# Security in Agentic AI Systems: Threat Taxonomy and Defense Frameworks for MCP-Based Architectures

**Author:** Allan Douglas Costa  
**Target Journal:** IEEE Transactions on Information Forensics and Security (TIFS)  
**Status:** Submission Ready — July 2026  
**Score:** 9.28/10 (Internal Peer Review)

---

## Abstract

The Model Context Protocol (MCP) has emerged as the dominant architecture for orchestrating agentic AI systems across enterprise environments, with over 437,000 downloads of MCP-compatible packages. However, the rapid proliferation of MCP-based deployments has outpaced security standardization, leaving critical vulnerabilities undocumented and defenseless.

This paper presents **MCP-TaxSec**, a six-vector threat taxonomy validated against 50 vulnerabilities (24 CVEs, 13 critical-severity incidents), and **AEGIS-MCP**, a five-layer runtime defense framework achieving 94.7% attack detection accuracy with 2.1% false positive rate. We introduce the **Agent Trust Score (ATS)** metric — a quantitative trust quantification mechanism combining cryptographic evidence (40%), reputation (30%), behavioral analysis (20%), and attestation signals (10%).

Empirical evaluation demonstrates AEGIS-MCP reduces mean Time-to-Remediation-and-Containment (TTRC) from 240+ seconds to 2.4 seconds, with latency overhead of 14.2% remaining within operational tolerance for enterprise deployments.

---

## Key Contributions

| Contribution | Description |
|---|---|
| **MCP-TaxSec** | 6-vector threat taxonomy (TI, MP, PM, TC, SC, AA) validated against VulnerableMCP dataset |
| **AEGIS-MCP** | 5-layer runtime defense (Protocol → Policy → Trust → Audit → Alert) |
| **ATS Metric** | Quantitative trust score: ATS = 0.4C + 0.3R + 0.2B + 0.1A |
| **VulnerableMCP** | Dataset: 50 vulnerabilities, 24 CVEs, 13 critical incidents |
| **CVE-2025-6514** | CVSS 9.6 critical vulnerability analysis affecting 437,000+ downloads |

---

## MCP-TaxSec: Six-Vector Threat Taxonomy

```
MCP Attack Vectors
├── TI — Tool Injection (TI-1 to TI-4)
├── MP — Memory Poisoning (MP-1 to MP-3)
├── PM — Prompt Manipulation (PM-1 to PM-3)
├── TC — Transport Compromise (TC-1 to TC-2)
├── SC — Supply Chain Attack (SC-1 to SC-4)
└── AA — Agent-to-Agent Exploitation (AA-1 to AA-3)
```

---

## AEGIS-MCP: Five-Layer Defense Architecture

```
L5  Alert & Response      — Automated containment, capability revocation
L4  Forensic Audit        — Cryptographic O(1) proof generation, GDPR compliance
L3  Trust Attestation     — ATS computation, threshold enforcement (min 0.50)
L2  Policy Enforcement    — Capability-based access control, schema validation
L1  Protocol Interception — JSON-RPC boundary monitoring, schema validation
```

---

## Experimental Results

| Metric | AEGIS-MCP | Baseline | Delta |
|---|---|---|---|
| Detection Rate | **94.7%** | 31.2% | +63.5% |
| False Positive Rate | **2.1%** | 0.8% | +1.3% |
| AUC (ROC) | **0.962** | 0.812 | +0.150 |
| TTRC | **2.4s** | 240+s | -99% |
| Latency Overhead | 14.2% | 0% | +14.2% |

---

## Agent Trust Score (ATS)

```
ATS = 0.4·C + 0.3·R + 0.2·B + 0.1·A

Where:
  C = Cryptographic evidence score  (0-1)
  R = Reputation score              (0-1)
  B = Behavioral anomaly inverse    (0-1)
  A = Attestation signal strength   (0-1)

Thresholds:
  ATS >= 0.75  → Trusted   (38% of sampled servers)
  ATS  0.50-0.75 → Restricted (31%)
  ATS <  0.50  → Quarantined (31%)
```

---

## Repository Structure

```
.
├── manuscript/
│   ├── main.tex              # Main LaTeX source (IEEE TIFS format)
│   ├── glossario.tex         # Glossary of technical terms
│   ├── main.pdf              # Compiled manuscript
│   └── figures/
│       ├── taxonomy_diagram.drawio   # MCP-TaxSec taxonomy (editable)
│       ├── taxonomy_diagram.png      # Taxonomy diagram (300dpi)
│       ├── aegis_architecture.drawio # AEGIS-MCP architecture (editable)
│       └── aegis_architecture.png    # Architecture diagram (300dpi)
├── artigo_FINAL_COMPLETO.pdf # Final compiled PDF
├── compile_pdf.sh            # Compilation script (Tectonic/XeLaTeX)
├── RELATORIO_ACESSIBILIDADE_FINAL.md  # WCAG 2.1 AA audit report (98.75%)
├── RELATÓRIO_VALIDAÇÃO_FINAL.md       # Peer review validation report
└── README.md
```

---

## Compilation

Requires [Tectonic](https://tectonic-typesetting.github.io/) (lightweight XeLaTeX):

```bash
# Install Tectonic (macOS)
brew install tectonic

# Compile manuscript
cd manuscript
tectonic --outdir build main.tex

# Output: manuscript/build/main.pdf
```

---

## Accessibility

This manuscript achieves **98.75% WCAG 2.1 AA compliance**:

- 12pt font size (upgraded from IEEE default 10pt)
- High-contrast color links (8.6:1 ratio)
- Alt-text for all 9 figures (55 words each)
- PDF/A archival format
- Semantic LaTeX structure

---

## Citation

```bibtex
@article{costa2026security,
  title   = {Security in Agentic {AI} Systems: Threat Taxonomy and Defense
             Frameworks for {MCP}-Based Architectures},
  author  = {Costa, Allan Douglas},
  journal = {IEEE Transactions on Information Forensics and Security},
  year    = {2026},
  note    = {Submitted}
}
```

---

## License

This research is submitted for peer review at IEEE TIFS. The code and datasets are released under [MIT License](LICENSE) for reproducibility. The manuscript text is under IEEE copyright upon acceptance.

---

*Sec365 Security Research — LICA/UFRA — INCT iAmazonia*
