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

from pid_dynamic_systems.controllers.pid import PIDController
from pid_dynamic_systems.simulation.engine import simulate


@st.cache_data(show_spinner=False)
def cached_simulate(
    model_name: str,
    params_tuple: tuple[tuple[str, float], ...],
    Kp: float, Ki: float, Kd: float, tau_f: float,
    ref: float, t_final: float, dt: float,
    u_min: float, u_max: float,
    dist_enabled: bool, dist_t_step: float, dist_magnitude: float,
):
    """Wrapper hasheable de simulate() para @st.cache_data.

    Reconstruye modelo + controlador adentro porque los objetos
    no son hasheables. Devuelve el SimulationResult (que si lo es
    una vez calculado; Streamlit lo serializa via pickle).
    """
    params = dict(params_tuple)
    model = build_model(model_name, params)
    ctrl = PIDController(Kp=Kp, Ki=Ki, Kd=Kd, tau_f=tau_f,
                         u_min=u_min, u_max=u_max, dt=dt)
    dist_fn = None
    if dist_enabled:
        dist_fn = lambda t, _m=dist_magnitude, _t=dist_t_step: _m if t >= _t else 0.0
    return simulate(model, ctrl, ref=ref, t_final=t_final, dt=dt,
                    disturbance=dist_fn)
# === Textos de ayuda para tooltips de parametros ===
HELP_TEXTS = {
    # --- PID ---
    "Kp": "Ganancia proporcional. Aumentar Kp = respuesta mas rapida y mas overshoot. Puede causar inestabilidad si es muy alto.",
    "Ki": "Ganancia integral. Elimina el error estacionario (offset). Si es muy alto puede causar oscilaciones lentas.",
    "Kd": "Ganancia derivativa. Amortigua el sobreimpulso. Si es muy alto amplifica ruido de medicion.",
    "tau_f": "Constante de tiempo del filtro de derivada. Mas grande = derivada mas suave pero menos reactiva. Tipico: 0.01 s.",
    # --- Simulacion ---
    "ref": "Setpoint: el valor que quieres que el sistema alcance.",
    "t_final": "Duracion total de la simulacion en segundos.",
    "dt": "Paso de integracion. Mas pequeno = mas preciso pero mas lento. Tipico: 0.001 s.",
    "u_min": "Limite inferior del actuador. El controlador no puede dar valores menores.",
    "u_max": "Limite superior del actuador. El controlador no puede dar valores mayores.",
    "dist_t_step": "Instante (s) en que se aplica el escalon de perturbacion.",
    "dist_magnitude": "Magnitud del escalon de perturbacion (sumada a la entrada).",
    # --- Modelos ---
    "R": "Resistencia. En motor: de armadura (Ohm). En termico: resistencia termica (K/W).",
    "L": "Inductancia de armadura (H). Afecta que tan rapido responde la corriente.",
    "J": "Inercia del rotor (kg.m^2). Mas inercia = respuesta mas lenta.",
    "B": "Friccion viscosa (N.m.s/rad). Disipa energia, amortigua.",
    "Kt": "Constante de torque (N.m/A). Relaciona corriente con par mecanico.",
    "Ke": "Constante electromotriz (V.s/rad). Relaciona velocidad con voltaje inducido.",
    "C": "Capacidad termica (J/K). Energia necesaria para subir 1 K de temperatura.",
    "T_amb_ref": "Temperatura ambiente de referencia (K). 293.15 K = 20 C.",
    "m": "Masa del cuerpo (kg). Afecta la inercia del sistema.",
    "c": "Amortiguamiento viscoso (N.s/m). Disipa energia.",
    "k": "Rigidez del resorte (N/m). Que tan duro es el resorte.",
}

# === Intro de cada modelo (que es y para que sirve) ===
MODEL_INTRO = {
    "Motor DC": "Sistema electromecanico que regula la velocidad angular de un motor mediante el voltaje aplicado. Clasico en robotica y control industrial.",
    "Sistema termico": "Cuerpo con capacidad termica que intercambia calor con el ambiente. Ejemplo: control de temperatura en un horno.",
    "Masa-resorte-amortiguador": "Sistema mecanico de segundo orden. Ejemplo clasico: suspension de un vehiculo o posicionamiento de precision.",
}

# === Presets: ejemplos listos para cargar ===
PRESETS = {
    "DC - respuesta ideal": {
        "model_name": "Motor DC",
        "Kp": 2.0, "Ki": 5.0, "Kd": 0.0, "tau_f": 0.01,
        "ref": 10.0, "t_final": 5.0, "dt": 0.001,
        "desc": "PI sintonizado: converge rapido sin overshoot severo.",
    },
    "DC - overshoot alto": {
        "model_name": "Motor DC",
        "Kp": 10.0, "Ki": 20.0, "Kd": 0.0, "tau_f": 0.01,
        "ref": 10.0, "t_final": 5.0, "dt": 0.001,
        "desc": "Kp alto: respuesta rapida pero con sobreimpulso grande.",
    },
    "Termico - control tipico": {
        "model_name": "Sistema termico",
        "Kp": 100.0, "Ki": 10.0, "Kd": 0.0, "tau_f": 0.01,
        "ref": 320.0, "t_final": 300.0, "dt": 0.01,
        "desc": "Control de temperatura con escalon de 20 C.",
    },
    "MSD - amortiguado": {
        "model_name": "Masa-resorte-amortiguador",
        "Kp": 10.0, "Ki": 5.0, "Kd": 2.0, "tau_f": 0.01,
        "ref": 1.0, "t_final": 10.0, "dt": 0.001,
        "desc": "PID con Kd para amortiguar el segundo orden.",
    },
}