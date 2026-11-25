"""Tests del modelo masa-resorte-amortiguador (segundo orden)."""

from __future__ import annotations

import numpy as np
import pytest

from pid_dynamic_systems.models.mass_spring_damper import MassSpringDamper


def test_transfer_function_shape() -> None:
    """FT debe ser 1 / (m*s^2 + c*s + k)."""
    s = MassSpringDamper(m=1.0, c=2.0, k=10.0)
    num, den = s.transfer_function()
    assert np.allclose(num, [1.0])
    assert np.allclose(den, [1.0, 2.0, 10.0])


def test_dc_gain_matches_1_over_k() -> None:
    """Ganancia DC es 1/k [m/N]."""
    s = MassSpringDamper(k=10.0)
    assert s.dc_gain() == pytest.approx(0.1)


def test_wn_and_zeta() -> None:
    """wn = sqrt(k/m); zeta = c / (2*sqrt(k*m))."""
    s = MassSpringDamper(m=1.0, c=2.0, k=10.0)
    assert s.wn == pytest.approx(np.sqrt(10.0))
    assert s.zeta == pytest.approx(1.0 / np.sqrt(10.0))


def test_derivatives_at_equilibrium_is_zero() -> None:
    """En equilibrio (x=x_eq, v=0), dx/dt = 0."""
    s = MassSpringDamper(m=1.0, c=2.0, k=10.0)
    F = 10.0
    x_eq = s.steady_state_from_F(F)
    dx = s.derivatives(0.0, np.array([x_eq, 0.0]), np.array([F, 0.0]))
    assert np.allclose(dx, [0.0, 0.0], atol=1e-10)


def test_derivatives_from_rest_accelerates() -> None:
    """Desde x=0, v=0 con F>0, aceleracion inicial positiva."""
    s = MassSpringDamper(m=1.0, c=2.0, k=10.0)
    dx = s.derivatives(0.0, np.array([0.0, 0.0]), np.array([10.0, 0.0]))
    assert dx[1] > 0.0


def test_steady_state_from_F() -> None:
    """x_eq = (F + F_dist) / k."""
    s = MassSpringDamper(k=10.0)
    assert s.steady_state_from_F(10.0) == pytest.approx(1.0)
    assert s.steady_state_from_F(10.0, F_dist=5.0) == pytest.approx(1.5)
