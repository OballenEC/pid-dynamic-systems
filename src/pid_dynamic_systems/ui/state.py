"""Estado de sesion y registro de modelos para la UI."""

from __future__ import annotations

import streamlit as st

from pid_dynamic_systems.models.dc_motor import DCMotor
from pid_dynamic_systems.models.mass_spring_damper import MassSpringDamper
from pid_dynamic_systems.models.thermal import ThermalSystem


MODEL_REGISTRY = {
    "Motor DC": {
        "class": DCMotor,
        "description": "Control de velocidad angular de un motor electrico de CD.",
        "params": {
            "R": {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1, "unit": "Ohm"},
            "L": {"default": 0.5, "min": 0.01, "max": 5.0, "step": 0.01, "unit": "H"},
            "J": {"default": 0.01, "min": 0.001, "max": 1.0, "step": 0.001, "unit": "kg.m^2"},
            "B": {"default": 0.1, "min": 0.001, "max": 5.0, "step": 0.001, "unit": "N.m.s/rad"},
            "Kt": {"default": 0.1, "min": 0.01, "max": 1.0, "step": 0.01, "unit": "N.m/A"},
            "Ke": {"default": 0.1, "min": 0.01, "max": 1.0, "step": 0.01, "unit": "V.s/rad"},
        },
        "output": "omega [rad/s]",
        "input": "v [V]",
    },
    "Sistema termico": {
        "class": ThermalSystem,
        "description": "Control de temperatura en un cuerpo con capacidad termica.",
        "params": {
            "R": {"default": 0.1, "min": 0.01, "max": 5.0, "step": 0.01, "unit": "K/W"},
            "C": {"default": 1000.0, "min": 10.0, "max": 10000.0, "step": 10.0, "unit": "J/K"},
            "T_amb_ref": {"default": 293.15, "min": 250.0, "max": 350.0, "step": 0.5, "unit": "K"},
        },
        "output": "T [K]",
        "input": "Q_in [W]",
    },
    "Masa-resorte-amortiguador": {
        "class": MassSpringDamper,
        "description": "Control de posicion de una masa con resorte y amortiguador.",
        "params": {
            "m": {"default": 1.0, "min": 0.1, "max": 20.0, "step": 0.1, "unit": "kg"},
            "c": {"default": 2.0, "min": 0.0, "max": 20.0, "step": 0.1, "unit": "N.s/m"},
            "k": {"default": 10.0, "min": 0.1, "max": 100.0, "step": 0.1, "unit": "N/m"},
        },
        "output": "x [m]",
        "input": "F [N]",
    },
}

DEFAULT_PID = {"Kp": 1.0, "Ki": 1.0, "Kd": 0.0, "tau_f": 0.01}
DEFAULT_SIM = {"ref": 10.0, "t_final": 10.0, "dt": 0.001,
               "u_min": -1000.0, "u_max": 1000.0}
DEFAULT_DIST = {"enabled": False, "t_step": 2.0, "magnitude": 0.0}


def _default(key: str, value) -> None:
    """Setea session_state[key] solo si no existe (idempotente)."""
    if key not in st.session_state:
        st.session_state[key] = value


def init_session_state() -> None:
    """Inicializa session_state con valores por defecto. Idempotente."""
    _default("model_name", "Motor DC")
    _default("result", None)
    for k, v in DEFAULT_PID.items():
        _default(k, v)
    for k, v in DEFAULT_SIM.items():
        _default(k, v)
    for k, v in DEFAULT_DIST.items():
        _default(k, v)


def build_model(model_name: str, params: dict):
    """Construye la instancia del modelo con los parametros del sidebar."""
    cls = MODEL_REGISTRY[model_name]["class"]
    return cls(**params)
