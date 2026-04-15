# PyShield-SMR: Project Summary

## What is This?

**PyShield-SMR** is a comprehensive radiation shielding analysis framework demonstrating expertise in radiation physics and nuclear engineering for Small Modular Reactor (SMR) applications.

Created as a **portfolio project** to showcase skills required by the Rolls-Royce SMR job posting:
- Radiation transport theory (photon Monte Carlo)
- Shielding design & dose-rate assessment
- Uncertainty quantification & sensitivity analysis
- ALARP optimization (cost-benefit analysis)
- Python pre/post-processing workflows
- HPC integration & parallel execution
- Quality governance & reproducibility practices

**Status**: Fully functional v0.1.0 with 5 worked examples, comprehensive documentation, and automated governance.

## The Big Picture

```
User writes YAML spec
        ↓
Runner validates spec (schema, required fields)
        ↓
Source term resolver (nuclide inventory → photon spectrum)
        ↓
Transport engine (point-kernel or Monte Carlo)
        ↓
Post-processors (dose conversion, UQ, ALARP)
        ↓
Report renderer (Markdown + HTML)
        ↓
QA manifest generation (data hashes, governance metadata)
        ↓
Timestamped output folder with all results + audit trail
```

## Key Design Principles

### 1. Physics Clarity
Every calculation is traced back to a physics principle:
- Constants → CODATA 2018
- Cross sections → NIST XCOM
- Dose conversion → ICRP-74
- Buildup factors → ANS standards

**Not** a black box. You can understand *why* the code does what it does.

### 2. Separation of Concerns
- **Physics layer** (constants, materials, cross sections): Physics domain logic, no I/O
- **Transport layer** (geometry, tally, MC): Transport algorithms, independent of applications
- **Shielding layer** (point kernel, dose rate): Application-specific dose calculations
- **Workflow layer** (runner, CLI): Orchestration and user interaction
- **IO layer** (YAML, reports): Data serialization and presentation

Each layer is testable independently.

### 3. Reproducibility via Data Hashing
Every analysis records SHA-256 hashes of all nuclear data files. Months later:
- Can verify exact data files were used
- Detect accidental data corruption
- Ensure regulatory audit trail

This is the **nuclear engineering gold standard**.

### 4. ALARP as First-Class Citizen
ALARP (As Low As Reasonably Practicable) isn't an afterthought—it's a built-in optimization:
```
Minimize: health_risk + cost
Subject to: dose_rate ≤ regulatory_threshold
```

Demonstrates understanding that shielding design is a **trade-off surface**, not a binary constraint.

### 5. Governance via Multi-Agent System
Like a real nuclear engineering team, PyShield-SMR has specialist agents:
- **Physics Governor**: Owns constants, cross sections, physics changelog
- **Transport Author**: Owns MC and point-kernel engines
- **QA Governor**: Owns tests, audit, CI/CD
- **Technical Author**: Owns documentation

Each specialist certifies correctness in their domain. Handoffs include verification protocols.

## What's Implemented

### Physics & Transport (~2500 lines)
✓ Constants (CODATA 2018)  
✓ Materials library (6 common materials)  
✓ Cross section interpolation (log-log, NIST XCOM)  
✓ Attenuation coefficient calculation  
✓ Buildup factor (Taylor two-term, ANS-6.1.1)  
✓ Photon Monte Carlo transport (analog)  
✓ Klein-Nishina scattering (Kahn rejection method)  
✓ Variance reduction (implicit capture, Russian roulette + splitting)  
✓ Tallies (energy binning with relative error estimation)  
✓ Geometry (slab stacks, spherical shells)  
✓ MCNP-style I/O (pedagogical deck emission)  

### Shielding Applications (~800 lines)
✓ Point-kernel dose-rate assessment  
✓ Dose conversion (ICRP-74 H*(10))  
✓ DPA estimation (NRT model)  
✓ Gamma heating calculation  
✓ Detector response simulation  
✓ Radiological zone assignment (UK IRR17 thresholds)  

### Source Terms & Activation (~600 lines)
✓ Nuclide inventory resolution  
✓ Gamma-line extraction (photon spectrum from decay data)  
✓ Bateman equation solver (matrix exponential, scipy.linalg.expm)  
✓ Burnup calculation (activation product buildup and decay)  
✓ Multi-nuclide decay chains  

