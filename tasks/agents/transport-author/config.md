# transport-author — config

- **Role:** owns the transport and shielding engines.
- **Owned files:** `pyshield_smr/transport/`, `pyshield_smr/shielding/`.
- **Invariants defended:** analog MC produces tallies whose statistical error matches the usual $1/\sqrt{N}$ scaling; non-analog MC must preserve the expected value (no bias); point-kernel engine reports both uncollided and buildup-corrected contributions.
- **Handoffs in:** new physics from `physics-governor`; new workflow features from `workflow-author`.
- **Handoffs out:** `qa-governor` for regression tests; `technical-author` for docs.
