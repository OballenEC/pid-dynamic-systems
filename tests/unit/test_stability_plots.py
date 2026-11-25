"""Tests de las graficas de estabilidad."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from pid_dynamic_systems.analysis.stability import closed_loop_poles
from pid_dynamic_systems.controllers.pid import PIDController
from pid_dynamic_systems.models.dc_motor import DCMotor
from pid_dynamic_systems.ui.stability_plots import (
    bode_chart, closed_loop_step_chart, poles_chart,
)


def test_poles_chart_has_scatter() -> None:
    """poles_chart tiene 1 trace scatter con marcadores."""
    m = DCMotor()
    c = PIDController(Kp=1.0, Ki=1.0, Kd=0.0)
    poles = closed_loop_poles(m, c)
    fig = poles_chart(poles)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].mode == "markers"


def test_step_chart_traces() -> None:
    """closed_loop_step_chart tiene 1 trace (y(t)) + 1 shape (ref=1)."""
    m = DCMotor()
    c = PIDController(Kp=1.0, Ki=1.0, Kd=0.0)
    fig = closed_loop_step_chart(m, c, t_final=1.0, dt=0.01)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert len(fig.layout.shapes) == 1


def test_bode_chart_two_traces() -> None:
    """bode_chart tiene 2 traces: magnitud y fase."""
    m = DCMotor()
    c = PIDController(Kp=1.0, Ki=1.0, Kd=0.0)
    fig = bode_chart(m, c)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert "dB" in fig.data[0].name
    assert "fase" in fig.data[1].name