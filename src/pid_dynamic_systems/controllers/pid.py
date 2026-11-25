"""Controlador PID discreto con derivada filtrada y anti-windup.

Ecuacion: u[k] = Kp*e[k] + I[k] + Kd*d_f[k]

Derivada filtrada (paso-bajos primer orden):
    d_raw[k] = (e[k] - e[k-1]) / dt
    d_f[k]   = alpha * d_raw[k] + (1-alpha) * d_f[k-1]
    alpha    = dt / (tau_f + dt)

Anti-windup: la integral solo se acumula cuando la salida NO
esta saturada (clamping condicional).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class PIDController:
    """Controlador PID discreto con derivada filtrada y anti-windup."""

    Kp: float = 1.0
    Ki: float = 0.0
    Kd: float = 0.0
    tau_f: float = 0.01
    u_min: float = -np.inf
    u_max: float = np.inf
    dt: float = 0.001

    _integral: float = field(default=0.0, init=False, repr=False)
    _e_prev: float = field(default=0.0, init=False, repr=False)
    _d_f: float = field(default=0.0, init=False, repr=False)
    _first: bool = field(default=True, init=False, repr=False)

    def reset(self) -> None:
        """Reinicia el estado interno (integral, error previo, derivada)."""
        self._integral = 0.0
        self._e_prev = 0.0
        self._d_f = 0.0
        self._first = True

    def step(self, error: float, dt: float | None = None) -> float:
        """Un paso del PID. Retorna la salida saturada en [u_min, u_max]."""
        if dt is None:
            dt = self.dt

        # Derivada (filtrada). En el primer paso no hay e_prev.
        if self._first:
            d_raw = 0.0
        else:
            d_raw = (error - self._e_prev) / dt
        alpha = dt / (self.tau_f + dt)
        self._d_f = alpha * d_raw + (1.0 - alpha) * self._d_f

        # Integral provisional (puede ser rechazada por anti-windup)
        I_new = self._integral + self.Ki * error * dt

        # Salida raw y saturada
        u_raw = self.Kp * error + I_new + self.Kd * self._d_f
        u_sat = float(np.clip(u_raw, self.u_min, self.u_max))

        # Anti-windup (clamping condicional)
        if u_raw == u_sat:
            self._integral = I_new

        # Actualizar estado para el siguiente paso
        self._e_prev = error
        self._first = False

        return u_sat
