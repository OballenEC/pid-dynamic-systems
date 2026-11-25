"""Modelo del motor electrico DC controlado por voltaje de armadura.

Ecuaciones diferenciales (tiempo continuo):

    L * di/dt     = v - R*i - Ke*omega
    J * domega/dt = Kt*i - B*omega - tau_L

Funcion de transferencia (omega(s)/V(s), con tau_L=0):

              Kt
    --------------------------------
    L*J*s^2 + (L*B + R*J)*s + (R*B + Kt*Ke)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class DCMotor:
    """Motor DC con excitacion independiente (armadura controlada)."""

    R: float = 1.0     # Resistencia de armadura [Ohm]
    L: float = 0.5     # Inductancia de armadura [H]
    J: float = 0.01    # Momento de inercia del rotor [kg*m^2]
    B: float = 0.1     # Coeficiente de friccion viscosa [N*m*s/rad]
    Kt: float = 0.1    # Constante de par [N*m/A]
    Ke: float = 0.1    # Constante de fuerza contraelectromotriz [V*s/rad]

    # ---- Metadatos ----
    @property
    def state_names(self) -> list[str]:
        return ["i", "omega"]

    @property
    def input_names(self) -> list[str]:
        return ["v", "tau_L"]

    @property
    def output_index(self) -> int:
        """Indice del estado que es la salida controlada (omega)."""
        return 1

    # ---- Dinamica ----
    def derivatives(self, t: float, x, u) -> np.ndarray:
        """Devuelve dx/dt = [di/dt, domega/dt].

        Parameters
        ----------
        t : float
            Tiempo actual (no usado, el sistema es invariante).
        x : array_like
            Estado [i, omega].
        u : array_like
            Entrada [v, tau_L].
        """
        i, omega = x
        v, tau_L = u
        di = (v - self.R * i - self.Ke * omega) / self.L
        domega = (self.Kt * i - self.B * omega - tau_L) / self.J
        return np.array([di, domega])

    # ---- Funcion de transferencia ----
    def transfer_function(self) -> tuple[list[float], list[float]]:
        """Coeficientes (num, den) de Omega(s)/V(s) en potencias descendentes."""
        num = [self.Kt]
        den = [
            self.L * self.J,
            self.L * self.B + self.R * self.J,
            self.R * self.B + self.Kt * self.Ke,
        ]
        return num, den

    def dc_gain(self) -> float:
        """Ganancia DC = Kt / (R*B + Kt*Ke)."""
        return self.Kt / (self.R * self.B + self.Kt * self.Ke)

    # ---- Equilibrio ----
    def steady_state_from_voltage(self, v: float, tau_L: float = 0.0) -> tuple[float, float]:
        """Estado estacionario (i_ss, omega_ss) para voltaje y par de carga dados."""
        omega_ss = (v - self.R * tau_L / self.Kt) / (self.R * self.B / self.Kt + self.Ke)
        i_ss = (self.B * omega_ss + tau_L) / self.Kt
        return i_ss, omega_ss