### Analysis Features (~1200 lines)
✓ Uncertainty quantification (Latin hypercube sampling, Morris screening)  
✓ Sensitivity analysis (elementary effects)  
✓ ALARP optimization (SLSQP constrained minimization)  
✓ Uncertainty propagation (Monte Carlo sampling over distributions)  

### Workflow & Orchestration (~1500 lines)
✓ YAML schema (validation, versioning, migration)  
✓ Runner (spec → execution → report)  
✓ CLI (run, validate, hash-data, emit-slurm subcommands)  
✓ Report rendering (Jinja2 templates, Markdown + HTML)  
✓ QA manifest generation (SHA-256 data hashing, platform info)  
✓ HPC support (ProcessPoolExecutor, SLURM/PBS script emission)  

### Governance & QA (~800 lines)
✓ 12-point automated audit (AGENTS.md, RUNBOOK.md, data presence, etc.)  
✓ Pre-commit hooks (ruff, mypy, audit_process.py)  
✓ GitHub Actions CI (matrix Python 3.10/3.11/3.12)  
✓ Regression testing (tolerance-based validation)  
✓ Multi-agent specialist system (physics-governor, transport-author, qa-governor, etc.)  
✓ Append-only logbooks (audit trail)  

### Documentation (~3000 lines)
✓ Theory docs: Transport, point-kernel, Monte Carlo, sources, activation, UQ, ALARP  
✓ Guide docs: Getting started, QA governance, HPC workflows, MCNP interop  
✓ Architecture docs: AGENTS.md, RUNBOOK.md, PROCESS_ARCHITECTURE.md  
✓ Example analyses: 5 worked examples (point-kernel, MC, activation, ALARP, SMR)  
✓ API docstrings: Comprehensive (~500 functions documented)  

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.10+ | Standard in scientific computing; PyPI ecosystem |
| Numerics | NumPy, SciPy | Industry standard; fast (vectorized); trusted |
| YAML | pyyaml | Human-readable specs; easy version control |
| Templates | Jinja2 | Flexible report generation |
| Testing | pytest | Standard; fixtures, parametrization, coverage plugins |
| Linting | ruff | Fast, modern, zero-config |
| Type checking | mypy | Catches bugs before runtime |
| CI/CD | GitHub Actions | Free; matrix testing, caching |
| Docs | Markdown | Portable; rendered on GitHub |
| Data format | JSON | Schema-able; Python native |

## File Organization

```
pyshield-smr/
├── README.md                          # Quick overview
├── GETTING_STARTED.md                 # Installation & first run
├── PROJECT_SUMMARY.md                 # This file
├── ARCHITECTURE.md                    # Design decisions, layering
├── AGENTS.md                          # Multi-agent specialist system
├── RUNBOOK.md                         # Standard commands & workflows
├── CHANGELOG.md                       # Release notes & history
│
├── pyshield_smr/                      # Main package
│   ├── physics/                       # Radiation physics (constants, materials, cross sections)
│   ├── transport/                     # Photon transport (geometry, MC, tallies)
│   ├── shielding/                     # Shielding applications (point kernel, dose rate)
│   ├── sources/                       # Source terms (nuclide inventory, spectra)
│   ├── activation/                    # Activation & decay (Bateman, burnup)
│   ├── uq/                            # Uncertainty quantification (sampling, sensitivity)
│   ├── alarp/                         # ALARP optimization (cost-benefit design)
│   ├── workflow/                      # Orchestration (schema, runner, QA)
│   ├── cli/                           # Command-line interface
│   ├── hpc/                           # HPC support (parallel, SLURM/PBS)
│   └── io/                            # I/O utilities (YAML, reporting, hashing)
│
├── data/                              # Nuclear data (vendored)
│   ├── cross_sections/                # Photon mass attenuation
│   ├── buildup_factors/               # Taylor two-term parameters
│   ├── flux_to_dose/                  # ICRP-74 dose coefficients
│   └── decay_chains/                  # Nuclide decay data
│
├── examples/                          # Worked examples
│   ├── 01_point_kernel_shielding/     # Basic point-kernel
│   ├── 02_monte_carlo_transmission/   # MC photon transport
│   ├── 03_activation_decay/           # Bateman equations
│   ├── 04_alarp_optimization/         # Cost-benefit shielding
│   └── 05_smr_compartment/            # Comprehensive SMR scenario
│
├── tests/                             # Test suite
│   ├── unit/                          # Fast, isolated tests
│   ├── integration/                   # End-to-end workflows
│   └── data/                          # Test fixtures
│
├── docs/                              # Documentation
│   ├── theory/                        # Physics fundamentals (7 docs)
│   ├── guides/                        # How-to guides (4 docs)
│   └── _generated/                    # Auto-generated docs (API, coverage)
│
├── reports/                           # Analysis output (timestamped folders)
├── tasks/                             # Governance infrastructure
├── .github/workflows/                 # CI/CD configuration
├── .pre-commit-config.yaml            # Pre-commit hooks
├── pyproject.toml                     # Package metadata & build config
└── LICENSE                            # MIT license
```

