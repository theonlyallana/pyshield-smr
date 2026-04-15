"""Transport subpackage.

Contains geometry primitives, tallies, the analog + non-analog photon Monte Carlo
solver, variance-reduction helpers, and a thin MCNP-style input / output adapter
for pedagogical interoperability demonstrations.
"""

from .geometry import SlabStack, Sphere
from .monte_carlo import MonteCarloPhoton, MonteCarloResult, photon_transmission
from .tally import EnergyTally, SurfaceTally

__all__ = [
    "EnergyTally",
    "MonteCarloPhoton",
    "MonteCarloResult",
    "SlabStack",
    "Sphere",
    "SurfaceTally",
    "photon_transmission",
]
