# PID & Dynamic Systems

> Laboratorio interactivo para el estudio de sistemas dinamicos y controladores PID.

[![Tests](https://img.shields.io/badge/tests-59%20passed-brightgreen)](https://github.com/OballenEC/pid-dynamic-systems)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Simulador educativo de control automatico. Implementa tres sistemas fisicos
(motor de CD, sistema termico y masa-resorte-amortiguador), un controlador
PID discreto con derivada filtrada y anti-windup, y una interfaz web
interactiva con analisis de estabilidad y explicaciones pedagogicas.

---

## Caracteristicas

- **3 modelos fisicos** con interface comun, simulacion generica
- **PID discreto** con derivada filtrada (primer orden) y anti-windup
- **Motor de simulacion ZOH** paso a paso (respeta el caracter discreto del controlador)
- **Metricas** de respuesta temporal: rise time, settling, overshoot, SSE, ISE
- **Analisis de estabilidad** por polos del lazo cerrado
- **UI Streamlit** con 3 tabs: Simulacion / Analisis / Aprender
- **Modulo educativo** con explicaciones generadas dinamicamente
- **Reporte PDF** descargable con parametros, graficas, metricas e interpretacion
- **59 tests** unitarios (validados contra soluciones analiticas)

---

## Instalacion rapida

```powershell
git clone https://github.com/OballenEC/pid-dynamic-systems.git
cd "pid-dynamic-systems"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

---

## Uso

```powershell
streamlit run src\pid_dynamic_systems\ui\app.py
```

Se abre en `http://localhost:8501`. Selecciona un modelo, ajusta los
parametros del PID, presiona **Simular** y explora los tres tabs.

Ver [`docs/user_manual.md`](docs/user_manual.md) para instrucciones detalladas.

---

## Modelos implementados

### Motor de CD
Control de velocidad angular. Estados: `[i, omega]`. Entrada: voltaje `v`.
FT: `Kt / (L*J*s^2 + (L*B+R*J)*s + (R*B+Kt*Ke))`.

### Sistema termico
Control de temperatura. Estado: `[T]`. Entrada: potencia `Q_in`.
FT: `R / (R*C*s + 1)`.

### Masa-resorte-amortiguador
Control de posicion. Estados: `[x, v]`. Entrada: fuerza `F`.
FT: `1 / (m*s^2 + c*s + k)`.

Detalle matematico completo en [`docs/mathematical_models.md`](docs/mathematical_models.md).

---

## Arquitectura

```
src/pid_dynamic_systems/
  models/         # 3 modelos fisicos (dominio puro)
  controllers/    # PID discreto (dominio puro)
  simulation/     # Motor ZOH (dominio puro)
  analysis/       # Metricas + estabilidad (dominio puro)
  ui/             # Streamlit + Plotly
  report/         # ReportLab + matplotlib
tests/unit/       # 10 archivos, 59 tests
```

**Regla:** `models`, `controllers`, `simulation`, `analysis` no
importan `streamlit`, `plotly` ni `reportlab`. La logica es
independiente de la presentacion.

Decisiones de diseno completas en [`docs/technical_documentation.md`](docs/technical_documentation.md).

---

## Stack

| Capa | Tecnologia |
|---|---|
| Lenguaje | Python 3.10+ |
| Numerico | numpy, scipy |
| Control | python-control |
| UI | Streamlit, Plotly |
| Reportes | ReportLab, matplotlib |
| Tests | pytest |
| Deploy | Streamlit Cloud |

---

## Tests

```powershell
python -m pytest -v
```

**59 tests** cubriendo modelos, PID, simulacion, metricas, estabilidad,
graficas, explicaciones y generacion de PDF. Todos validan contra
soluciones analiticas conocidas (no solo no-regresion).

---

## Documentacion

- [`docs/mathematical_models.md`](docs/mathematical_models.md) - Modelos fisicos, ecuaciones, FTs, parametros
- [`docs/technical_documentation.md`](docs/technical_documentation.md) - Arquitectura, decisiones, ZOH, PID, testing
- [`docs/user_manual.md`](docs/user_manual.md) - Guia de instalacion y uso
- [`HANDOFF.md`](HANDOFF.md) - Contexto completo para continuidad del proyecto

---

## Licencia

MIT. Ver [`LICENSE`](LICENSE).

---

## Autor

**Oscar Ballen** - Estudiante de Ingenieria en Telecomunicaciones, Sistemas y Electronica (ITSE)  
UNAM FES Cuautitlan