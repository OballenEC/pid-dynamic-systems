"""Tests de comparacion de configuraciones."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import pytest

from pid_dynamic_systems.controllers.pid import PIDController
from pid_dynamic_systems.models.dc_motor import DCMotor
from pid_dynamic_systems.simulation.engine import simulate
from pid_dynamic_systems.ui.plotly_charts import comparison_chart, compare_metrics
from pid_dynamic_systems.ui.state import capture_config


def test_capture_config_returns_hashable_dict() -> None:
    cfg = capture_config(
        "Motor DC", {"R": 1.0, "L": 0.5},
        Kp=1.0, Ki=1.0, Kd=0.0, tau_f=0.01,
        ref=10.0, t_final=5.0, dt=0.001,
        u_min=-1000.0, u_max=1000.0,
        dist_enabled=False, dist_t_step=0.0, dist_magnitude=0.0,
    )
    assert isinstance(cfg["params"], tuple)
    assert cfg["model_name"] == "Motor DC"
    hash(cfg["params"])


def test_comparison_chart_two_traces() -> None:
    t = np.linspace(0, 5, 501)
    ya = 1 - np.exp(-t)
    yb = 1 - np.exp(-2 * t)
    fig = comparison_chart(t, ya, 1.0, t, yb, 1.0)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert len(fig.layout.shapes) == 2


def test_compare_metrics_returns_rows() -> None:
    m = DCMotor()
    r_a = simulate(m, PIDController(Kp=1.0, Ki=1.0, Kd=0.0), ref=10.0, t_final=3.0, dt=0.01)
    r_b = simulate(m, PIDController(Kp=5.0, Ki=1.0, Kd=0.0), ref=10.0, t_final=3.0, dt=0.01)
    rows = compare_metrics(r_a, r_b)
    assert len(rows) == 5
    for row in rows:
        assert set(row.keys()) == {"Metrica", "A", "B", "Delta (B-A)"}


def test_compare_metrics_identical_results_zero_delta() -> None:
    m = DCMotor()
    r = simulate(m, PIDController(Kp=1.0, Ki=1.0, Kd=0.0), ref=10.0, t_final=2.0, dt=0.01)
    rows = compare_metrics(r, r)
    for row in rows:
        if row["Delta (B-A)"] != "n/a":
            assert float(row["Delta (B-A)"]) == pytest.approx(0.0, abs=1e-6)


def test_compare_metrics_different_gains_different_metrics() -> None:
    m = DCMotor()
    r_a = simulate(m, PIDController(Kp=1.0, Ki=1.0, Kd=0.0), ref=10.0, t_final=3.0, dt=0.01)
    r_b = simulate(m, PIDController(Kp=10.0, Ki=1.0, Kd=0.0), ref=10.0, t_final=3.0, dt=0.01)
    rows = compare_metrics(r_a, r_b)
    has_difference = any(row["Delta (B-A)"] not in ("0.0000", "n/a") for row in rows)
    assert has_difference