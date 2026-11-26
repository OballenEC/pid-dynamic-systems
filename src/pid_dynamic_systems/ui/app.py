"""Streamlit app para PID & Dynamic Systems."""

from __future__ import annotations

import csv
import io

import numpy as np
import streamlit as st

from pid_dynamic_systems.analysis.metrics import (
    ise, overshoot, rise_time, settling_time, steady_state_error,
)
from pid_dynamic_systems.controllers.pid import PIDController
from pid_dynamic_systems.simulation.engine import simulate
from pid_dynamic_systems.ui.plotly_charts import (
    control_chart, error_chart, response_chart,
)
from pid_dynamic_systems.ui.explanations import (
    explain_all,
    explain_overshoot,
    explain_rise_time,
    explain_saturation,
    explain_settling_time,
    explain_stability,
    explain_steady_state_error,
)
from pid_dynamic_systems.ui.state import (
    MODEL_REGISTRY, build_model, init_session_state,
)
from pid_dynamic_systems.ui.state import HELP_TEXTS, MODEL_INTRO, PRESETS
from pid_dynamic_systems.ui.state import cached_simulate

from pid_dynamic_systems.analysis.stability import (
    closed_loop_poles, damping_ratio, is_stable, natural_frequency,
)
from pid_dynamic_systems.ui.stability_plots import (
    bode_chart, closed_loop_step_chart, poles_chart,
)


from pid_dynamic_systems.report.pdf_generator import generate_pdf
from pid_dynamic_systems.ui.state import capture_config, simulate_from_config
from pid_dynamic_systems.ui.plotly_charts import comparison_chart, compare_metrics

