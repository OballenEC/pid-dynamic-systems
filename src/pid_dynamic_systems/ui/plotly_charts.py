"""Graficas Plotly para la UI."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go


def response_chart(t: np.ndarray, y: np.ndarray, ref: float) -> go.Figure:
    """Salida y(t) con linea de referencia."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=y, mode="lines", name="y(t)"))
    fig.add_hline(y=ref, line_dash="dash", line_color="gray",
                  annotation_text="ref")
    fig.update_layout(
        title="Respuesta temporal",
        xaxis_title="t [s]",
        yaxis_title="salida",
        height=350,
    )
    return fig


def control_chart(t: np.ndarray, u: np.ndarray) -> go.Figure:
    """Senal de control u(t)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=u, mode="lines", name="u(t)",
                             line=dict(color="orange")))
    fig.update_layout(
        title="Senal de control",
        xaxis_title="t [s]",
        yaxis_title="u",
        height=350,
    )
    return fig


def error_chart(t: np.ndarray, e: np.ndarray) -> go.Figure:
    """Error e(t) = ref - y(t)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=e, mode="lines", name="e(t)",
                             line=dict(color="red")))
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.update_layout(
        title="Error",
        xaxis_title="t [s]",
        yaxis_title="e",
        height=350,
    )
    return fig