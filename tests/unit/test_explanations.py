"""Tests del modulo educativo."""

from __future__ import annotations

from pid_dynamic_systems.ui.explanations import (
    explain_all, explain_overshoot, explain_saturation,
    explain_stability, explain_steady_state_error,
)


def test_explain_overshoot_returns_list() -> None:
    """Siempre devuelve lista no vacia."""
    assert len(explain_overshoot(20.0, 0.4)) > 0
    assert len(explain_overshoot(0.0, 1.5)) > 0
    assert len(explain_overshoot(50.0, 0.1)) > 0


def test_explain_overshoot_low_and_high_differ() -> None:
    """Sobreimpulso bajo y alto producen texto distinto."""
    low = " ".join(explain_overshoot(1.0, 1.5))
    high = " ".join(explain_overshoot(40.0, 0.15))
    assert low != high


def test_explain_saturation_no_saturation() -> None:
    """Cero pasos saturados menciona 'Sin saturacion'."""
    lines = explain_saturation(0, -10.0, 10.0)
    assert any("Sin saturacion" in s for s in lines)


def test_explain_saturation_with_saturation() -> None:
    """Saturacion alta menciona anti-windup."""
    lines = explain_saturation(100, -1.0, 1.0)
    joined = " ".join(lines)
    assert "anti-windup" in joined.lower()


def test_explain_stability_stable() -> None:
    """Polos con Re<0 producen texto estable."""
    lines = explain_stability(True, [complex(-1, 1), complex(-2, 0)])
    joined = " ".join(lines).lower()
    assert "estable" in joined


def test_explain_stability_unstable() -> None:
    """Un polo con Re>0 produce texto inestable."""
    lines = explain_stability(False, [complex(0.5, 1)])
    joined = " ".join(lines).lower()
    assert "inestable" in joined


def test_explain_steady_state_error_ki_effect() -> None:
    """SSE grande con Ki bajo menciona aumentar Ki."""
    lines = explain_steady_state_error(0.5, 0.0)
    joined = " ".join(lines).lower()
    assert "aumentar ki" in joined or "ki" in joined


def test_explain_all_returns_dict() -> None:
    """explain_all devuelve dict con 6 temas, cada uno no vacio."""
    d = explain_all(
        overshoot_pct=20.0, zeta=0.4, rise_time=0.5, settling_time=2.0,
        wn=3.0, Kp=1.0, Ki=1.0, Kd=0.1, sse=0.01, saturated_steps=0,
        u_min=-10.0, u_max=10.0, is_stable=True,
        poles=[complex(-1, 1), complex(-2, 0)],
    )
    assert len(d) == 6
    for v in d.values():
        assert isinstance(v, list) and len(v) > 0