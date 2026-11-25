"""Modelo del sistema termico de primer orden.

Dinamica:  C dT/dt = Q_in + (T_amb - T)/R

- Estado: T [K]
- Entrada control: Q_in [W]
- Perturbacion: T_amb [K]
- Salida: T (indice 0)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ThermalSystem:
    """Sistema termico de primer orden (una resistencia + una capacidad)."""

    R: float = 0.1
    C: float = 1000.0
    T_amb_ref: float = 293.15

    @property
    def state_names(self) -> list[str]:
        return ["T"]

    @property
    def input_names(self) -> list[str]:
        return ["Q_in", "T_amb"]

    @property
    def output_index(self) -> int:
        return 0

    @property
    def tau(self) -> float:
        return self.R * self.C

    def derivatives(self, t: float, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """dx/dt para x=[T] y u=[Q_in, T_amb]."""
        T = x[0]
        Q_in = u[0]
        T_amb = u[1]
        dT = (Q_in + (T_amb - T) / self.R) / self.C
        return np.array([dT])

    def transfer_function(self) -> tuple[np.ndarray, np.ndarray]:
        """FT Q_in -> T: R / (R*C*s + 1). Devuelve (num, den)."""
        num = np.array([self.R])
        den = np.array([self.R * self.C, 1.0])
        return num, den

    def dc_gain(self) -> float:
        """Ganancia DC [K/W] desde Q_in a T."""
        return self.R

    def steady_state_from_Q_in(
        self, Q_in: float, T_amb: float | None = None
    ) -> float:
        """Temperatura de equilibrio para Q_in dado y T_amb constante."""
        if T_amb is None:
            T_amb = self.T_amb_ref
        return T_amb + self.R * Q_in
