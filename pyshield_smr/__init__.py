"""PyShield-SMR — radiation physics and shielding analysis framework.

This package provides a pedagogically transparent but physically meaningful
implementation of the core analysis stack used by a Radiation Physics &
Shielding (RP&S) engineer on an SMR programme:

* source-term generation and Bateman decay-chain solution
* photon transport via point-kernel and analog / non-analog Monte Carlo
* dose-rate, DPA, gamma-heating, detector-response post-processing
* Latin-hypercube Monte Carlo uncertainty quantification
* ALARP optimisation of shielding thickness
* a YAML-driven workflow engine with an auditable QA manifest

It is an educational / portfolio project, **not** a licensed safety-case tool.
"""

from importlib.metadata import PackageNotFoundError, version

try:  # pragma: no cover - trivial
    __version__ = version("pyshield-smr")
except PackageNotFoundError:  # pragma: no cover - local editable install edge case
    __version__ = "0.1.0"

__all__ = ["__version__"]
