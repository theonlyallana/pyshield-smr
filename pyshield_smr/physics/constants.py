"""Physical constants.

Values follow CODATA 2018 where relevant. Energies are stored in MeV, lengths in
metres, masses in kilograms. Constants that cross unit systems are exposed twice,
with the unit spelled out in the identifier.
"""

from __future__ import annotations

AVOGADRO: float = 6.022_140_76e23  # mol^-1
ELEMENTARY_CHARGE_C: float = 1.602_176_634e-19  # Coulomb
ELECTRON_MASS_KG: float = 9.109_383_7015e-31
ELECTRON_MASS_MEV: float = 0.510_998_950_00  # MeV / c^2
SPEED_OF_LIGHT_MPS: float = 2.997_924_58e8  # exact, m/s

# Convenience unit conversions used throughout
MEV_TO_J: float = 1.602_176_634e-13
J_TO_MEV: float = 1.0 / MEV_TO_J
BARN_TO_CM2: float = 1.0e-24
CM2_TO_BARN: float = 1.0e24
GRAM_PER_KG: float = 1.0e3

# Classical electron radius, useful for Klein–Nishina scattering
CLASSICAL_ELECTRON_RADIUS_CM: float = 2.817_940_3262e-13
