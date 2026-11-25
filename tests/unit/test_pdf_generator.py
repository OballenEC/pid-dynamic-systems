"""Tests del generador de PDF."""

from __future__ import annotations

from pid_dynamic_systems.analysis.stability import (
    closed_loop_poles, damping_ratio, is_stable, natural_frequency,
)
from pid_dynamic_systems.controllers.pid import PIDController
from pid_dynamic_systems.models.dc_motor import DCMotor
from pid_dynamic_systems.report.pdf_generator import generate_pdf
from pid_dynamic_systems.simulation.engine import simulate
from pid_dynamic_systems.ui.explanations import explain_all


def _build_report():
    m = DCMotor()
    c = PIDController(Kp=1.0, Ki=1.0, Kd=0.0, dt=0.01, u_min=-1000, u_max=1000)
    r = simulate(m, c, ref=10.0, t_final=3.0, dt=0.01)
    poles = closed_loop_poles(m, c)
    pole_data = [{
        "polo": f"p{i}",
        "Re": f"{complex(p).real:+.4f}",
        "Im": f"{complex(p).imag:+.4f}",
        "|p|": f"{natural_frequency(p):.4f}",
        "zeta": f"{damping_ratio(p):.4f}",
    } for i, p in enumerate(poles, start=1)]
    y_ss = float(r.y[-1])
    from pid_dynamic_systems.analysis.metrics import (
        overshoot, rise_time, settling_time, steady_state_error,
    )
    expl = explain_all(
        overshoot_pct=overshoot(r.y, y_ss), zeta=0.7,
        rise_time=rise_time(r.t, r.y, y_ss),
        settling_time=settling_time(r.t, r.y, y_ss),
        wn=3.0, Kp=1.0, Ki=1.0, Kd=0.0,
        sse=steady_state_error(r.ref, y_ss),
        saturated_steps=r.saturated_steps,
        u_min=-1000.0, u_max=1000.0,
        is_stable=is_stable(poles), poles=poles,
    )
    pdf = generate_pdf(
        result=r, model=m, model_name="Motor DC", controller=c,
        model_description="Control de velocidad", params={"R": 1.0, "L": 0.5},
        u_min=-1000.0, u_max=1000.0,
        dist_enabled=False, dist_t_step=0.0, dist_magnitude=0.0,
        pole_data=pole_data, is_stable=is_stable(poles), explanations=expl,
    )
    return pdf


def test_pdf_returns_bytes() -> None:
    """generate_pdf devuelve bytes no vacios."""
    pdf = _build_report()
    assert isinstance(pdf, bytes)
    assert len(pdf) > 1000


def test_pdf_has_pdf_header() -> None:
    """Los bytes empiezan con %PDF-."""
    pdf = _build_report()
    assert pdf[:5] == b"%PDF-"


def test_pdf_ends_with_eof() -> None:
    """Los bytes terminan con %%EOF."""
    pdf = _build_report()
    assert pdf.rstrip().endswith(b"%%EOF")