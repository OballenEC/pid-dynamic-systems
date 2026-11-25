"""Metricas de respuesta temporal para sistemas de control."""

from __future__ import annotations

import numpy as np


def rise_time(t: np.ndarray, y: np.ndarray, y_ss: float,
              lo: float = 0.1, hi: float = 0.9) -> float:
    """Tiempo de subida lo-hi (default 10%-90%) interpolado. NaN si no cruza."""
    if y_ss == 0:
        return float("nan")
    y_norm = y / y_ss
    i_lo = int(np.argmax(y_norm >= lo))
    i_hi = int(np.argmax(y_norm >= hi))
    if not (y_norm[i_lo] >= lo) or not (y_norm[i_hi] >= hi):
        return float("nan")

    def _interp(i: int, level: float) -> float:
        if i == 0:
            return float(t[0])
        y0, y1 = float(y_norm[i - 1]), float(y_norm[i])
        if y1 == y0:
            return float(t[i])
        frac = (level - y0) / (y1 - y0)
        return float(t[i - 1] + frac * (t[i] - t[i - 1]))

    return _interp(i_hi, hi) - _interp(i_lo, lo)


def settling_time(t: np.ndarray, y: np.ndarray, y_ss: float,
                  band: float = 0.02) -> float:
    """Tiempo de establecimiento: ultimo t fuera de +-band*|y_ss|. NaN si no."""
    if y_ss != 0:
        tol = band * abs(y_ss)
    else:
        tol = band * float(np.max(np.abs(y)))
    if tol == 0:
        return 0.0
    out = np.where(np.abs(y - y_ss) > tol)[0]
    if len(out) == 0:
        return 0.0
    last = int(out[-1])
    if last >= len(t) - 1:
        return float("nan")
    return float(t[last + 1])


def overshoot(y: np.ndarray, y_ss: float) -> float:
    """Sobreimpulso porcentual. Positivo si pico sobre y_ss; negativo si bajo."""
    if y_ss == 0:
        return 0.0
    peak = float(np.max(y)) if y_ss > 0 else float(np.min(y))
    return (peak - y_ss) / y_ss * 100.0


def steady_state_error(ref: float, y_ss: float) -> float:
    """|ref - y_ss|."""
    return float(abs(ref - y_ss))


def ise(t: np.ndarray, e: np.ndarray) -> float:
    """Integral del error cuadratico (trapezoidal)."""
    try:
        return float(np.trapezoid(e * e, t))
    except AttributeError:
        return float(np.trapz(e * e, t))
