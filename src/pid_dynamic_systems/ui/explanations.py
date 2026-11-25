"""Explicaciones dinamicas del comportamiento del sistema.

Funciones puras: no importan streamlit. Reciben solo los datos
necesarios y devuelven lista de strings (parrafos o vinetas).
"""

from __future__ import annotations

from typing import Sequence


def explain_overshoot(overshoot_pct: float, zeta: float) -> list[str]:
    """Interpreta el sobreimpulso en funcion del amortiguamiento."""
    lines: list[str] = []
    if overshoot_pct < 0.5:
        lines.append(
            "Sin sobreimpulso significativo: respuesta sobreamortiguada o "
            "criticamente amortiguada. El sistema no rebasa el setpoint."
        )
    elif overshoot_pct < 10.0:
        lines.append(
            f"Sobreimpulso bajo ({overshoot_pct:.1f}%). Amortiguamiento "
            "adecuado para la mayoria de aplicaciones industriales."
        )
    elif overshoot_pct < 25.0:
        lines.append(
            f"Sobreimpulso moderado ({overshoot_pct:.1f}%). Tipico de sistemas "
            "subamortiguados (zeta ~ 0.4-0.7). La respuesta rebasa el "
            "setpoint antes de estabilizarse."
        )
    else:
        lines.append(
            f"Sobreimpulso alto ({overshoot_pct:.1f}%). El sistema es marcadamente "
            "subamortiguado. En aplicaciones fisicas (motores, actuadores) esto "
            "puede danar el equipo o saturar el actuador."
        )
    if zeta < 0.7 and overshoot_pct > 5.0:
        lines.append(
            f"Con zeta = {zeta:.3f} el sistema oscila antes de asentarse. "
            "Aumentar Kd incrementa el amortiguamiento efectivo y suaviza el pico."
        )
    return lines


def explain_rise_time(rise_time: float, wn: float, Kp: float) -> list[str]:
    """Interpreta el tiempo de subida en funcion de la frecuencia natural."""
    lines: list[str] = []
    if not (rise_time == rise_time):  # NaN check sin importar math
        lines.append(
            "El sistema no alcanza el 90% del valor final en el horizonte "
            "simulado. Considera aumentar Kp o extender t_final."
        )
        return lines
    if wn > 0:
        approx = 1.8 / wn
        if abs(rise_time - approx) / approx < 0.5:
            lines.append(
                f"Rise time = {rise_time:.3f} s, consistente con 1.8/wn "
                f"(wn = {wn:.3f} rad/s). La velocidad de respuesta esta dominada "
                "por la dinamica del sistema, no solo por Kp."
            )
        else:
            lines.append(
                f"Rise time = {rise_time:.3f} s (referencia 1.8/wn = {approx:.3f} s). "
                "La diferencia sugiere que la dinamica del lazo cerrado esta "
                "modificada significativamente por el controlador."
            )
    else:
        lines.append(f"Rise time = {rise_time:.3f} s.")
    if Kp > 10.0:
        lines.append(
            f"Con Kp = {Kp:.2f} elevado la accion proporcional acelera la "
            "respuesta pero tambien puede amplificar el ruido de medicion."
        )
    elif Kp < 0.5:
        lines.append(
            f"Con Kp = {Kp:.2f} bajo el controlador es suave. El rise time "
            "podria reducirse incrementando Kp."
        )
    return lines


def explain_settling_time(settling_time: float, zeta: float,
                          Kd: float) -> list[str]:
    """Interpreta el tiempo de establecimiento (+-2%)."""
    lines: list[str] = []
    if not (settling_time == settling_time):  # NaN
        lines.append(
            "El sistema no se estabiliza dentro de la banda +-2% en el tiempo "
            "simulado. Esto puede indicar oscilacion sostenida o deriva."
        )
        return lines
    if zeta > 0 and zeta < 1:
        approx = 4.0 / (zeta * max(1.0, 1.0))  # simplificado
        lines.append(
            f"Settling time = {settling_time:.3f} s. Con zeta = {zeta:.3f} "
            "el sistema esta subamortiguado; el asentamiento esta limitado por "
            "el decaimiento exponencial de la envolvente."
        )
    else:
        lines.append(
            f"Settling time = {settling_time:.3f} s. Amortiguamiento suficiente "
            "para entrar en la banda +-2% rapidamente."
        )
    if settling_time > 5.0 and Kd < 0.1:
        lines.append(
            "El asentamiento es lento y Kd es bajo. Un incremento moderado de "
            "Kd puede reducir el settling time sin sacrificar velocidad."
        )
    return lines
