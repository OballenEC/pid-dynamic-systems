"""Tests de los diccionarios de ayuda y presets de la UI."""

from __future__ import annotations

from pid_dynamic_systems.models.dc_motor import DCMotor
from pid_dynamic_systems.models.mass_spring_damper import MassSpringDamper
from pid_dynamic_systems.models.thermal import ThermalSystem
from pid_dynamic_systems.ui.state import HELP_TEXTS, MODEL_INTRO, MODEL_REGISTRY, PRESETS


def test_all_model_params_have_help_text() -> None:
    """Cada parametro fisico debe tener texto de ayuda."""
    for model_name, meta in MODEL_REGISTRY.items():
        for pname in meta["params"]:
            assert pname in HELP_TEXTS, f"Falta help para {pname} (modelo {model_name})"
            assert len(HELP_TEXTS[pname]) > 10, f"Help muy corto para {pname}"


def test_all_models_have_intro() -> None:
    """Cada modelo debe tener descripcion introductoria."""
    for model_name in MODEL_REGISTRY:
        assert model_name in MODEL_INTRO, f"Falta intro para {model_name}"
        assert len(MODEL_INTRO[model_name]) > 30


def test_pid_and_sim_params_have_help() -> None:
    """Los parametros del PID y simulacion tambien deben tener help."""
    for key in ("Kp", "Ki", "Kd", "tau_f", "ref", "t_final", "dt",
                "u_min", "u_max", "dist_t_step", "dist_magnitude"):
        assert key in HELP_TEXTS, f"Falta help para {key}"


def test_all_presets_reference_valid_model() -> None:
    """Cada preset debe referenciar un modelo registrado."""
    for preset_name, p in PRESETS.items():
        assert "model_name" in p, f"Preset {preset_name} sin model_name"
        assert p["model_name"] in MODEL_REGISTRY, \
            f"Preset {preset_name} referencia modelo inexistente: {p['model_name']}"


def test_all_presets_have_required_pid_params() -> None:
    """Cada preset debe tener Kp, Ki, Kd, ref, t_final."""
    for preset_name, p in PRESETS.items():
        for key in ("Kp", "Ki", "Kd", "ref", "t_final"):
            assert key in p, f"Preset {preset_name} sin {key}"
            assert isinstance(p[key], (int, float)), \
                f"Preset {preset_name}: {key} no es numerico"


def test_preset_params_are_physical() -> None:
    """Los valores de los presets deben ser fisicamente razonables."""
    for preset_name, p in PRESETS.items():
        assert p["Kp"] >= 0, f"Preset {preset_name}: Kp negativo"
        assert p["Ki"] >= 0, f"Preset {preset_name}: Ki negativo"
        assert p["Kd"] >= 0, f"Preset {preset_name}: Kd negativo"
        assert p["t_final"] > 0, f"Preset {preset_name}: t_final <= 0"