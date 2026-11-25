"""Tests de analisis de estabilidad."""

from __future__ import annotations

import numpy as np
import pytest

from pid_dynamic_systems.analysis.stability import (
    closed_loop_poles, damping_ratio, is_stable, natural_frequency,
    pid_transfer_function,
)
from pid_dynamic_systems.controllers.pid import PIDController
from pid_dynamic_systems.models.dc_motor import DCMotor
from pid_dynamic_systems.models.thermal import ThermalSystem


def test_pid_tf_p_only() -> None:
    """P puro: C(s) = Kp (grado 0 / grado 0)."""
    num, den = pid_transfer_function(PIDController(Kp=2.0, Ki=0.0, Kd=0.0))
    assert np.allclose(num, [2.0])
    assert np.allclose(den, [1.0])


def test_pid_tf_full() -> None:
    """PID: C(s) = (Kd*s^2 + Kp*s + Ki)/s."""
    num, den = pid_transfer_function(PIDController(Kp=1.0, Ki=2.0, Kd=0.5))
    assert np.allclose(num, [0.5, 1.0, 2.0])
    assert np.allclose(den, [1.0, 0.0])


def test_is_stable_true() -> None:
    """Polos con Re<0 son estables."""
    assert is_stable(np.array([complex(-1, 1), complex(-1, -1)]))


def test_is_stable_false() -> None:
    """Un polo con Re>0 hace inestable al lazo."""
    assert not is_stable(np.array([complex(0.1, 1), complex(-2, 0)]))


def test_damping_and_freq() -> None:
    """Polo -1+j: |p|=sqrt(2), zeta=1/sqrt(2)."""
    p = complex(-1, 1)
    assert natural_frequency(p) == pytest.approx(np.sqrt(2), rel=1e-6)
    assert damping_ratio(p) == pytest.approx(1.0 / np.sqrt(2), rel=1e-6)


def test_dc_motor_pi_closed_loop_stable() -> None:
    """DC motor + PI: 3 polos, todos estables."""
    m = DCMotor()
    ctrl = PIDController(Kp=1.0, Ki=1.0, Kd=0.0)
    poles = closed_loop_poles(m, ctrl)
    assert len(poles) == 3
    assert is_stable(poles)


def test_thermal_pi_closed_loop_stable() -> None:
    """Thermal + PI: 2 polos, todos estables."""
    m = ThermalSystem()
    ctrl = PIDController(Kp=1.0, Ki=1.0, Kd=0.0)
    poles = closed_loop_poles(m, ctrl)
    assert len(poles) == 2
    assert is_stable(poles)
