"""Modelo masa-resorte-amortiguador (segundo orden).

Dinamica:  m x'' + c x' + k x = F + F_dist

- Estado: [x, v] = [posicion, velocidad]
- Entrada control: F [N]
- Perturbacion: F_dist [N]
- Salida: x (indice 0)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MassSpringDamper:
    """Sistema masa-resorte-amortiguador de segundo orden."""

    m: float = 1.0
    c: float = 2.0
    k: float = 10.0

    @property
    def state_names(self) -> list[str]:
        return ["x", "v"]

    @property
    def input_names(self) -> list[str]:
        return ["F", "F_dist"]

    @property
    def output_index(self) -> int:
        return 0

    @property
    def wn(self) -> float:
        """Frecuencia natural [rad/s]."""
        return float(np.sqrt(self.k / self.m))

    @property
    def zeta(self) -> float:
        """Coeficiente de amortiguamiento (adimensional)."""
        return self.c / (2.0 * np.sqrt(self.k * self.m))

    def derivatives(self, t: float, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """dx/dt para x=[x, v] y u=[F, F_dist]."""
        pos, vel = x[0], x[1]
        F, F_dist = u[0], u[1]
        acc = (F + F_dist - self.c * vel - self.k * pos) / self.m
        return np.array([vel, acc])

    def transfer_function(self) -> tuple[np.ndarray, np.ndarray]:
        """FT F -> x: 1 / (m*s^2 + c*s + k). Devuelve (num, den)."""
        num = np.array([1.0])
        den = np.array([self.m, self.c, self.k])
        return num, den

    def dc_gain(self) -> float:
        """Ganancia DC [m/N] desde F a x."""
        return 1.0 / self.k

    def steady_state_from_F(
        self, F: float, F_dist: float = 0.0
    ) -> float:
        """Posicion de equilibrio para F y F_dist dados."""
        return (F + F_dist) / self.k