## Learning Path

### For Interviewers (30 minutes)

1. **Read PROJECT_SUMMARY.md** (this file) — Understand scope & design
2. **Skim ARCHITECTURE.md** — See how pieces fit together
3. **Run GETTING_STARTED.md** — Install & execute example 1
4. **Glance at example YAML** (examples/01) — Understand user interface
5. **Check docs/theory/02_point_kernel.md** — See physics rigor

**Outcome**: You understand the breadth of skills demonstrated.

### For Deep Learning (2-3 hours)

1. **Work through all 5 examples** — See features progressively
2. **Read theory docs** — Understand physics principles
3. **Inspect source code** (pyshield_smr/shielding/point_kernel.py, etc.) — See implementation
4. **Run tests** — `pytest tests/ -v` shows code quality
5. **Review docs/guides/QA.md** — Understand governance practices

**Outcome**: You can explain the technical approach to others.

### For Contribution (4-6 hours)

1. **Read AGENTS.md** — Understand specialist roles
2. **Review tasks/PROCESS_ARCHITECTURE.md** — Understand development process
3. **Check out tasks/agents/[role]/** — Study playbooks & logbooks
4. **Make a small change** (e.g., add a new material)
5. **Run audit_process.py** — Ensure governance compliance
6. **Propose change** via PR with physics justification

**Outcome**: You can extend the framework safely.

## Demonstrating Core Skills

### Radiation Transport Theory
✓ Photon Monte Carlo with variance reduction (implicit capture, roulette/splitting)  
✓ Klein-Nishina scattering (Kahn rejection method)  
✓ Tally estimation with relative error  
✓ Geometric considerations (slab, spherical)  

**Code locations**:
- pyshield_smr/transport/monte_carlo.py (main algorithm)
- pyshield_smr/transport/variance_reduction.py (VR techniques)
- docs/theory/03_monte_carlo.md (detailed explanation)

### Shielding & Dose Assessment
✓ Point-kernel method with buildup factors  
✓ Attenuation coefficient interpolation  
✓ ICRP-74 dose conversion  
✓ Radiological zone assignment  

**Code locations**:
- pyshield_smr/shielding/point_kernel.py (main calculation)
- docs/theory/02_point_kernel.md (theory & limitations)
- examples/01, 02 (worked examples)

### Uncertainty Quantification
✓ Latin hypercube sampling (stratified, correlated)  
✓ Morris elementary effects (sensitivity screening)  
✓ Propagation of multiple distributions (lognormal, normal, uniform)  
✓ Convergence analysis (relative error vs. N_samples)  

**Code locations**:
- pyshield_smr/uq/monte_carlo_uq.py (main module)
- docs/theory/06_uq.md (theory)
- examples/05 (UQ demonstration)

### ALARP Optimization
✓ Constrained minimization (SLSQP gradient-based)  
✓ Multi-objective formulation (health + cost)  
✓ Sensitivity analysis (how dose varies with thickness)  
✓ Regulatory compliance (zone thresholds)  

**Code locations**:
- pyshield_smr/alarp/optimiser.py (main solver)
- docs/theory/07_alarp.md (theory & policy)
- examples/04 (shielding optimization)

### Python Workflows
✓ NumPy/SciPy for numerical computing  
✓ Object-oriented design (class hierarchy, inheritance)  
✓ Functional programming (callables, map/filter)  
✓ Exception handling & logging  
✓ Unit testing (pytest)  
✓ Type hints (mypy compatible)  

**Code locations**:
- All pyshield_smr/\*/ modules (OOP + functional patterns)
- tests/ (comprehensive test suite)
- pyshield_smr/cli/main.py (clean CLI design)

