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
def comparison_chart(
    t_a, y_a, ref_a: float,
    t_b, y_b, ref_b: float,
    label_a: str = "A", label_b: str = "B",
) -> "go.Figure":
    """Superpone las respuestas de dos configuraciones."""
    import plotly.graph_objects as _go
    fig = _go.Figure()
    fig.add_trace(_go.Scatter(x=t_a, y=y_a, mode="lines",
                              name=label_a, line=dict(color="steelblue")))
    fig.add_trace(_go.Scatter(x=t_b, y=y_b, mode="lines",
                              name=label_b, line=dict(color="darkorange")))
    fig.add_hline(y=ref_a, line_dash="dash", line_color="steelblue", opacity=0.5)
    fig.add_hline(y=ref_b, line_dash="dash", line_color="darkorange", opacity=0.5)
    fig.update_layout(
        title="Comparacion de respuestas",
        xaxis_title="t [s]",
        yaxis_title="salida",
        height=400,
    )
    return fig


def compare_metrics(result_a, result_b) -> list:
    """Devuelve lista de dicts con metricas lado a lado."""
    from pid_dynamic_systems.analysis.metrics import (
        ise as _ise, overshoot as _os, rise_time as _tr,
        settling_time as _ts, steady_state_error as _sse,
    )
    import numpy as _np

    def _fmt(x):
        return f"{x:.4f}" if _np.isfinite(x) else "n/a"

    y_ss_a = float(result_a.y[-1])
    y_ss_b = float(result_b.y[-1])
    rows = [
        ("Rise time [s]", _tr(result_a.t, result_a.y, y_ss_a), _tr(result_b.t, result_b.y, y_ss_b)),
        ("Settling time [s]", _ts(result_a.t, result_a.y, y_ss_a), _ts(result_b.t, result_b.y, y_ss_b)),
        ("Overshoot [%]", _os(result_a.y, y_ss_a), _os(result_b.y, y_ss_b)),
        ("SSE", _sse(result_a.ref, y_ss_a), _sse(result_b.ref, y_ss_b)),
        ("ISE", _ise(result_a.t, result_a.error), _ise(result_b.t, result_b.error)),
    ]
    out = []
    for label, va, vb in rows:
        delta = vb - va
        out.append({
            "Metrica": label,
            "A": _fmt(va),
            "B": _fmt(vb),
            "Delta (B-A)": _fmt(delta),
        })
    return out