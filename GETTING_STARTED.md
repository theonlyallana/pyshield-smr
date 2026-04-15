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
git clone https://github.com/YOUR_GITHUB_USERNAME/pyshield-smr.git
cd pyshield-smr
```

```bash
# Linux / macOS
git clone https://github.com/YOUR_GITHUB_USERNAME/pyshield-smr.git
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
pip install -r requirements-dev.txt
pip install -e .
```

`requirements-dev.txt` installs `numpy`, `scipy`, `pyyaml`, `jinja2` (runtime)
plus `pytest`, `ruff`, `mypy` (dev/test).  The `-e .` registers the `pyshield`
CLI command and lets you edit code without reinstalling.

If you only need to run analyses (no tests or linting):

```powershell
pip install -r requirements.txt
pip install -e .
```

---

## 4. Verify the installation

### Governance audit (should show 13 green ticks)

```powershell
python tasks/audit_process.py --verbose
```

Expected tail of output:

```
  ...
  ✓ examples-consistency: all 5 example directories have config.yaml
audit: PASS (13 checks)
```

### Test suite

```powershell
pytest -q
```

All tests should pass.  Unit tests alone are faster if you just want a quick sanity check:

```powershell
pytest -q tests/unit
```

---

## 5. Run your first analysis

```powershell
pyshield run examples/01_point_kernel_shielding/config.yaml
```

Expected console output:

```
INFO | Starting analysis: Co-60 Behind 5cm Lead
INFO | Resolving Co-60 at 1.00e+06 Bq
INFO | Resolved 2 photon lines
INFO | Building slab: lead 5.0 cm
INFO | Engine: point-kernel
INFO | Dose rate at receptor: 1.721e-08 Sv/h
INFO | Zone assigned: uncontrolled
INFO | All outputs written to reports\2026-..._Co-60_Behind_5cm_Lead\
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

Each produces its own timestamped folder under `reports/`.

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

**Try it:** Change `thickness_m: 0.05` to `thickness_m: 0.10` and re-run. The dose rate drops by roughly a factor of 5–10. Each run goes to a new timestamped folder — nothing is ever overwritten.

---

## 8. Push to GitHub and enable CI

### Step 1 — Create an empty GitHub repository

Go to [github.com/new](https://github.com/new):
- Name: `pyshield-smr`
- Visibility: **Public** (required for portfolio visibility)
- **Do not** tick "Add a README", "Add .gitignore", or "Choose a licence" — the repo already has all of these.

### Step 2 — Commit and push

```powershell
git add .
git commit -m "Initial commit — PyShield-SMR v0.1.1"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/pyshield-smr.git
git push -u origin main
```

### Step 3 — Watch CI run

Click the **Actions** tab on your repository page. GitHub will automatically run the CI pipeline in `.github/workflows/ci.yml`, testing across Python 3.10, 3.11, and 3.12:

- Lint (`ruff`)
- Type checks (`mypy`)
- Governance audit (`python tasks/audit_process.py --verbose`)
- Unit tests
- Integration tests

Once the pipeline passes you will see a green ✓ in the Actions tab and a green badge on your README.

### Step 4 — Update the badge URLs

In `README.md`, replace the two occurrences of `YOUR_GITHUB_USERNAME` with your actual username:

```powershell
# PowerShell — change 'andrewallana' to your actual GitHub username
(Get-Content README.md) -replace 'YOUR_GITHUB_USERNAME', 'andrewallana' | Set-Content README.md
git add README.md
git commit -m "docs: add real CI badge URLs"
git push
```

---

## 9. Quick-reference command table

| Intent | Windows (PowerShell) | Linux / macOS |
|---|---|---|
| Activate venv | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| Install all deps | `pip install -r requirements-dev.txt && pip install -e .` | same |
| Run governance audit | `python tasks/audit_process.py --verbose` | same |
| Run all tests | `pytest -q` | same |
| Run unit tests | `pytest -q tests/unit` | same |
| Run example 1 | `pyshield run examples/01_point_kernel_shielding/config.yaml` | same |
| Run MC example (parallel) | `pyshield run examples/02_monte_carlo_transmission/config.yaml --workers 4` | same |
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
Run `pip install -r requirements-dev.txt` — this installs all dependencies in one go.

**Report rendering error — template not found**
Ensure `reports/templates/report.md.j2` and `report.html.j2` exist. If not, restore from git:
```powershell
git checkout HEAD -- reports/templates/
```

**Audit fails — missing required files**
```powershell
git checkout HEAD -- <path/to/missing/file>
```

---

## What to read next

| | |
|---|---|
| `docs/theory/01_transport_theory.md` | Boltzmann equation, photon interactions, H*(10) dose quantity |
| `docs/theory/02_point_kernel.md` | Detailed derivation of the point-kernel calculation |
| `docs/theory/07_alarp.md` | ALARP regulatory framework and optimisation formulation |
| `docs/guides/QA.md` | Reproducibility, QA manifest, regression testing |
| `docs/guides/HPC.md` | Running large Monte Carlo jobs on a SLURM/PBS cluster |
| `ARCHITECTURE.md` | Layered design, module map, extension points |
