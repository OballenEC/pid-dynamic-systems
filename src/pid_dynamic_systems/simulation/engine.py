"""Motor de simulacion en lazo cerrado con ZOH del PID.

En cada intervalo [t_k, t_k+1] el controlador entrega u (constante
por zero-order hold) y solve_ivp integra el modelo con esa u fija.
Esto respeta el caracter discreto del PID y su anti-windup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp


@dataclass
class SimulationResult:
    """Resultado de una simulacion en lazo cerrado."""

    t: np.ndarray
    y: np.ndarray
    u: np.ndarray
    x: np.ndarray
    error: np.ndarray
    ref: float
    dt: float
    t_final: float
    saturated_steps: int

def simulate(
    model,
    controller,
    ref: float,
    t_final: float,
    dt: float = 0.001,
    x0: np.ndarray | None = None,
    disturbance: Callable[[float], float] | None = None,
) -> SimulationResult:
    """Simula el modelo en lazo cerrado bajo el PID durante [0, t_final]."""
    n = len(model.state_names)
    x = np.zeros(n) if x0 is None else np.asarray(x0, dtype=float)
    controller.reset()

    n_steps = int(round(t_final / dt)) + 1
    t_arr = np.linspace(0.0, t_final, n_steps)
    x_arr = np.zeros((n_steps, n))
    y_arr = np.zeros(n_steps)
    u_arr = np.zeros(n_steps)
    e_arr = np.zeros(n_steps)

    x_arr[0] = x
    y_arr[0] = x[model.output_index]
    saturated = 0

    for k in range(n_steps - 1):
        e = ref - y_arr[k]
        u = controller.step(e, dt)
        if u <= controller.u_min or u >= controller.u_max:
            saturated += 1
        u_arr[k] = u
        e_arr[k] = e

        def rhs(t: float, x_: np.ndarray, _u: float = u) -> np.ndarray:
            d = 0.0 if disturbance is None else disturbance(t)
            return model.derivatives(t, x_, np.array([_u, d]))

        sol = solve_ivp(
            rhs, (t_arr[k], t_arr[k + 1]), x,
            method="RK45", rtol=1e-8, atol=1e-10,
        )
        x = sol.y[:, -1]
        x_arr[k + 1] = x
        y_arr[k + 1] = x[model.output_index]

    e_arr[-1] = ref - y_arr[-1]
    if n_steps > 1:
        u_arr[-1] = u_arr[-2]

    return SimulationResult(
        t=t_arr, y=y_arr, u=u_arr, x=x_arr, error=e_arr,
        ref=ref, dt=dt, t_final=t_final, saturated_steps=saturated,
    )