st.set_page_config(
    page_title="PID & Dynamic Systems",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()

st.title("PID & Dynamic Systems")
st.caption("Laboratorio interactivo de sistemas dinamicos y control PID")

with st.sidebar:
    st.caption("Carga un ejemplo listo y presiona **Simular** para ver resultados. Luego explora cambiando un parametro a la vez.")
    preset_name = st.selectbox(
        "Cargar ejemplo",
        ["(ninguno)"] + list(PRESETS.keys()),
        key="preset_selector",
        help="Los presets cargan modelo + PID + simulacion ya sintonizados para un caso tipico.",
    )
    if preset_name != "(ninguno)" and st.button("Aplicar preset", key="apply_preset"):
        p = PRESETS[preset_name]
        st.session_state["model_name"] = p["model_name"]
        for k in ("Kp", "Ki", "Kd", "tau_f", "ref", "t_final", "dt"):
            if k in p:
                st.session_state[k] = float(p[k])
        st.success(f"Aplicado: {preset_name}")
        st.rerun()

    st.divider()
    st.header("Modelo")
    model_names = list(MODEL_REGISTRY.keys())
    default_idx = model_names.index(st.session_state["model_name"])
    model_name = st.selectbox("Selecciona el sistema", model_names, index=default_idx)
    st.session_state["model_name"] = model_name

    st.caption(MODEL_INTRO.get(model_name, ''))
    st.caption(MODEL_REGISTRY[model_name]["description"])
    st.caption(
        f"Salida: {MODEL_REGISTRY[model_name]['output']}  |  "
        f"Entrada: {MODEL_REGISTRY[model_name]['input']}"
    )

    st.subheader("Parametros fisicos")
    params = {}
    for pname, meta in MODEL_REGISTRY[model_name]["params"].items():
        params[pname] = st.number_input(
            f"{pname} [{meta['unit']}]",
            min_value=float(meta["min"]),
            max_value=float(meta["max"]),
            value=float(meta["default"]),
            step=float(meta["step"]),
            key=f"param_{model_name}_{pname}",
        )

    st.subheader("Controlador PID")
    Kp = st.number_input("Kp", min_value=0.0, max_value=1000.0, step=0.1, key="Kp", help=HELP_TEXTS["Kp"])
    Ki = st.number_input("Ki", min_value=0.0, max_value=1000.0, step=0.1, key="Ki", help=HELP_TEXTS["Ki"])
    Kd = st.number_input("Kd", min_value=0.0, max_value=100.0, step=0.01, key="Kd", help=HELP_TEXTS["Kd"])
    tau_f = st.number_input("tau_f [s]", min_value=1e-4, max_value=1.0,
                            step=0.001, format="%.4f", key="tau_f", help=HELP_TEXTS["tau_f"])

    st.subheader("Simulacion")
    ref = st.number_input("Setpoint", step=0.5, key="ref", help=HELP_TEXTS["ref"])
    t_final = st.number_input("Tiempo final [s]", min_value=0.1, max_value=60.0,
                              step=0.5, key="t_final", help=HELP_TEXTS["t_final"])
    dt = st.number_input("dt [s]", min_value=1e-4, max_value=0.1,
                         step=0.001, format="%.4f", key="dt", help=HELP_TEXTS["dt"])
    u_min = st.number_input("u_min", step=1.0, key="u_min", help=HELP_TEXTS["u_min"])
    u_max = st.number_input("u_max", step=1.0, key="u_max", help=HELP_TEXTS["u_max"])

    st.subheader("Perturbacion")
    dist_enabled = st.checkbox("Aplicar perturbacion", key="dist_enabled")
    dist_t_step = st.number_input(
        "t_step [s]", min_value=0.0, max_value=60.0, step=0.5,
        key="dist_t_step", help=HELP_TEXTS["dist_t_step"], disabled=not dist_enabled,
    )
    dist_magnitude = st.number_input(
        "magnitud", step=0.1, key="dist_magnitude", help=HELP_TEXTS["dist_magnitude"],
        disabled=not dist_enabled,
    )

    st.divider()
    simulate_btn = st.button("Simular", type="primary")

    st.subheader("Comparar configuraciones")
    st.caption("Guarda la config actual como A o B. Luego ve al tab Comparar.")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Guardar A"):
            st.session_state["config_a"] = capture_config(
                model_name, params, Kp, Ki, Kd, tau_f, ref, t_final, dt,
                u_min, u_max, dist_enabled, dist_t_step, dist_magnitude,
            )
            st.success("Config A guardada")
    with col_b:
        if st.button("Guardar B"):
            st.session_state["config_b"] = capture_config(
                model_name, params, Kp, Ki, Kd, tau_f, ref, t_final, dt,
                u_min, u_max, dist_enabled, dist_t_step, dist_magnitude,
            )
            st.success("Config B guardada")

    has_a = "config_a" in st.session_state
    has_b = "config_b" in st.session_state
    if has_a and has_b:
        st.info("A y B guardadas. Ve al tab **Comparar**.")
    elif has_a:
        st.caption("A guardada. Falta B.")
    elif has_b:
        st.caption("B guardada. Falta A.")
    else:
        st.caption("Aun no hay configuraciones guardadas.")
# === MAIN ===
current_snapshot = (
    model_name,
    tuple(sorted(params.items())),
    float(Kp), float(Ki), float(Kd), float(tau_f),
    float(ref), float(t_final), float(dt), float(u_min), float(u_max),
    bool(dist_enabled), float(dist_t_step), float(dist_magnitude),
)

if simulate_btn:
    with st.spinner("Simulando..."):
        result = cached_simulate(
            model_name,
            tuple(sorted(params.items())),
            float(Kp), float(Ki), float(Kd), float(tau_f),
            float(ref), float(t_final), float(dt),
            float(u_min), float(u_max),
            bool(dist_enabled), float(dist_t_step), float(dist_magnitude),
        )
    st.session_state["result"] = result
    st.session_state["result_snapshot"] = current_snapshot
    st.session_state["result_model"] = build_model(model_name, params)
    st.session_state["result_model_name"] = model_name

result = st.session_state.get("result")
saved_snapshot = st.session_state.get("result_snapshot")

tab_sim, tab_analysis, tab_learn, tab_guide, tab_compare = st.tabs(["Simulacion", "Analisis", "Aprender", "Guia", "Comparar"])

with tab_sim:
    if result is None:
        st.header("Bienvenido al laboratorio de control")
        st.markdown(
            "Esta app simula **sistemas fisicos** bajo un controlador **PID**. "
            "Eliges un modelo (motor, termico o masa-resorte), ajustas sus "
            "parametros y las ganancias del controlador, y observas como responde."
        )
        st.subheader("Como empezar en 3 pasos")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**1. Elige un modelo**")
            st.caption("En la barra lateral izquierda. O carga un preset listo.")
        with col2:
            st.markdown("**2. Ajusta el PID**")
            st.caption("Kp, Ki, Kd controlan el comportamiento. Pasa el mouse por cada campo para ver que hace.")
        with col3:
            st.markdown("**3. Presiona Simular**")
            st.caption("Veras la respuesta, las metricas y podras descargar CSV o PDF.")
        st.divider()
        st.subheader("Recomendacion para tu primera prueba")
        st.markdown(
            "Carga el preset **DC - respuesta ideal** (arriba del sidebar) "
            "y presiona el boton **Simular**. Despues cambia solo `Kp` y "
            "vuelve a simular para ver el efecto."
        )
        st.info("Consejo: el tab **Guia** (al lado de Aprender) explica cada concepto en detalle.")
    else:
        if saved_snapshot != current_snapshot:
            st.warning("Los parametros cambiaron. Presiona **Simular** para actualizar.")

        y_ss = float(result.y[-1])
        tr = rise_time(result.t, result.y, y_ss)
        ts = settling_time(result.t, result.y, y_ss)
        os_pct = overshoot(result.y, y_ss)
        sse = steady_state_error(result.ref, y_ss)
        ise_val = ise(result.t, result.error)

        m1, m2, m3 = st.columns(3)
        m1.metric("Rise time", f"{tr:.3f} s" if np.isfinite(tr) else "n/a")
        m2.metric("Settling time (+-2%)", f"{ts:.3f} s" if np.isfinite(ts) else "n/a")
        m3.metric("Overshoot", f"{os_pct:.2f} %")

        m4, m5, m6 = st.columns(3)
        m4.metric("SSE", f"{sse:.2e}")
        m5.metric("ISE", f"{ise_val:.2e}")
        m6.metric("Pasos saturados", f"{result.saturated_steps}")

        st.subheader("Respuesta temporal")
        st.plotly_chart(response_chart(result.t, result.y, result.ref),
                        use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Senal de control")
            st.plotly_chart(control_chart(result.t, result.u),
                            use_container_width=True)
        with c2:
            st.subheader("Error")
            st.plotly_chart(error_chart(result.t, result.error),
                            use_container_width=True)

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["t", "y", "u", "e"])
        for tk, yk, uk, ek in zip(result.t, result.y, result.u, result.error):
            w.writerow([f"{tk:.6g}", f"{yk:.6g}", f"{uk:.6g}", f"{ek:.6g}"])
        st.download_button(
            "Descargar CSV",
            buf.getvalue(),
            file_name="simulacion.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("Reporte PDF")
        if st.button("Preparar PDF", type="secondary"):
            with st.spinner("Generando PDF..."):
                saved_model = st.session_state.get("result_model")
                if saved_model is None:
                    st.error("Modelo no disponible. Presiona Simular primero.")
                else:
                    ctrl_pdf = PIDController(
                        Kp=Kp, Ki=Ki, Kd=Kd, tau_f=tau_f,
                        u_min=u_min, u_max=u_max, dt=dt,
                    )
                    poles_pdf = closed_loop_poles(saved_model, ctrl_pdf)
                    is_stable_pdf = is_stable(poles_pdf)
                    pole_data_pdf = [
                        {
                            "polo": f"p{i}",
                            "Re": f"{complex(p).real:+.4f}",
                            "Im": f"{complex(p).imag:+.4f}",
                            "|p| (wn)": f"{natural_frequency(p):.4f}",
                            "zeta": f"{damping_ratio(p):.4f}",
                        }
                        for i, p in enumerate(poles_pdf, start=1)
                    ]
                    y_ss_pdf = float(result.y[-1])
                    tr_pdf = rise_time(result.t, result.y, y_ss_pdf)
                    ts_pdf = settling_time(result.t, result.y, y_ss_pdf)
                    os_pdf = overshoot(result.y, y_ss_pdf)
                    sse_pdf = steady_state_error(result.ref, y_ss_pdf)
                    zeta_vals_pdf = [damping_ratio(p) for p in poles_pdf
                                     if complex(p).imag > 0]
                    zeta_pdf = max(zeta_vals_pdf) if zeta_vals_pdf else 1.0
                    wn_vals_pdf = [natural_frequency(p) for p in poles_pdf]
                    wn_pdf = max(wn_vals_pdf) if wn_vals_pdf else 0.0
                    expl_pdf = {
                        "Sobreimpulso": explain_overshoot(os_pdf, zeta_pdf),
                        "Velocidad (rise time)": explain_rise_time(tr_pdf, wn_pdf, Kp),
                        "Asentamiento": explain_settling_time(ts_pdf, zeta_pdf, Kd),
                        "Error estacionario": explain_steady_state_error(sse_pdf, Ki),
                        "Saturacion": explain_saturation(result.saturated_steps, u_min, u_max),
                        "Estabilidad": explain_stability(is_stable_pdf, poles_pdf),
                    }
                    pdf_bytes = generate_pdf(
                        result=result, model=saved_model,
                        model_name=model_name, controller=ctrl_pdf,
                        model_description=MODEL_REGISTRY[model_name]["description"],
                        params=params,
                        u_min=u_min, u_max=u_max,
                        dist_enabled=dist_enabled,
                        dist_t_step=dist_t_step,
                        dist_magnitude=dist_magnitude,
                        pole_data=pole_data_pdf,
                        is_stable=is_stable_pdf,
                        explanations=expl_pdf,
                    )
                    st.session_state["pdf_bytes"] = pdf_bytes
                    st.success(f"PDF generado ({len(pdf_bytes) // 1024} KB)")
        if st.session_state.get("pdf_bytes"):
            st.download_button(
                "Descargar PDF",
                data=st.session_state["pdf_bytes"],
                file_name=f"reporte_{model_name.replace(' ', '_').lower()}.pdf",
                mime="application/pdf",
                type="primary",
            )

with tab_analysis:
    if result is None or st.session_state.get("result_model") is None:
        st.info("Primero ejecuta una simulacion en el tab **Simulacion**.")
    else:
        saved_model = st.session_state["result_model"]
        ctrl_cl = PIDController(Kp=Kp, Ki=Ki, Kd=Kd, tau_f=tau_f,
                                u_min=u_min, u_max=u_max, dt=dt)
        poles = closed_loop_poles(saved_model, ctrl_cl)
        stable = is_stable(poles)

        st.subheader("Estabilidad del lazo cerrado")
        col_a, col_b = st.columns(2)
        col_a.metric("Estable", "SI" if stable else "NO",
                     delta=None if stable else "inestable")
        col_b.metric("Numero de polos", f"{len(poles)}")

        if len(poles) > 0:
            pole_data = []
            for i, p in enumerate(poles, start=1):
                p_c = complex(p)
                pole_data.append({
                    "polo": f"p{i}",
                    "Re": f"{p_c.real:+.4f}",
                    "Im": f"{p_c.imag:+.4f}",
                    "|p| (wn)": f"{natural_frequency(p_c):.4f}",
                    "zeta": f"{damping_ratio(p_c):.4f}",
                })
            st.dataframe(pole_data)

        st.subheader("Plano complejo")
        st.plotly_chart(poles_chart(poles))

        st.subheader("Respuesta al escalon (lazo cerrado)")
        st.plotly_chart(
            closed_loop_step_chart(saved_model, ctrl_cl, t_final=t_final, dt=dt),
            use_container_width=True,
        )

        st.subheader("Bode del lazo cerrado")
        try:
            st.plotly_chart(bode_chart(saved_model, ctrl_cl),
                            use_container_width=True)
        except Exception as exc:
            st.warning(f"No se pudo calcular el Bode: {exc}")

with tab_learn:
    if result is None or st.session_state.get("result_model") is None:
        st.info("Primero ejecuta una simulacion en el tab **Simulacion**.")
    else:
        saved_model = st.session_state["result_model"]
        ctrl_learn = PIDController(Kp=Kp, Ki=Ki, Kd=Kd, tau_f=tau_f,
                                    u_min=u_min, u_max=u_max, dt=dt)
        poles_learn = closed_loop_poles(saved_model, ctrl_learn)
        stable_learn = is_stable(poles_learn)

        y_ss_l = float(result.y[-1])
        tr_l = rise_time(result.t, result.y, y_ss_l)
        ts_l = settling_time(result.t, result.y, y_ss_l)
        os_l = overshoot(result.y, y_ss_l)
        sse_l = steady_state_error(result.ref, y_ss_l)
        zeta_vals = [damping_ratio(p) for p in poles_learn if complex(p).imag > 0]
        zeta_l = max(zeta_vals) if zeta_vals else 1.0
        wn_vals = [natural_frequency(p) for p in poles_learn]
        wn_l = max(wn_vals) if wn_vals else 0.0

        st.caption(
            "Las explicaciones de abajo se generan dinamicamente segun los "
            "resultados reales de tu simulacion. Cambia parametros y presiona "
            "**Simular** para ver como cambia la interpretacion."
        )

        with st.expander("Sobreimpulso", expanded=True):
            for line in explain_overshoot(os_l, zeta_l):
                st.write("- " + line)
        with st.expander("Velocidad (rise time)"):
            for line in explain_rise_time(tr_l, wn_l, Kp):
                st.write("- " + line)
        with st.expander("Asentamiento"):
            for line in explain_settling_time(ts_l, zeta_l, Kd):
                st.write("- " + line)
        with st.expander("Error estacionario"):
            for line in explain_steady_state_error(sse_l, Ki):
                st.write("- " + line)
        with st.expander("Saturacion"):
            for line in explain_saturation(result.saturated_steps, u_min, u_max):
                st.write("- " + line)
        with st.expander("Estabilidad"):
            for line in explain_stability(stable_learn, poles_learn):
                st.write("- " + line)

        with st.expander("Como leer todo junto"):
            st.markdown(
                "**Regla general del PID:**\n"
                "- Aumentar **Kp** acelera la respuesta pero puede aumentar el "
                "sobreimpulso y acercar el sistema a la inestabilidad.\n"
                "- Aumentar **Ki** elimina el error estacionario pero puede "
                "introducir oscilaciones lentas.\n"
                "- Aumentar **Kd** amortigua (reduce sobreimpulso) pero "
                "amplifica ruido de medicion.\n"
                "- **tau_f** filtra la derivada: mas grande = mas suave pero "
                "menos reactivo."
            )
with tab_guide:
    st.header("Guia de uso")
    st.markdown(
        "Manual rapido de la app. Para la version completa, ver "
        "[`docs/user_manual.md`](https://github.com/OballenEC/pid-dynamic-systems/blob/main/docs/user_manual.md) "
        "en el repositorio."
    )

    st.subheader("Que hace esta app")
    st.markdown(
        "Simula **3 sistemas fisicos** bajo un controlador **PID discreto**. "
        "Puedes cambiar parametros del modelo y del controlador, ejecutar la "
        "simulacion, y ver el resultado en tiempo real con graficas, metricas "
        "y explicaciones generadas automaticamente."
    )

    st.subheader("Los 3 sistemas")
    st.markdown(
        "- **Motor DC:** control de velocidad angular. Entrada = voltaje, salida = omega [rad/s].\n"
        "- **Sistema termico:** control de temperatura. Entrada = potencia, salida = T [K].\n"
        "- **Masa-resorte-amortiguador:** control de posicion. Entrada = fuerza, salida = x [m]."
    )

    with st.expander("Que significa cada parametro del PID", expanded=False):
        st.markdown(
            "**Kp (proporcional):** reacciona al error actual. Aumentar Kp = mas "
            "rapido pero mas overshoot.\n\n"
            "**Ki (integral):** acumula el error en el tiempo. Elimina el error "
            "estacionario (offset). Si es muy alto, causa oscilaciones lentas.\n\n"
            "**Kd (derivativo):** reacciona al cambio del error. Amortigua el "
            "overshoot. Si es muy alto, amplifica ruido.\n\n"
            "**tau_f:** constante del filtro de derivada. Mas grande = derivada "
            "mas suave pero menos reactiva."
        )

    with st.expander("Que significa cada metrica de la simulacion", expanded=False):
        st.markdown(
            "- **Rise time:** tiempo en ir del 10% al 90% del valor final. "
            "Mide velocidad de respuesta.\n"
            "- **Settling time (+-2%):** tiempo en entrar y quedarse dentro del "
            "+-2% del setpoint. Mide cuando se estabiliza.\n"
            "- **Overshoot (%):** cuanto rebasa el setpoint. 0% = sin sobrepico.\n"
            "- **SSE:** error estacionario. Diferencia final respecto al setpoint.\n"
            "- **ISE:** integral del error cuadratico. Penaliza errores grandes.\n"
            "- **Pasos saturados:** cuantos pasos el controlador quedo limitado "
            "por u_min/u_max."
        )

    with st.expander("Que significa el tab Analisis", expanded=False):
        st.markdown(
            "**Polos del lazo cerrado:** raices del denominador de T(s) = G*C/(1+G*C).\n"
            "- Re < 0: sistema estable\n"
            "- Re > 0: sistema INESTABLE\n"
            "- Cerca del eje imaginario: margen pequeno\n\n"
            "**zeta:** coeficiente de amortiguamiento. zeta < 1 = subamortiguado (oscila).\n\n"
            "**wn:** frecuencia natural. Mas grande = mas rapido.\n\n"
            "**Bode:** muestra como responde el sistema a distintas frecuencias."
        )

    with st.expander("Reglas de oro del PID", expanded=True):
        st.markdown(
            "1. **Aumenta Kp** -> mas rapido, mas overshoot, riesgo de inestabilidad.\n"
            "2. **Aumenta Ki** -> elimina offset, pero puede oscilar.\n"
            "3. **Aumenta Kd** -> reduce overshoot, pero amplifica ruido.\n"
            "4. **Siempre**: cambia un parametro a la vez y compara resultados.\n"
            "5. **Si el sistema es inestable**: empieza reduciendo Kp, luego Ki."
        )

    with st.expander("Como interpretar el tab Aprender", expanded=False):
        st.markdown(
            "El tab **Aprender** genera texto dinamicamente segun los resultados "
            "reales de tu simulacion. Si cambias Kp y simulas, el texto cambia "
            "para reflejar el nuevo comportamiento. Usalo para entender **por "
            "que** paso lo que viste."
        )

    with st.expander("Problemas comunes", expanded=False):
        st.markdown(
            "- **\"El sistema no converge\"**: aumenta Ki o extiende t_final.\n"
            "- **\"Oscila mucho\"**: reduce Kp o aumenta Kd.\n"
            "- **\"La senal de control se satura\"**: aumenta u_max o reduce las ganancias.\n"
            "- **\"El PDF tarda\"**: la primera generacion tarda 2-3 s (matplotlib). Es normal."
        )
with tab_compare:
    st.header("Comparar configuraciones")
    cfg_a = st.session_state.get("config_a")
    cfg_b = st.session_state.get("config_b")

    if cfg_a is None and cfg_b is None:
        st.info(
            "Aun no hay configuraciones guardadas. Ve al sidebar, "
            "configura el sistema y presiona **Guardar A** o **Guardar B**."
        )
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Configuracion A")
            if cfg_a is None:
                st.warning("Falta A. Presiona **Guardar A** en el sidebar.")
            else:
                st.write(f"Modelo: **{cfg_a['model_name']}**")
                st.write(f"Kp={cfg_a['Kp']}, Ki={cfg_a['Ki']}, Kd={cfg_a['Kd']}")
                st.write(f"ref={cfg_a['ref']}, t_final={cfg_a['t_final']}")
        with col_b:
            st.subheader("Configuracion B")
            if cfg_b is None:
                st.warning("Falta B. Presiona **Guardar B** en el sidebar.")
            else:
                st.write(f"Modelo: **{cfg_b['model_name']}**")
                st.write(f"Kp={cfg_b['Kp']}, Ki={cfg_b['Ki']}, Kd={cfg_b['Kd']}")
                st.write(f"ref={cfg_b['ref']}, t_final={cfg_b['t_final']}")

        st.divider()
        if cfg_a is not None and cfg_b is not None:
            if st.button("Simular y comparar", type="primary"):
                with st.spinner("Simulando A y B..."):
                    try:
                        res_a = simulate_from_config(cfg_a)
                        res_b = simulate_from_config(cfg_b)
                        st.session_state["comparison_result"] = (res_a, res_b)
                    except Exception as exc:
                        st.error(f"Error simulando: {exc}")

            comparison = st.session_state.get("comparison_result")
            if comparison is not None:
                res_a, res_b = comparison
                label_a = f"A: {cfg_a['model_name']} (Kp={cfg_a['Kp']})"
                label_b = f"B: {cfg_b['model_name']} (Kp={cfg_b['Kp']})"

                st.plotly_chart(
                    comparison_chart(
                        res_a.t, res_a.y, res_a.ref,
                        res_b.t, res_b.y, res_b.ref,
                        label_a, label_b,
                    ),
                )

                st.subheader("Metricas lado a lado")
                rows = compare_metrics(res_a, res_b)
                st.dataframe(rows)

                st.subheader("Como interpretar")
                st.caption(
                    "**Delta (B - A)** indica cuanto cambio de A a B. "
                    "Delta positivo en overshoot = B tiene mas sobreimpulso. "
                    "Delta negativo en rise time = B es mas rapido."
                )
                if st.button("Limpiar comparacion"):
                    if "comparison_result" in st.session_state:
                        del st.session_state["comparison_result"]
                    st.rerun()
        else:
            st.info("Necesitas A y B guardadas para comparar.")