# Getting Started with PyShield-SMR

This guide takes you from a fresh clone to a running analysis in under 10 minutes.
Windows (PowerShell) instructions come first; Linux/macOS equivalents follow each step.

---

## Prerequisites

| Tool | Minimum version | How to check |
|---|---|---|
| Python | 3.10 | `python --version` |
| Git | any | `git --version` |

Download Python from [python.org](https://www.python.org/downloads/).
On Windows, tick **"Add Python to PATH"** during installation.

---

## 1. Clone the repository

```powershell
# Windows (PowerShell)
git clone https://github.com/theonlyallana/pyshield-smr.git
cd pyshield-smr
```

```bash
# Linux / macOS
git clone https://github.com/theonlyallana/pyshield-smr.git
cd pyshield-smr
```

---

## 2. Create and activate a virtual environment

```powershell
# Windows
python -m venv .venv
.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate
```

After activation you will see `(.venv)` at the start of your prompt.

> **PowerShell execution-policy error?**  Run this once, then retry the Activate step:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

---

## 3. Install dependencies

```powershell
pip install -e ".[dev]"
```

That command installs the package in editable mode, including `numpy`, `scipy`,
`pyyaml`, and `jinja2`, plus `pytest`, `ruff`, and `mypy`. It registers the
`pyshield` command. There is no `requirements.txt`. `requirements-dev.txt`
lists the same dependencies for `pip install -r`, but that command does not
install the package itself.

Runtime-only install (no test tools):

```powershell
pip install -e .
```

---

## 4. Verify the installation

### Governance audit

```powershell
python tasks/audit_process.py --verbose
```

The script runs 12 checks. On Python 3.12 it reported `audit: PASS (12 checks)`. `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and `docs/guides/QA.md` are not required. `tasks/memory/MEMORY.md`, `tasks/memory/feedback.md`, and `tasks/process_state.md` keep their original dates.

### Test suite

```powershell
pytest -q
```

On Python 3.12 this reported 254 passed. `pytest -q tests/integration` reported 12 passed.

---

## 5. Run your first analysis

```powershell
pyshield run examples/01_point_kernel_shielding/config.yaml
```

Expected console output:

```
... | INFO | pyshield_smr.workflow.runner | Starting analysis: Co-60 Behind 5cm Lead
... | INFO | pyshield_smr.workflow.runner |   Resolving Co-60 at 1.00e+06 Bq
... | INFO | pyshield_smr.workflow.runner |   Resolved 2 photon lines
... | INFO | pyshield_smr.workflow.runner |   Building slab: lead 5.0 cm
... | INFO | pyshield_smr.workflow.runner |   Engine: point-kernel
... | INFO | pyshield_smr.workflow.runner |     Dose rate at receptor: 1.721e-08 Sv/h
... | INFO | pyshield_smr.workflow.runner |   Zone assigned: uncontrolled
... | INFO | pyshield_smr.workflow.runner | All outputs written to reports/<timestamp>_Co-60_Behind_5cm_Lead
```

Open the timestamped report folder:

```powershell
# Windows — opens File Explorer
explorer reports
```

Then double-click `report.html` to open in your browser, or `report.md` to read in a text editor.

```bash
# Linux
xdg-open reports/*/report.html

# macOS
open reports/*/report.html
```

The report folder always contains four files:

| File | Contents |
|---|---|
| `report.md` | Human-readable analysis summary |
| `report.html` | Styled HTML report (open in browser) |
| `qa_manifest.json` | Code version, nuclear-data SHA-256 hashes, runtime, warnings |
| `spec_used.yaml` | Exact YAML spec that produced this result |

---

## 6. Run all five examples

```powershell
# Example 2 — Monte Carlo photon transmission through lead
pyshield run examples/02_monte_carlo_transmission/config.yaml

# Example 3 — Activation product decay chain (Co-60 in steel)
pyshield run examples/03_activation_decay/config.yaml

# Example 4 — ALARP shielding optimisation (Cs-137 vault)
pyshield run examples/04_alarp_optimization/config.yaml

# Example 5 — Simplified SMR compartment: composite shield + multiple receptors
pyshield run examples/05_smr_compartment/config.yaml
```

Each command writes a timestamped folder under `reports/`. Examples 03, 04, and 05 still compute a point-kernel dose from the source written in the YAML. Example 02 requests `engine: monte_carlo`; the runner logs that Monte Carlo is not integrated and does not report a dose. Examples 04 and 05 do not run the optimiser or the uncertainty sampler.

---

## 7. Understand and edit an analysis spec

Every analysis is described by a YAML file that you can version-control, diff, and review. Open `examples/01_point_kernel_shielding/config.yaml` in any text editor:

```yaml
schema_version: "1.0.0"
case_name: "Co-60 Behind 5cm Lead"
engine: point_kernel

geometry:
  type: infinite_slab
  material: lead
  thickness_m: 0.05      # Change this to alter the shielding

source:
  type: point_isotropic
  position_m: [0.0, 0.0, 0.0]
  nuclide: Co-60
  activity_bq: 1.0e6

receptor:
  type: point
  position_m: [0.0, 0.0, 1.0]   # 1 m from source

buildup_material: lead
report_format: [markdown, html]
```

**Try it:** Change `thickness_m: 0.05` to `thickness_m: 0.10` and re-run. Each run goes to a new timestamped folder. Compare the dose rate printed for the two runs; this guide does not quote a ratio.

---

## 8. Repository

The public repository is https://github.com/theonlyallana/pyshield-smr.

There is no `.github/workflows` directory, so GitHub Actions does not run lint, tests, or the governance audit on push. The README does not carry a CI badge.

---

## 9. Quick-reference command table

| Intent | Windows (PowerShell) | Linux / macOS |
|---|---|---|
| Activate venv | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| Install package and dev tools | `pip install -e ".[dev]"` | same |
| Run governance audit | `python tasks/audit_process.py --verbose` | same |
| Run all tests | `pytest -q` | same |
| Run unit tests | `pytest -q tests/unit` | same |
| Run example 1 | `pyshield run examples/01_point_kernel_shielding/config.yaml` | same |
| Run example 2 | `pyshield run examples/02_monte_carlo_transmission/config.yaml` | same; the runner warns that Monte Carlo is not integrated and reports no dose. The CLI has no `--workers` flag |
| Open report folder | `explorer reports` | `open reports/` |
| Lint | `ruff check .` | same |
| Format | `ruff format .` | same |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'pyshield_smr'`**
The package is not installed.  Make sure the venv is active, then run `pip install -e .`.

**`'pyshield' is not recognised as an internal or external command`**
The venv is not active.  Run `.venv\Scripts\Activate.ps1` first.

**`cannot be loaded because running scripts is disabled`**
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**`No module named 'scipy'`** or **`No module named 'jinja2'`**
Run `pip install -e ".[dev]"` with the virtual environment active.

**Report rendering error — template not found**
Ensure `reports/templates/report.md.j2` and `report.html.j2` exist. If not, restore from git:
```powershell
git checkout HEAD -- reports/templates/
```

**Audit fails — missing required files**
`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and `docs/guides/QA.md` are not in the current tree. Checking them out from an older commit restores files that were deleted on purpose; decide that separately rather than treating the audit failure as a local checkout mistake.

---

## What to read next

| | |
|---|---|
| `docs/theory/01_transport_theory.md` | Boltzmann equation, photon interactions, H*(10) dose quantity |
| `docs/theory/02_point_kernel.md` | Detailed derivation of the point-kernel calculation |
| `docs/theory/07_alarp.md` | ALARP regulatory framework and optimisation formulation |
| `docs/theory/PHYSICS_CHANGELOG.md` | Recorded physics changes. There is no `docs/guides/QA.md` |
| `docs/guides/HPC.md` | HPC helpers, and which CLI flags are absent |
| `ARCHITECTURE.md` | Layered design, module map, extension points |
