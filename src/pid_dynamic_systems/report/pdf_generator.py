"""Generador de reportes PDF con ReportLab + matplotlib."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from pid_dynamic_systems.analysis.metrics import (
    ise, overshoot, rise_time, settling_time, steady_state_error,
)


def _fig_to_bytes(fig) -> io.BytesIO:
    """Convierte figura matplotlib a PNG en BytesIO."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _make_response_fig(t, y, ref) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(t, y, label="y(t)", linewidth=1.5)
    ax.axhline(ref, linestyle="--", color="gray", label="ref")
    ax.set_xlabel("t [s]")
    ax.set_ylabel("salida")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    ax.set_title("Respuesta temporal")
    return _fig_to_bytes(fig)


def _make_control_fig(t, u) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(8, 3.0))
    ax.plot(t, u, label="u(t)", color="tab:orange", linewidth=1.5)
    ax.set_xlabel("t [s]")
    ax.set_ylabel("u")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    ax.set_title("Senal de control")
    return _fig_to_bytes(fig)


def _make_error_fig(t, e) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(8, 3.0))
    ax.plot(t, e, label="e(t)", color="tab:red", linewidth=1.5)
    ax.axhline(0, linestyle=":", color="gray")
    ax.set_xlabel("t [s]")
    ax.set_ylabel("e")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    ax.set_title("Error")
    return _fig_to_bytes(fig)
def generate_pdf(
    result,
    model,
    model_name: str,
    controller,
    model_description: str,
    params: dict,
    u_min: float,
    u_max: float,
    dist_enabled: bool,
    dist_t_step: float,
    dist_magnitude: float,
    pole_data: Sequence[dict],
    is_stable: bool,
    explanations: dict[str, list[str]],
) -> bytes:
    """Genera un PDF de reporte y devuelve los bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="PID & Dynamic Systems - Reporte",
    )
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=9, leading=11)

    elements = []

    # === Portada ===
    elements.append(Spacer(1, 3*cm))
    elements.append(Paragraph("PID &amp; Dynamic Systems", h1))
    elements.append(Paragraph("Reporte de simulacion", h2))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        f"<b>Modelo:</b> {model_name}<br/>"
        f"<b>Descripcion:</b> {model_description}<br/>"
        f"<b>Generado:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        body,
    ))
    elements.append(PageBreak())

    # === Parametros ===
    elements.append(Paragraph("1. Parametros de configuracion", h1))
    elements.append(Spacer(1, 0.3*cm))

    param_rows = [["Parametro fisico", "Valor"]]
    for k, v in params.items():
        param_rows.append([k, f"{v:g}"])
    pid_rows = [["PID", "Valor"],
                ["Kp", f"{controller.Kp:g}"],
                ["Ki", f"{controller.Ki:g}"],
                ["Kd", f"{controller.Kd:g}"],
                ["tau_f [s]", f"{controller.tau_f:g}"]]
    sim_rows = [["Simulacion", "Valor"],
                ["Setpoint", f"{result.ref:g}"],
                ["t_final [s]", f"{result.t_final:g}"],
                ["dt [s]", f"{result.dt:g}"],
                ["u_min", f"{u_min:g}"],
                ["u_max", f"{u_max:g}"],
                ["Perturbacion", "escalon" if dist_enabled else "no"],
                ["t_step [s]", f"{dist_t_step:g}" if dist_enabled else "-"],
                ["magnitud", f"{dist_magnitude:g}" if dist_enabled else "-"]]

    def _mk_table(data):
        t = Table(data, colWidths=[6*cm, 5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E86AB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    elements.append(_mk_table(param_rows))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(_mk_table(pid_rows))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(_mk_table(sim_rows))
    elements.append(PageBreak())

    # === Graficas ===
    elements.append(Paragraph("2. Graficas", h1))
    elements.append(Spacer(1, 0.3*cm))
    for label, buf_fig in [
        ("Respuesta temporal", _make_response_fig(result.t, result.y, result.ref)),
        ("Senal de control", _make_control_fig(result.t, result.u)),
        ("Error", _make_error_fig(result.t, result.error)),
    ]:
        elements.append(Paragraph(label, h2))
        elements.append(Image(buf_fig, width=16*cm, height=6.5*cm))
        elements.append(Spacer(1, 0.4*cm))
    elements.append(PageBreak())

    # === Metricas ===
    elements.append(Paragraph("3. Metricas de desempeno", h1))
    elements.append(Spacer(1, 0.3*cm))

    y_ss = float(result.y[-1])
    tr = rise_time(result.t, result.y, y_ss)
    ts = settling_time(result.t, result.y, y_ss)
    os_pct = overshoot(result.y, y_ss)
    sse = steady_state_error(result.ref, y_ss)
    ise_val = ise(result.t, result.error)

    def _fmt(x):
        return f"{x:.4f}" if np.isfinite(x) else "n/a"

    metric_rows = [
        ["Metrica", "Valor"],
        ["Rise time (10-90%) [s]", _fmt(tr)],
        ["Settling time (+-2%) [s]", _fmt(ts)],
        ["Overshoot [%]", f"{os_pct:.2f}"],
        ["Error estacionario", f"{sse:.3e}"],
        ["ISE", f"{ise_val:.3e}"],
        ["Pasos saturados", f"{result.saturated_steps}"],
        ["Estable", "SI" if is_stable else "NO"],
    ]
    elements.append(_mk_table(metric_rows))
    elements.append(Spacer(1, 0.5*cm))

    if pole_data:
        elements.append(Paragraph("Polos del lazo cerrado", h2))
        pole_table = [list(pole_data[0].keys())]
        for row in pole_data:
            pole_table.append(list(row.values()))
        t_poles = Table(pole_table)
        t_poles.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E86AB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(t_poles)
    elements.append(PageBreak())

    # === Interpretacion ===
    elements.append(Paragraph("4. Interpretacion", h1))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "Las siguientes observaciones se generan dinamicamente a partir "
        "de los resultados de la simulacion.", small,
    ))
    elements.append(Spacer(1, 0.3*cm))
    for topic, lines in explanations.items():
        elements.append(Paragraph(topic, h2))
        for line in lines:
            elements.append(Paragraph("&bull; " + line.replace("<", "&lt;").replace(">", "&gt;"), body))
        elements.append(Spacer(1, 0.2*cm))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()