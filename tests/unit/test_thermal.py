"""Tests del modelo termico de primer orden."""

from __future__ import annotations

import numpy as np
import pytest

from pid_dynamic_systems.models.thermal import ThermalSystem


def test_transfer_function_shape() -> None:
    """FT debe ser R / (R*C*s + 1)."""
    s = ThermalSystem(R=0.1, C=1000.0)
    num, den = s.transfer_function()
    assert np.allclose(num, [0.1])
    assert np.allclose(den, [100.0, 1.0])


def test_dc_gain_matches_R() -> None:
    """Ganancia DC es R [K/W]."""
    s = ThermalSystem(R=0.1)
    assert s.dc_gain() == pytest.approx(0.1)


def test_tau() -> None:
    """Constante de tiempo tau = R*C."""
    s = ThermalSystem(R=0.1, C=1000.0)
    assert s.tau == pytest.approx(100.0)


def test_derivatives_at_equilibrium_is_zero() -> None:
    """En equilibrio termico, dT/dt = 0."""
    s = ThermalSystem(R=0.1, C=1000.0, T_amb_ref=293.15)
    Q_in = 100.0
    T_eq = s.steady_state_from_Q_in(Q_in)
    dx = s.derivatives(0.0, np.array([T_eq]), np.array([Q_in, 293.15]))
    assert dx[0] == pytest.approx(0.0, abs=1e-10)


def test_derivatives_positive_when_cold() -> None:
    """Si T < T_eq con Q_in aplicado, dT/dt > 0 (calienta)."""
    s = ThermalSystem(R=0.1, C=1000.0)
    dx = s.derivatives(0.0, np.array([293.15]), np.array([100.0, 293.15]))
    assert dx[0] > 0.0


def test_steady_state_from_Q_in() -> None:
    """T_eq = T_amb + R*Q_in."""
    s = ThermalSystem(R=0.1, T_amb_ref=293.15)
    assert s.steady_state_from_Q_in(100.0) == pytest.approx(303.15)
