"""Tests del motor de simulacion en lazo cerrado."""

from __future__ import annotations

import numpy as np
import pytest

from pid_dynamic_systems.controllers.pid import PIDController
from pid_dynamic_systems.models.dc_motor import DCMotor
from pid_dynamic_systems.models.mass_spring_damper import MassSpringDamper
from pid_dynamic_systems.simulation.engine import simulate


def test_result_shapes() -> None:
    """Arrays del resultado tienen n_steps elementos."""
    r = simulate(DCMotor(), PIDController(Kp=1.0), ref=1.0, t_final=0.1, dt=0.01)
    n = int(round(0.1 / 0.01)) + 1
    assert r.t.shape == (n,)
    assert r.y.shape == (n,)
    assert r.u.shape == (n,)
    assert r.x.shape == (n, 2)
    assert r.error.shape == (n,)


def test_zero_gains_give_zero_control() -> None:
    """Kp=Ki=Kd=0 -> u=0 en todos los pasos."""
    r = simulate(DCMotor(), PIDController(Kp=0.0, Ki=0.0, Kd=0.0),
                 ref=10.0, t_final=0.5, dt=0.01)
    assert np.allclose(r.u, 0.0)


def test_p_control_reaches_analytic_steady_state() -> None:
    """Con P puro, converge al SS analitico y_ss = G0*Kp*ref/(1+G0*Kp)."""
    m = DCMotor()
    Kp = 1.0
    ref = 10.0
    r = simulate(m, PIDController(Kp=Kp, Ki=0.0, Kd=0.0),
                 ref=ref, t_final=5.0, dt=0.01)
    G0 = m.dc_gain()
    y_ss_analytic = G0 * Kp * ref / (1.0 + G0 * Kp)
    assert abs(r.y[-1] - y_ss_analytic) < 0.05


def test_dc_motor_closed_loop_reaches_setpoint() -> None:
    """PI sobre DC motor converge al setpoint (error < 5%)."""
    r = simulate(DCMotor(), PIDController(Kp=1.0, Ki=1.0, Kd=0.0),
                 ref=10.0, t_final=15.0, dt=0.01)
    assert abs(r.y[-1] - 10.0) < 0.5


def test_saturation_counted_with_tight_bounds() -> None:
    """Con u_max bajo, hay saturacion en al menos un paso."""
    ctrl = PIDController(Kp=10.0, Ki=0.0, Kd=0.0, u_min=-1.0, u_max=1.0)
    r = simulate(DCMotor(), ctrl, ref=10.0, t_final=0.2, dt=0.01)
    assert r.saturated_steps > 0


def test_disturbance_affects_output() -> None:
    """Una perturbacion escalon desvia la salida respecto al caso sin perturbacion."""
    m = MassSpringDamper()
    ctrl = PIDController(Kp=10.0, Ki=0.0, Kd=0.0)
    r0 = simulate(m, ctrl, ref=0.5, t_final=1.0, dt=0.01)
    ctrl2 = PIDController(Kp=10.0, Ki=0.0, Kd=0.0)
    r1 = simulate(m, ctrl2, ref=0.5, t_final=1.0, dt=0.01,
                  disturbance=lambda t: 5.0 if t > 0.3 else 0.0)
    assert abs(r1.y[-1] - r0.y[-1]) > 0.01


