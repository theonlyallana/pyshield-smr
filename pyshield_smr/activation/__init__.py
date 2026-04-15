"""Activation, Bateman decay-chain solution, and simplified burn-up."""

from .burnup import simple_burnup_buildup

__all__ = ["simple_burnup_buildup"]

# scipy-dependent Bateman solver — optional at import time.
try:
    from .bateman import decay_inventory, decay_matrix
    __all__ += ["decay_inventory", "decay_matrix"]
except ImportError:  # scipy not available
    pass
