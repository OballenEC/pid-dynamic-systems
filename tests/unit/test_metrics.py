"""Tests de metricas de respuesta temporal."""

from __future__ import annotations

import numpy as np
import pytest

from pid_dynamic_systems.analysis.metrics import (
    ise, overshoot, rise_time, settling_time, steady_state_error,
)


def test_rise_time_first_order() -> None:
    """Rise time 10-90% en 1er orden tau=1: ~2.197 s (analitico)."""
    t = np.linspace(0, 10, 100001)
    y = 1.0 - np.exp(-t)
    rt = rise_time(t, y, y_ss=1.0)
    assert rt == pytest.approx(2.197, abs=0.01)


def test_settling_time_first_order() -> None:
    """Settling time +-2% en 1er orden tau=1: -ln(0.02) = 3.912 s."""
    t = np.linspace(0, 10, 100001)
    y = 1.0 - np.exp(-t)
    st = settling_time(t, y, y_ss=1.0, band=0.02)
    assert st == pytest.approx(3.912, abs=0.02)


def test_overshoot_positive() -> None:
    """Pico 20% sobre y_ss."""
    y = np.array([0.0, 0.5, 1.2, 1.05, 1.0])
    assert overshoot(y, y_ss=1.0) == pytest.approx(20.0)


def test_steady_state_error() -> None:
    """SSE = |ref - y_ss|."""
    assert steady_state_error(ref=5.0, y_ss=4.9) == pytest.approx(0.1)


def test_ise_rampa() -> None:
    """ISE de e(t)=t en [0,1] = 1/3."""
    t = np.linspace(0, 1, 100001)
    e = t.copy()
    assert ise(t, e) == pytest.approx(1.0 / 3.0, abs=1e-6)


def test_rise_time_nan_when_never_reached() -> None:
    """Si nunca alcanza el nivel, rise_time = NaN."""
    t = np.linspace(0, 1, 100)
    y = np.zeros_like(t)
    assert np.isnan(rise_time(t, y, y_ss=1.0))
