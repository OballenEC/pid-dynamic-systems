"""Tests del controlador PID discreto."""

from __future__ import annotations

import pytest

from pid_dynamic_systems.controllers.pid import PIDController


def test_p_only_output() -> None:
    """Kp puro: u = Kp*e (primer paso, sin saturacion)."""
    ctrl = PIDController(Kp=2.0, Ki=0.0, Kd=0.0)
    assert ctrl.step(1.0) == pytest.approx(2.0)


def test_i_only_increments() -> None:
    """Ki puro: primer paso aplica Ki*e*dt."""
    ctrl = PIDController(Kp=0.0, Ki=1.0, Kd=0.0, dt=0.1)
    assert ctrl.step(1.0) == pytest.approx(0.1)


def test_first_step_no_derivative_spike() -> None:
    """Primer paso: D=0 aunque el error sea grande (evita spike)."""
    ctrl = PIDController(Kp=0.0, Ki=0.0, Kd=100.0, dt=0.01)
    assert ctrl.step(10.0) == pytest.approx(0.0, abs=1e-9)


def test_derivative_kicks_second_step() -> None:
    """Segundo paso con cambio de error: contribucion de D positiva."""
    ctrl = PIDController(Kp=0.0, Ki=0.0, Kd=1.0, tau_f=0.001, dt=0.01)
    ctrl.step(0.0)
    out = ctrl.step(0.1)
    assert out > 0.0


def test_saturation_clips_output() -> None:
    """La salida se limita a [u_min, u_max]."""
    ctrl = PIDController(Kp=10.0, Ki=0.0, Kd=0.0, u_min=0.0, u_max=1.0)
    assert ctrl.step(1.0) == pytest.approx(1.0)


def test_anti_windup_bounds_integral() -> None:
    """Con saturacion, la integral no crece sin control."""
    ctrl = PIDController(Kp=0.0, Ki=10.0, Kd=0.0, dt=0.1, u_min=-1.0, u_max=1.0)
    for _ in range(50):
        ctrl.step(1.0)
    assert ctrl._integral <= 1.5


def test_reset_clears_state() -> None:
    """reset() deja el controlador como nuevo."""
    ctrl = PIDController(Kp=1.0, Ki=1.0, Kd=1.0, dt=0.1)
    ctrl.step(1.0)
    ctrl.step(1.0)
    ctrl.reset()
    out = ctrl.step(1.0)
    assert out == pytest.approx(1.1)
