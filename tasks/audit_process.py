"""PyShield-SMR governance audit.

Executable source of compliance truth for the project. If a rule is not
checked by this script (or by a test), it is not enforced.

Usage:
    python tasks/audit_process.py           # fail silently, set exit code
    python tasks/audit_process.py --verbose # print every check

Exit codes:
    0 — all required checks passed
    1 — at least one required check failed
    2 — audit itself could not run (missing file it cannot create)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class AuditReport:
    checks: List[CheckResult] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(CheckResult(name, ok, detail))

    @property
    def passed(self) -> bool:
        return all(c.ok for c in self.checks)


# --------------------------------------------------------------------------- #
# Individual checks                                                            #
# --------------------------------------------------------------------------- #

REQUIRED_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "RUNBOOK.md",
    "README.md",
    "pyproject.toml",
    "LICENSE",
    "tasks/PROCESS_ARCHITECTURE.md",
    "tasks/process_state.md",
    "tasks/todo.md",
    "tasks/lessons.md",
    "tasks/playbook.md",
    "tasks/logbook.md",
    "tasks/agents/registry.md",
    "tasks/memory/MEMORY.md",
    "tasks/memory/user.md",
    "tasks/memory/feedback.md",
    "tasks/memory/project.md",
    "tasks/memory/reference.md",
    "tasks/memory/source_index.md",
    "docs/theory/01_transport_theory.md",
    "docs/theory/02_point_kernel.md",
    "docs/theory/03_monte_carlo.md",
    "docs/theory/04_source_terms.md",
    "docs/theory/05_activation_and_decay.md",
    "docs/theory/06_uq.md",
    "docs/theory/07_alarp.md",
    "docs/theory/PHYSICS_CHANGELOG.md",
    "docs/guides/QA.md",
    "docs/guides/HPC.md",
    "docs/guides/GETTING_STARTED.md",
    "docs/guides/MCNP_INTEROP.md",
]


def check_required_files(report: AuditReport) -> None:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).exists()]
    report.add(
        "required-files-present",
        ok=not missing,
        detail="missing: " + ", ".join(missing) if missing else "all present",
    )


def check_architecture_links(report: AuditReport) -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    runbook = (ROOT / "RUNBOOK.md").read_text(encoding="utf-8")
    ok_agents = "PROCESS_ARCHITECTURE" in agents or "tasks/PROCESS_ARCHITECTURE" in agents
    ok_runbook = "audit_process" in runbook or "PROCESS_ARCHITECTURE" in runbook
    report.add(
        "architecture-links",
        ok=ok_agents and ok_runbook,
        detail=(
            f"AGENTS.md→PROCESS_ARCHITECTURE={ok_agents}, "
            f"RUNBOOK.md→audit/arch={ok_runbook}"
        ),
    )


def check_specialist_routing(report: AuditReport) -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    has_auto = "Automatic Specialist" in agents
    has_handoff = "Decentralised Handoff" in agents or "Decentralized Handoff" in agents
    report.add(
        "specialist-routing-doctrine",
        ok=has_auto and has_handoff,
        detail=f"automatic={has_auto}, handoff={has_handoff}",
    )


def check_registry_agents(report: AuditReport) -> None:
    registry_path = ROOT / "tasks" / "agents" / "registry.md"
    if not registry_path.exists():
        report.add("agent-registry", False, "registry.md missing")
        return

    registry = registry_path.read_text(encoding="utf-8")
    active_names = re.findall(r"\|\s*([a-z][a-z0-9-]+)\s*\|\s*Active", registry)
    missing_files: list[str] = []
    for name in active_names:
        for fname in ("config.md", "playbook.md", "logbook.md"):
            path = ROOT / "tasks" / "agents" / name / fname
            if not path.exists():
                missing_files.append(f"{name}/{fname}")
    report.add(
        "agent-files-present",
        ok=not missing_files,
        detail=(
            f"active={active_names}; missing={missing_files}"
            if missing_files
            else f"active={active_names}; all files present"
        ),
    )


def check_memory_freshness(report: AuditReport, max_age_days: int = 180) -> None:
    memory_dir = ROOT / "tasks" / "memory"
    stale: list[str] = []
    for path in memory_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        m = re.search(r"last_updated:\s*(\d{4}-\d{2}-\d{2})", text)
        if not m:
            stale.append(f"{path.name}(no-date)")
            continue
        date = _dt.date.fromisoformat(m.group(1))
        if (_dt.date.today() - date).days > max_age_days:
            stale.append(f"{path.name}({m.group(1)})")
    report.add(
        "memory-freshness",
        ok=not stale,
        detail=(
            f"stale: {stale}"
            if stale
            else f"all memory files refreshed within {max_age_days} days"
        ),
    )


def check_process_state(report: AuditReport) -> None:
    path = ROOT / "tasks" / "process_state.md"
    text = path.read_text(encoding="utf-8")
    next_review = re.search(r"next_review_due:\s*(\d{4}-\d{2}-\d{2})", text)
    if not next_review:
        report.add("process-state-review-date", False, "no next_review_due")
        return
    due = _dt.date.fromisoformat(next_review.group(1))
    overdue = due < _dt.date.today()
    report.add(
        "process-state-review-date",
        ok=not overdue,
        detail=f"next_review_due={due.isoformat()} overdue={overdue}",
    )


def check_todo_review_section(report: AuditReport) -> None:
    text = (ROOT / "tasks" / "todo.md").read_text(encoding="utf-8")
    has_review = "### Review" in text or "## Review" in text
    has_verification = "### Verification" in text or "## Verification" in text
    report.add(
        "todo-review-present",
        ok=has_review and has_verification,
        detail=f"review_heading={has_review}, verification_heading={has_verification}",
    )


def check_physics_changelog(report: AuditReport) -> None:
    cl = ROOT / "docs" / "theory" / "PHYSICS_CHANGELOG.md"
    ok = cl.exists() and len(cl.read_text(encoding="utf-8").strip()) > 0
    report.add(
        "physics-changelog-nonempty",
        ok=ok,
        detail=str(cl),
    )


def check_yaml_schema_version(report: AuditReport) -> None:
    schema_py = ROOT / "pyshield_smr" / "workflow" / "schema.py"
    if not schema_py.exists():
        report.add("yaml-schema-version", False, "schema.py missing")
        return
    text = schema_py.read_text(encoding="utf-8")
    m = re.search(r"SCHEMA_VERSION\s*=\s*['\"]([\w.-]+)['\"]", text)
    report.add(
        "yaml-schema-version",
        ok=bool(m),
        detail=f"SCHEMA_VERSION={m.group(1) if m else '<not found>'}",
    )


def check_data_directory(report: AuditReport) -> None:
    data_dir = ROOT / "data"
    has_any = any(data_dir.rglob("*.json")) or any(data_dir.rglob("*.yaml"))
    report.add("data-directory-populated", has_any, f"dir={data_dir}")


def check_tests_discoverable(report: AuditReport) -> None:
    tests_dir = ROOT / "tests"
    ok = tests_dir.exists() and any(tests_dir.rglob("test_*.py"))
    report.add("tests-discoverable", ok, f"tests_dir={tests_dir}")


def check_qa_hash_stability(report: AuditReport) -> None:
    """Smoke check: ensure the hashing helper is present and importable path exists."""
    quality = ROOT / "pyshield_smr" / "workflow" / "quality.py"
    text = quality.read_text(encoding="utf-8") if quality.exists() else ""
    report.add(
        "qa-manifest-hashing",
        ok="sha256" in text and "build_qa_manifest" in text,
        detail=str(quality),
    )


def check_examples_consistency(report: AuditReport) -> None:
    """Every subdirectory under examples/ must contain a config.yaml.

    Catches the class of bug where an empty duplicate folder is created
    (e.g. by renaming/spelling drift) and a RUNBOOK command silently points
    at a directory with no spec.
    """
    examples_dir = ROOT / "examples"
    if not examples_dir.is_dir():
        report.add("examples-consistency", False, "examples/ directory missing")
        return

    bad: list[str] = []
    for subdir in sorted(examples_dir.iterdir()):
        if not subdir.is_dir():
            continue
        if not (subdir / "config.yaml").exists():
            bad.append(subdir.name)

    report.add(
        "examples-consistency",
        ok=not bad,
        detail=(
            "directories missing config.yaml: " + ", ".join(bad)
            if bad
            else f"all {sum(1 for d in examples_dir.iterdir() if d.is_dir())} example"
            f" directories have config.yaml"
        ),
    )


# --------------------------------------------------------------------------- #
# Entry point                                                                  #
# --------------------------------------------------------------------------- #

CHECKS: List[Callable[[AuditReport], None]] = [
    check_required_files,
    check_architecture_links,
    check_specialist_routing,
    check_registry_agents,
    check_memory_freshness,
    check_process_state,
    check_todo_review_section,
    check_physics_changelog,
    check_yaml_schema_version,
    check_data_directory,
    check_tests_discoverable,
    check_qa_hash_stability,
    check_examples_consistency,
]


def run(verbose: bool = False) -> int:
    report = AuditReport()
    for check in CHECKS:
        try:
            check(report)
        except Exception as exc:  # audit must never crash silently
            report.add(check.__name__, ok=False, detail=f"exception: {exc!r}")

    if verbose:
        for r in report.checks:
            flag = "✓" if r.ok else "✗"
            print(f"  {flag} {r.name}: {r.detail}")

    if report.passed:
        print(f"audit: PASS ({len(report.checks)} checks)")
        return 0

    fails = [r for r in report.checks if not r.ok]
    print(f"audit: FAIL ({len(fails)}/{len(report.checks)} checks failed)")
    if not verbose:
        for r in fails:
            print(f"  ✗ {r.name}: {r.detail}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="PyShield-SMR governance audit")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()
    return run(verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
