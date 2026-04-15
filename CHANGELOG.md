# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-14

### Added
- Initial scaffold: physics core, Monte Carlo and point-kernel transport engines, shielding post-processors (DPA, gamma heating, detector response), source-term and activation / Bateman decay, UQ (LHS + Morris), ALARP optimiser, YAML workflow engine with QA manifest and report generator, CLI, HPC executor.
- Governance layer: AGENTS.md, RUNBOOK.md, PROCESS_ARCHITECTURE.md, audit_process.py, agent registry with five specialists, memory files.
- Documentation: README, ARCHITECTURE, seven theory docs, QA, HPC, MCNP interop, GETTING_STARTED.
- CI (GitHub Actions), pre-commit, pyproject packaging.
- Five worked examples, unit + integration tests.
