"""Tests de las graficas Plotly."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from pid_dynamic_systems.ui.plotly_charts import (
    control_chart, error_chart, response_chart,
)


def test_response_chart_structure() -> None:
    """response_chart tiene 1 trace (y) + 1 shape (ref horizontal)."""
    t = np.linspace(0, 1, 101)
    y = 1 - np.exp(-t)
    fig = response_chart(t, y, ref=1.0)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].name == "y(t)"
    assert len(fig.layout.shapes) == 1


def test_control_chart_structure() -> None:
    """control_chart tiene 1 trace (u)."""
    t = np.linspace(0, 1, 101)
    u = np.ones_like(t)
    fig = control_chart(t, u)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].name == "u(t)"


def test_error_chart_structure() -> None:
    """error_chart tiene 1 trace (e) + 1 shape (linea y=0)."""
    t = np.linspace(0, 1, 101)
    e = np.exp(-t)
    fig = error_chart(t, e)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].name == "e(t)"
    assert len(fig.layout.shapes) == 1