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
from pid_dynamic_systems.ui.explanations import explain_all
from pid_dynamic_systems.ui.state import (
    MODEL_REGISTRY, build_model, init_session_state,
)

from pid_dynamic_systems.analysis.stability import (
    damping_ratio, is_stable, natural_frequency,
)
from pid_dynamic_systems.ui.stability_plots import (
    bode_chart, closed_loop_step_chart, poles_chart,
)


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
    st.header("Modelo")
    model_names = list(MODEL_REGISTRY.keys())
    default_idx = model_names.index(st.session_state["model_name"])
    model_name = st.selectbox("Selecciona el sistema", model_names, index=default_idx)
    st.session_state["model_name"] = model_name

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
    Kp = st.number_input("Kp", min_value=0.0, max_value=1000.0, step=0.1, key="Kp")
    Ki = st.number_input("Ki", min_value=0.0, max_value=1000.0, step=0.1, key="Ki")
    Kd = st.number_input("Kd", min_value=0.0, max_value=100.0, step=0.01, key="Kd")
    tau_f = st.number_input("tau_f [s]", min_value=1e-4, max_value=1.0,
                            step=0.001, format="%.4f", key="tau_f")

    st.subheader("Simulacion")
    ref = st.number_input("Setpoint", step=0.5, key="ref")
    t_final = st.number_input("Tiempo final [s]", min_value=0.1, max_value=60.0,
                              step=0.5, key="t_final")
    dt = st.number_input("dt [s]", min_value=1e-4, max_value=0.1,
                         step=0.001, format="%.4f", key="dt")
    u_min = st.number_input("u_min", step=1.0, key="u_min")
    u_max = st.number_input("u_max", step=1.0, key="u_max")

    st.subheader("Perturbacion")
    dist_enabled = st.checkbox("Aplicar perturbacion", key="dist_enabled")
    dist_t_step = st.number_input(
        "t_step [s]", min_value=0.0, max_value=60.0, step=0.5,
        key="dist_t_step", disabled=not dist_enabled,
    )
    dist_magnitude = st.number_input(
        "magnitud", step=0.1, key="dist_magnitude",
        disabled=not dist_enabled,
    )

    st.divider()
    simulate_btn = st.button("Simular", type="primary", use_container_width=True)
# === MAIN ===
current_snapshot = (
    model_name,
    tuple(sorted(params.items())),
    float(Kp), float(Ki), float(Kd), float(tau_f),
    float(ref), float(t_final), float(dt), float(u_min), float(u_max),
    bool(dist_enabled), float(dist_t_step), float(dist_magnitude),
)

if simulate_btn:
    ctrl = PIDController(Kp=Kp, Ki=Ki, Kd=Kd, tau_f=tau_f,
                         u_min=u_min, u_max=u_max, dt=dt)
    model = build_model(model_name, params)
    dist_fn = None
    if dist_enabled:
        dist_fn = lambda t, _m=dist_magnitude, _t=dist_t_step: _m if t >= _t else 0.0
    with st.spinner("Simulando..."):
        result = simulate(model, ctrl, ref=ref, t_final=t_final, dt=dt,
                          disturbance=dist_fn)
    st.session_state["result"] = result
    st.session_state["result_snapshot"] = current_snapshot
    st.session_state["result_model"] = model
    st.session_state["result_model_name"] = model_name

result = st.session_state.get("result")
saved_snapshot = st.session_state.get("result_snapshot")

tab_sim, tab_analysis, tab_learn = st.tabs(["Simulacion", "Analisis", "Aprender"])

with tab_sim:
    if result is None:
        st.info("Configura el sistema en el sidebar y presiona **Simular**.")
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
            st.dataframe(pole_data, use_container_width=True)

        st.subheader("Plano complejo")
        st.plotly_chart(poles_chart(poles), use_container_width=True)

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