"""Graficas de analisis de estabilidad (polos, step CL, Bode CL)."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from pid_dynamic_systems.analysis.stability import (
    closed_loop_poles, is_stable, pid_transfer_function,
)
from pid_dynamic_systems.simulation.engine import simulate


def poles_chart(poles: np.ndarray) -> go.Figure:
    """Scatter de polos en el plano complejo."""
    fig = go.Figure()
    if len(poles) > 0:
        real = [complex(p).real for p in poles]
        imag = [complex(p).imag for p in poles]
        fig.add_trace(go.Scatter(
            x=real, y=imag, mode="markers",
            marker=dict(size=14, color="crimson", symbol="x"),
            name="polos",
        ))
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title=f"Polos del lazo cerrado (estable: {is_stable(poles)})",
        xaxis_title="Re(s)",
        yaxis_title="Im(s)",
        height=400,
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig


def closed_loop_step_chart(model, controller, t_final: float = 10.0,
                           dt: float = 0.001) -> go.Figure:
    """Respuesta al escalon unitario del lazo cerrado (via simulate)."""
    result = simulate(model, controller, ref=1.0, t_final=t_final, dt=dt)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=result.t, y=result.y, mode="lines", name="y(t)"))
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray",
                  annotation_text="ref=1")
    fig.update_layout(
        title="Respuesta al escalon unitario (lazo cerrado)",
        xaxis_title="t [s]",
        yaxis_title="y",
        height=400,
    )
    return fig


def bode_chart(model, controller) -> go.Figure:
    """Diagrama de Bode de T(s)=G*C/(1+G*C) usando python-control."""
    import control as ct

    num_G, den_G = model.transfer_function()
    num_C, den_C = pid_transfer_function(controller)
    num_cl = np.convolve(num_G, num_C)
    den_cl = np.polyadd(np.convolve(den_G, den_C), num_cl)
    sys_cl = ct.tf(num_cl, den_cl)

    mag, phase, omega = ct.bode(sys_cl, plot=False)
    mag_db = 20 * np.log10(np.maximum(mag, 1e-12))
    phase_deg = np.degrees(phase)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=omega, y=mag_db, mode="lines", name="|T(jw)| [dB]",
        line=dict(color="steelblue"),
    ))
    fig.add_trace(go.Scatter(
        x=omega, y=phase_deg, mode="lines", name="fase(T(jw)) [deg]",
        yaxis="y2", line=dict(color="darkorange"),
    ))
    fig.update_layout(
        title="Bode del lazo cerrado",
        xaxis=dict(title="w [rad/s]", type="log"),
        yaxis=dict(title="Magnitud [dB]"),
        yaxis2=dict(title="Fase [deg]", overlaying="y", side="right"),
        height=400,
    )
    return fig