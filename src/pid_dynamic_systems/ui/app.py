"""Streamlit app para PID & Dynamic Systems."""

from __future__ import annotations

import streamlit as st

from pid_dynamic_systems.ui.state import (
    MODEL_REGISTRY, build_model, init_session_state,
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

with st.sidebar:
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

    st.divider()
    simulate_btn = st.button("Simular", type="primary", use_container_width=True)

st.header("Estado actual")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Modelo")
    st.write(f"**{model_name}**")
    st.caption(MODEL_REGISTRY[model_name]["description"])
    st.write("**Parametros fisicos:**")
    for k, v in params.items():
        unit = MODEL_REGISTRY[model_name]["params"][k]["unit"]
        st.write(f"- {k} = {v} [{unit}]")

with col2:
    st.subheader("Controlador PID")
    st.write(f"- Kp = {Kp}")
    st.write(f"- Ki = {Ki}")
    st.write(f"- Kd = {Kd}")
    st.write(f"- tau_f = {tau_f} [s]")
    st.subheader("Simulacion")
    st.write(f"- Setpoint = {ref}")
    st.write(f"- t_final = {t_final} [s]")
    st.write(f"- dt = {dt} [s]")
    st.write(f"- u in [{u_min}, {u_max}]")

if simulate_btn:
    model = build_model(model_name, params)
    st.success(
        f"Simulacion solicitada: {model_name} | ref={ref} | "
        f"t_final={t_final} | dt={dt}"
    )
    st.info("Graficas y metricas llegan en Fase 4.2 (siguiente bloque).")
