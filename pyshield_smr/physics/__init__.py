"""Physics core: constants, units, materials, cross sections, buildup factors, dose coefficients."""

from .attenuation import (
    interpolate_mass_attenuation,
    linear_attenuation_coefficient,
)
from .buildup import taylor_buildup
from .constants import AVOGADRO, ELECTRON_MASS_MEV, MEV_TO_J
from .dose import flux_to_dose_h10
from .materials import Material, load_material_library
from .units import ureg

__all__ = [
    "AVOGADRO",
    "ELECTRON_MASS_MEV",
    "MEV_TO_J",
    "Material",
    "flux_to_dose_h10",
    "interpolate_mass_attenuation",
    "linear_attenuation_coefficient",
    "load_material_library",
    "taylor_buildup",
    "ureg",
]
