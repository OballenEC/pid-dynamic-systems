"""Pruebas unitarias del modelo de motor DC."""

import numpy as np
import pytest
from control import tf

from pid_dynamic_systems.models.dc_motor import DCMotor


def test_steady_state_equilibrium_has_zero_derivative():
    motor = DCMotor()
    v, tau_L = 10.0, 0.0
    i_ss, omega_ss = motor.steady_state_from_voltage(v, tau_L)
    dx = motor.derivatives(0.0, [i_ss, omega_ss], [v, tau_L])
    assert np.allclose(dx, 0.0, atol=1e-10)


def test_dc_gain_matches_steady_state():
    """La ganancia DC de la FT debe coincidir con omega_ss / v en equilibrio."""
    motor = DCMotor()
    v = 10.0
    _, omega_ss = motor.steady_state_from_voltage(v, tau_L=0.0)
    assert np.isclose(motor.dc_gain() * v, omega_ss, rtol=1e-10)


def test_transfer_function_is_stable():
    """Los polos deben tener parte real negativa (sistema estable)."""
    motor = DCMotor()
    num, den = motor.transfer_function()
    sys = tf(num, den)
    poles = sys.poles()
    assert np.all(np.real(poles) < 0), f"Polos inestables: {poles}"


def test_transfer_function_dc_gain_matches():
    """La ganancia DC de python-control coincide con dc_gain()."""
    motor = DCMotor()
    num, den = motor.transfer_function()
    sys = tf(num, den)
    dc_gain_ctrl = sys.dcgain()
    assert np.isclose(dc_gain_ctrl, motor.dc_gain(), rtol=1e-10)
