"""Analisis de estabilidad de lazo cerrado con PID."""

from __future__ import annotations

import numpy as np


def pid_transfer_function(controller) -> tuple[np.ndarray, np.ndarray]:
    """FT ideal del PID continuo: C(s) = (Kd*s^2 + Kp*s + Ki)/s.

    Si Kd=Ki=0 (P puro), devuelve C(s) = Kp (FT propia).
    """
    Kp, Ki, Kd = float(controller.Kp), float(controller.Ki), float(controller.Kd)
    if Kd == 0 and Ki == 0:
        return np.array([Kp]), np.array([1.0])
    return np.array([Kd, Kp, Ki]), np.array([1.0, 0.0])


def closed_loop_poles(model, controller) -> np.ndarray:
    """Polos del lazo cerrado G(s)*C(s)/(1+G(s)*C(s)).

    Formula: raices de den_G*den_C + num_G*num_C.
    """
    num_G, den_G = model.transfer_function()
    num_C, den_C = pid_transfer_function(controller)
    num_cl = np.convolve(num_G, num_C)
    den_cl = np.polyadd(np.convolve(den_G, den_C), num_cl)
    den_cl = np.trim_zeros(den_cl, "f")
    if len(den_cl) <= 1:
        return np.array([])
    return np.roots(den_cl)


def is_stable(poles: np.ndarray) -> bool:
    """True si todos los polos tienen parte real < 0."""
    if len(poles) == 0:
        return True
    return bool(np.all(np.real(poles) < 0))


def damping_ratio(pole: complex) -> float:
    """zeta = -Re(p)/|p|. zeta=1 para polos reales negativos."""
    p = complex(pole)
    mag = abs(p)
    if mag == 0.0:
        return 0.0
    return -p.real / mag


def natural_frequency(pole: complex) -> float:
    """wn = |p| [rad/s]."""
    return float(abs(complex(pole)))
