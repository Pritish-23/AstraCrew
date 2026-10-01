# AstraCrew Quickstart Guide

This guide will get you up and running with AstraCrew in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Git (optional, for cloning)
- OpenAI API key (optional, only needed for `--live` mode or `--mode crew`)

## Installation

### Option 1: Clone from GitHub

```bash
git clone https://github.com/Pritish-23/AstraCrew.git
cd AstraCrew
```

### Option 2: Download ZIP

Download and extract the project, then navigate to the directory.

### Set Up Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

## Basic Usage

### 1. Run Your First Audit (No API Key Needed!)

```bash
python main.py --mode deterministic
```

This runs a complete security audit using deterministic mock responses. Output:
- Console summary with resilience score
- `reports/audit_report.json` - Structured findings
- `reports/audit_report.pdf` - Executive PDF dossier

### 2. Test Specific Targets

```bash
# Test only the mock assistant
python main.py --mode deterministic --targets MOCK

# Test only RAG pipeline
python main.py --mode deterministic --targets RAG

# Test only agentic tool-caller
python main.py --mode deterministic --targets AGENTIC

# Test multiple (default is all three)
python main.py --mode deterministic --targets "MOCK,RAG,AGENTIC"
```

### 3. Use Live LLM (Requires API Key)

```bash
# Set up your API key
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-your-key-here

# Run with live OpenAI model
python main.py --mode deterministic --live --model gpt-4o-mini
```

### 4. Run Agentic Mode (Requires API Key)

```bash
python main.py --mode crew --model gpt-4o-mini
```

This launches a hierarchical CrewAI team that reasons about attack strategy.

### 5. Launch Interactive Dashboard

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Understanding the Output

### Console Output

```
======================================================================
                    AUDIT SCORECARD                           
======================================================================
Target Examined          : AstraBank Suite [Mock Sandbox]
Total Probes Executed    : 13
Confirmed Breaches       : 5
Breach Rate              : 38.46%
Mathematical Resilience  : 50.00 / 100.0
----------------------------------------------------------------------
Executive Verdict        : Security audit (deterministic mode) 
                          concluded with Resilience Index: 50.0/100.0
                          (HIGH_RISK). 5 boundary breach(es) detected
                          across 13 adversarial vectors...
======================================================================
```

### Resilience Score Interpretation

- **90-100**: LOW_RISK - Excellent security posture
- **70-89**: MODERATE_RISK - Good, but room for improvement
- **40-69**: HIGH_RISK - Significant vulnerabilities detected
- **0-39**: CRITICAL_RISK - Immediate remediation required

### JSON Report (`reports/audit_report.json`)

Contains:
- Complete probe execution traces
- Gate evaluation verdicts
- Resilience metrics
- OWASP category breakdown
- Remediation recommendations

### PDF Report (`reports/audit_report.pdf`)

Executive-ready dossier with:
- KPI scorecard
- OWASP coverage table
- Detailed probe findings
- Git-style prompt hardening diff
- Drop-in FastAPI middleware code

## Common Options

```bash
# Change canary token (for testing your own systems)
python main.py --canary MY_SECRET_TOKEN

# Set compliance threshold
python main.py --min-resilience 80.0

# Specify output paths
python main.py \
  --export-json results/my_audit.json \
  --export-pdf results/my_audit.pdf

# Use different OpenAI model
python main.py --live --model gpt-4o
```

## CI/CD Integration

### GitHub Actions (Automated)

The `.github/workflows/ci.yml` workflow runs automatically on:
- Every push to `main`
- Every pull request to `main`

It:
1. Lints code with `ruff`
2. Runs full test suite
3. Executes deterministic audit
4. Fails if resilience < 40.0
5. Archives audit artifacts

### Manual CI Run

```bash
# Run the same checks CI runs
ruff check .
pytest -v
python main.py --min-resilience 40.0
```

## Troubleshooting

### "No module named 'crewai'"

You didn't activate the virtual environment or install dependencies:

```bash
# Activate venv first
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### "Gate 2 skipped: no OPENAI_API_KEY configured"

This is normal for deterministic mode. Gate 2 only activates when Gate 1 is ambiguous. If you want full Gate 2 coverage, use `--live` mode.

### PDF Generation Fails

Make sure ReportLab is installed:

```bash
pip install reportlab
```

### Streamlit Dashboard Won't Start

```bash
pip install streamlit
streamlit run app.py
```

## Next Steps

- **Read the full documentation**: `README.md`
- **Understand the architecture**: Review `docs/` folder
- **Contribute**: See `CONTRIBUTING.md`
- **Add custom probes**: See examples in `probes/` directory
- **Integrate into your app**: Use the remediation outputs

## Key Files to Explore

- `orchestrator.py` - Main audit logic
- `probes/` - All 13 attack probes
- `evaluation/gate_one.py` - Deterministic detection
- `evaluation/gate_two.py` - LLM semantic arbiter
- `remediation/prompt_patcher.py` - Automated hardening
- `config/agents.yaml` - CrewAI agent definitions

## Need Help?

Open an issue on GitHub or check the documentation in the repository.

Happy red-teaming! 🛡️
