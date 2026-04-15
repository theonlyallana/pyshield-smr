"""Unit tests for 1-D slab-stack geometry.

Invariants:
    - Boundaries are cumulative sums of thicknesses, starting at 0.
    - material_at(x) returns correct material or None outside stack.
    - traverse() segments cover the full slab exactly, no gaps or overlaps.
    - SlabStack validates its inputs on construction.
"""

from __future__ import annotations

import pytest
import numpy as np

from pyshield_smr.transport.geometry import SlabStack, Sphere


class TestSlabStackConstruction:
    """SlabStack must validate its inputs."""

    def test_single_slab(self) -> None:
        s = SlabStack(["lead"], [0.05])
        assert s.total_thickness_m == pytest.approx(0.05)

    def test_multi_slab(self) -> None:
        s = SlabStack(["lead", "concrete_ordinary"], [0.05, 0.50])
        assert s.total_thickness_m == pytest.approx(0.55)

    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            SlabStack(["lead", "water"], [0.05])

    def test_zero_thickness_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            SlabStack(["lead"], [0.0])

    def test_negative_thickness_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            SlabStack(["lead"], [-0.01])


class TestBoundaries:
    """boundaries_m must include 0 and all cumulative sums."""

    def test_single_slab_boundaries(self) -> None:
        s = SlabStack(["lead"], [0.05])
        np.testing.assert_allclose(s.boundaries_m, [0.0, 0.05])

    def test_two_slab_boundaries(self) -> None:
        s = SlabStack(["lead", "iron"], [0.05, 0.10])
        np.testing.assert_allclose(s.boundaries_m, [0.0, 0.05, 0.15])

    def test_boundaries_length(self) -> None:
        s = SlabStack(["a", "b", "c"], [0.1, 0.2, 0.3])
        assert len(s.boundaries_m) == 4  # N slabs → N+1 boundaries


class TestMaterialAt:
    """material_at() should return the correct material name at any depth."""

    def test_first_slab(self) -> None:
        s = SlabStack(["lead", "water"], [0.05, 0.10])
        assert s.material_at(0.025) == "lead"

    def test_second_slab(self) -> None:
        s = SlabStack(["lead", "water"], [0.05, 0.10])
        assert s.material_at(0.07) == "water"

    def test_at_left_edge(self) -> None:
        s = SlabStack(["lead"], [0.05])
        assert s.material_at(0.0) == "lead"

    def test_before_stack_returns_none(self) -> None:
        s = SlabStack(["lead"], [0.05])
        assert s.material_at(-0.01) is None

    def test_after_stack_returns_none(self) -> None:
        s = SlabStack(["lead"], [0.05])
        assert s.material_at(0.06) is None

    def test_at_exact_right_boundary_returns_none(self) -> None:
        s = SlabStack(["lead"], [0.05])
        assert s.material_at(0.05) is None


class TestTraverse:
    """traverse() must return correct (material, path_length) segments."""

    def test_single_slab_normal_incidence(self) -> None:
        """Normal incidence (mu=1.0): path length == slab thickness."""
        s = SlabStack(["lead"], [0.05])
        segs = s.traverse(0.0, mu=1.0)
        assert len(segs) == 1
        assert segs[0][0] == "lead"
        assert segs[0][1] == pytest.approx(0.05)

    def test_two_slab_normal_incidence(self) -> None:
        s = SlabStack(["lead", "water"], [0.05, 0.10])
        segs = s.traverse(0.0, mu=1.0)
        assert len(segs) == 2
        assert segs[0] == ("lead", pytest.approx(0.05))
        assert segs[1] == ("water", pytest.approx(0.10))

    def test_oblique_incidence_path_length(self) -> None:
        """At mu=0.5 (60° from normal), path length doubles."""
        s = SlabStack(["lead"], [0.05])
        segs = s.traverse(0.0, mu=0.5)
        assert segs[0][1] == pytest.approx(0.10, rel=1e-6)

    def test_total_path_length_conserved(self) -> None:
        """Sum of path lengths must equal total thickness / |mu|."""
        s = SlabStack(["lead", "iron", "water"], [0.05, 0.10, 0.20])
        mu = 0.8
        segs = s.traverse(0.0, mu=mu)
        total_path = sum(pl for _, pl in segs)
        expected = s.total_thickness_m / mu
        assert total_path == pytest.approx(expected, rel=1e-6)

    def test_grazing_raises(self) -> None:
        s = SlabStack(["lead"], [0.05])
        with pytest.raises(ValueError, match="grazing"):
            s.traverse(0.0, mu=0.0)

    def test_start_outside_stack_gives_empty(self) -> None:
        """Starting beyond the stack: no segments traversed."""
        s = SlabStack(["lead"], [0.05])
        segs = s.traverse(0.10, mu=1.0)  # past the slab
        assert segs == []


class TestSphere:
    """Sphere geometry: basic construction and validation."""

    def test_construction(self) -> None:
        sp = Sphere(material="lead", r_in_m=0.5, r_out_m=0.55)
        assert sp.thickness_m == pytest.approx(0.05)

    def test_r_in_ge_r_out_raises(self) -> None:
        with pytest.raises(ValueError):
            Sphere(material="lead", r_in_m=0.5, r_out_m=0.4)

    def test_r_in_eq_r_out_raises(self) -> None:
        with pytest.raises(ValueError):
            Sphere(material="lead", r_in_m=0.5, r_out_m=0.5)

    def test_negative_r_in_raises(self) -> None:
        with pytest.raises(ValueError):
            Sphere(material="lead", r_in_m=-0.1, r_out_m=0.5)
