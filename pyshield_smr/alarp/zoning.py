"""Radiological zoning helpers.

The UK approach classifies areas by expected dose rate and required control.
Thresholds below follow the spirit of IRR17 / IRR2017, but the numerical values
here are pedagogical defaults — always consult the site safety case for the
values in force.

Zones used:

    * uncontrolled      (<= 2.5 uSv/h)
    * supervised        (>  2.5 uSv/h and <= 7.5 uSv/h)
    * controlled        (>  7.5 uSv/h and <= 1 mSv/h)
    * high-dose-rate    (>  1 mSv/h)

The numbers above are illustrative; a real project embeds the site's own
defined thresholds and reviews them against IRR17 regulation 17 duties.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneAssignment:
    """Zone at a location + basis numbers."""

    zone: str
    dose_rate_sv_per_h: float
    thresholds_sv_per_h: dict[str, float]


DEFAULT_THRESHOLDS_SV_PER_H: dict[str, float] = {
    "uncontrolled": 2.5e-6,
    "supervised": 7.5e-6,
    "controlled": 1.0e-3,
}


def assign_zone(
    dose_rate_sv_per_h: float,
    thresholds: dict[str, float] | None = None,
) -> ZoneAssignment:
    """Return the zone that a given dose rate falls into.

    Parameters
    ----------
    dose_rate_sv_per_h
        Maximum expected dose rate at the location, ``Sv/h``.
    thresholds
        Optional override of the default thresholds.

    Returns
    -------
    ZoneAssignment
    """
    t = thresholds or DEFAULT_THRESHOLDS_SV_PER_H
    if dose_rate_sv_per_h <= t["uncontrolled"]:
        zone = "uncontrolled"
    elif dose_rate_sv_per_h <= t["supervised"]:
        zone = "supervised"
    elif dose_rate_sv_per_h <= t["controlled"]:
        zone = "controlled"
    else:
        zone = "high-dose-rate"
    return ZoneAssignment(
        zone=zone,
        dose_rate_sv_per_h=float(dose_rate_sv_per_h),
        thresholds_sv_per_h=dict(t),
    )
