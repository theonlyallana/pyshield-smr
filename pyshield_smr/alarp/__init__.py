"""ALARP optimisation and radiological zoning."""

from .zoning import ZoneAssignment, assign_zone

__all__ = ["ZoneAssignment", "assign_zone"]

# scipy-dependent optimiser — optional at import time so the rest of the
# package works in environments where scipy is not installed (e.g., the
# sandbox used by CI linting or when only zoning is needed).
try:
    from .optimiser import OptimisationResult, optimise_shielding
    __all__ += ["OptimisationResult", "optimise_shielding"]
except ImportError:  # scipy not available
    pass
