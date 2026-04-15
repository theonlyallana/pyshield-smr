"""PyShield-SMR test suite.

## Testing Strategy

The test suite is organized into two layers:

### Unit Tests (tests/unit/)
Fast, isolated tests of individual components:
  - Physics correctness (constants, interpolation, dose conversion)
  - Transport behavior (geometry, tally variance, Klein-Nishina sampling)
  - Data structures (validation, serialization)

Each unit test is pinned to a specific tolerance (e.g., mass attenuation
interpolation within 0.5% of reference). These tolerances are documented
in the test with physical justification.

### Integration Tests (tests/integration/)
End-to-end workflows that exercise multiple components:
  - Full point-kernel analysis (source → geometry → dose rate)
  - Monte Carlo vs point-kernel agreement on simple cases
  - Uncertainty quantification convergence
  - ALARP optimization convergence

Integration tests include regression values (stored in
tests/integration/regression_values.yaml) that codify expected
results. If a result diverges from regression by > tolerance,
the test flags it as a potential physics regression.

## Running Tests

    # All tests
    pytest

    # Unit only
    pytest tests/unit/ -v

    # Integration only
    pytest tests/integration/ -v

    # With coverage
    pytest --cov=pyshield_smr tests/

## Test Data

Small test data files (synthetic spectra, toy geometries) are checked into
tests/data/. Large nuclear data (cross sections, decay chains) are vendored
in data/ at the repo root and reused across unit and integration tests.
"""
