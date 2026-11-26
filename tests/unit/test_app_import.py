"""Smoke test: app.py debe importar sin NameError en runtime."""
from __future__ import annotations


def test_app_module_imports_without_nameerror() -> None:
    import pid_dynamic_systems.ui.app  # noqa: F401