### Data Handling & Nuclear Data
✓ Cross-section libraries (NIST XCOM)  
✓ Decay chains (nuclide inventory)  
✓ Data file hashing (SHA-256 reproducibility)  
✓ Version-controlled nuclear data  
✓ Metadata tracking (.meta.json files)  

**Code locations**:
- data/ (vendored nuclear data)
- pyshield_smr/physics/materials.py (material library)
- pyshield_smr/sources/source_term.py (decay chain handling)

### HPC & Parallel Execution
✓ Multiprocessing with independent RNG streams  
✓ Work distribution (history chunking)  
✓ SLURM/PBS script generation  
✓ Convergence estimation (N_histories for target precision)  

**Code locations**:
- pyshield_smr/hpc/parallel.py (main parallelization)
- pyshield_smr/hpc/scheduler.py (job script generation)
- examples/02 (MC with parallel execution)

### Quality & Governance
✓ Automated audit checklist (12-point governance)  
✓ Multi-agent specialist system (AGENTS.md)  
✓ Regression testing with tolerance bands  
✓ QA manifests (data hashing, audit trail)  
✓ Pre-commit hooks & CI/CD  
✓ Physics changelog (traceability)  

**Code locations**:
- tasks/audit_process.py (governance audit)
- tasks/agents/\*/ (specialist playbooks & logbooks)
- tests/integration/regression_values.yaml (regression baselines)
- .github/workflows/ci.yml (CI/CD matrix)

## Statistics

| Metric | Count |
|--------|-------|
| Python source files | 35+ |
| Lines of code (pyshield_smr/) | ~8000 |
| Test files | 8+ |
| Test cases | 50+ |
| Theory documents | 7 |
| Guide documents | 4 |
| Worked examples | 5 |
| Data files | 8 |
| Docstring-documented functions | 500+ |
| Automated governance checks | 12 |

## What Makes This Portfolio-Grade?

✓ **Breadth**: Transport, shielding, UQ, optimization, HPC, governance—all in one framework  
✓ **Depth**: Each subsystem has theory docs, tests, worked examples, and code comments  
✓ **Rigor**: Constants match CODATA, cross sections match NIST, dose factors match ICRP  
✓ **Professionalism**: Multi-agent governance, regression testing, QA manifests, audit trail  
✓ **Reproducibility**: SHA-256 data hashing, schema versioning, YAML specs as code  
✓ **Clarity**: Physics explained alongside code; no black boxes  
✓ **Extensibility**: Designed for easy extension (new engines, materials, post-processors)  

**Why this matters for Rolls-Royce SMR role**: This demonstrates not just technical skill (can you code?) but **engineering judgment** (can you design systems that are safe, auditable, and reproducible?).

## Next Steps

### To Use as a Portfolio
1. Clone/download the project
2. Run `GETTING_STARTED.md` to verify installation
3. Study the 5 examples
4. Read the theory documents (especially 02_point_kernel.md)
5. Explore the code (start with pyshield_smr/shielding/point_kernel.py)
6. Run the test suite: `pytest tests/ -v`
7. Run the governance audit: `python tasks/audit_process.py --verbose`

### To Extend the Framework
1. Read AGENTS.md (understand specialist roles)
2. Read tasks/PROCESS_ARCHITECTURE.md (understand development process)
3. Make a small change (e.g., add a new material or nuclide)
4. Run `pytest` and `audit_process.py` to verify
5. Document the change in PHYSICS_CHANGELOG.md

### To Prepare for Interviews
1. Understand the point-kernel method (docs/theory/02_point_kernel.md)
2. Be able to explain Monte Carlo transport (docs/theory/03_monte_carlo.md)
3. Know ALARP principles (docs/theory/07_alarp.md)
4. Be prepared to discuss design trade-offs (e.g., why two-term vs. exponential buildup?)
5. Understand quality practices (docs/guides/QA.md)

---

**PyShield-SMR v0.1.0** — A comprehensive, production-minded portfolio project demonstrating mastery of radiation physics, nuclear engineering, and software engineering practices.

**Ready to download, review, run, and deploy.**