def explain_steady_state_error(sse: float, Ki: float) -> list[str]:
    """Explica el error estacionario en funcion de la accion integral."""
    lines: list[str] = []
    if sse < 1e-3:
        lines.append(
            f"Error estacionario practicamente nulo ({sse:.2e}). "
            "La accion integral esta eliminando el offset correctamente."
        )
    elif sse < 0.05:
        lines.append(
            f"Error estacionario pequeno ({sse:.2e}). Aceptable para la "
            "mayoria de aplicaciones de control."
        )
    elif Ki < 0.1:
        lines.append(
            f"Error estacionario {sse:.2e} con Ki = {Ki:.3f} bajo. "
            "Sin accion integral suficiente, el sistema mantiene un offset "
            "permanente. Aumentar Ki lo reduce (a costa de posible sobreimpulso)."
        )
    else:
        lines.append(
            f"Error estacionario {sse:.2e} a pesar de Ki = {Ki:.3f}. "
            "Posibles causas: saturacion persistente del actuador (anti-windup "
            "activo) o perturbacion no compensada."
        )
    return lines


def explain_saturation(saturated_steps: int, u_min: float,
                       u_max: float) -> list[str]:
    """Interpreta los pasos saturados en funcion de los limites del actuador."""
    lines: list[str] = []
    if saturated_steps == 0:
        lines.append(
            "Sin saturacion: el controlador opera dentro de sus limites "
            f"[{u_min:g}, {u_max:g}] durante toda la simulacion."
        )
    elif saturated_steps < 10:
        lines.append(
            f"Saturacion breve ({saturated_steps} pasos). Tipico al inicio si "
            "el error inicial es grande; el controlador recupera rapido."
        )
    else:
        lines.append(
            f"Saturacion en {saturated_steps} pasos. El actuador esta "
            f"trabajando al limite [{u_min:g}, {u_max:g}]. El anti-windup "
            "evita que la integral crezca sin control durante este periodo."
        )
        lines.append(
            "Considera: aumentar los limites si el actuador fisico lo permite, "
            "reducir las ganancias, o suavizar el setpoint con una rampa."
        )
    return lines


def explain_stability(is_stable: bool, poles: Sequence[complex]) -> list[str]:
    """Explica la estabilidad del lazo cerrado en funcion de los polos."""
    lines: list[str] = []
    if is_stable:
        real_parts = [complex(p).real for p in poles]
        max_real = max(real_parts) if real_parts else 0.0
        lines.append(
            f"Lazo cerrado estable: todos los polos tienen Re < 0. "
            f"El polo dominante tiene Re = {max_real:+.4f}."
        )
        if max_real > -0.1:
            lines.append(
                "El polo dominante esta muy cerca del eje imaginario: el "
                "sistema es estable pero con margen pequeno. Perturbaciones "
                "pequenas podrian sacarlo de la region segura."
            )
        else:
            lines.append(
                "Margen de estabilidad saludable. El sistema regresara al "
                "setpoint despues de una perturbacion."
            )
    else:
        unstable = [p for p in poles if complex(p).real >= 0]
        lines.append(
            f"Lazo cerrado INESTABLE: {len(unstable)} polo(s) con Re >= 0. "
            "La respuesta crecera sin limite. Reduce Kp, Ki o Kd segun el caso."
        )
        lines.append(
            "Heuristica: si con Ki=0 el sistema estabiliza pero con Ki>0 no, "
            "el problema es la accion integral. Si nunca estabiliza, el Kp es "
            "excesivo para la dinamica del modelo."
        )
    return lines


def explain_all(
    overshoot_pct: float,
    zeta: float,
    rise_time: float,
    settling_time: float,
    wn: float,
    Kp: float,
    Ki: float,
    Kd: float,
    sse: float,
    saturated_steps: int,
    u_min: float,
    u_max: float,
    is_stable: bool,
    poles: Sequence[complex],
) -> dict[str, list[str]]:
    """Devuelve dict con explicaciones agrupadas por tema."""
    return {
        "Sobreimpulso": explain_overshoot(overshoot_pct, zeta),
        "Velocidad (rise time)": explain_rise_time(rise_time, wn, Kp),
        "Asentamiento": explain_settling_time(settling_time, zeta, Kd),
        "Error estacionario": explain_steady_state_error(sse, Ki),
        "Saturacion": explain_saturation(saturated_steps, u_min, u_max),
        "Estabilidad": explain_stability(is_stable, poles),
    }