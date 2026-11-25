# PID & Dynamic Systems — Handoff

## 0. Resumen

Plataforma de simulacion de 3 sistemas dinamicos con PID.
Stack: Python + numpy + scipy + control + streamlit + plotly + pytest.

**Estado:** Fases 0, 1.1, 1.2, 1.3, 2, 3.1, 3.2 y 3.3 completas. Pendientes 4, 5.
## 1. Preferencias del desarrollador (CRITICO)

- **TODO por PowerShell.** Bloques copy-paste listos para ejecutar:
  creacion de archivos, instalacion, tests, git. Nada de abrir archivos
  en VS Code a mano.
- **Bloques cortos (maximo 40 lineas).** Bloques de 130+ lineas se
  truncan al pegar en la terminal. Partir siempre.
- **Verificacion por fase** antes de continuar (pytest debe dar
  `X passed`).
- **Docstrings en espanol sin acentos** (encoding en PowerShell).
- **Modularidad:** modelos / controladores / simulacion / analisis /
  ui / report. Los modelos NO importan streamlit ni plotly.
- **Un commit por fase** (`feat:`, `docs:`, `chore:`, `test:`).
- **Idioma:** identificadores de codigo en ingles, docstrings y
  comentarios en espanol.

## 2. Entorno

| Item | Valor |
|---|---|
| SO | Windows + PowerShell + VS Code |
| Python | 3.14 |
| Venv | `.venv\` en la raiz del proyecto |
| Ruta | `C:\Users\Home\Desktop\PYTHON\PROJECTS\PID & Dynamic Systems` |
| Deps | numpy scipy control streamlit plotly pytest reportlab |

Instalar con: `pip install -e ".[dev]"`

Cuidado: la ruta tiene espacios y `&`, usar comillas al `cd`:

```powershell
cd "C:\Users\Home\Desktop\PYTHON\PROJECTS\PID & Dynamic Systems"
.\.venv\Scripts\Activate.ps1
```

## 3. Estructura

```text
src/pid_dynamic_systems/
  models/           # dc_motor.py, thermal.py, mass_spring_damper.py (OK)
  controllers/      # pid.py (OK)
  simulation/       # engine.py (OK)
  analysis/         # metrics.py (PEND)
  ui/               # app.py (PEND)
  report/           # pdf_generator.py (PEND)
tests/
  unit/             # dc_motor, thermal, msd, pid, engine (OK)
  integration/
```

## 4. Interface de modelos (contrato interno)

Cada modelo debe ser `@dataclass` con:

- `state_names` -> list[str]              (property)
- `input_names` -> list[str]              (property, [entrada_control, perturbacion])
- `output_index` -> int                   (property, indice del estado controlado)
- `derivatives(t, x, u) -> np.ndarray`
- `transfer_function() -> (num, den)`
- `dc_gain() -> float`
- `steady_state_from_<input>(...) -> ...`

Permite que controlador, simulador y metricas traten cualquier modelo
de forma generica.

## 5. Modelos matematicos

### 5.1 Motor DC (COMPLETO en models/dc_motor.py)

```text
L di/dt  = v - R*i - Ke*omega
J domega/dt = Kt*i - B*omega - tau_L
```

FT: `Kt / (L*J*s^2 + (L*B + R*J)*s + (R*B + Kt*Ke))`

Parametros (SI): R=1 Ohm, L=0.5 H, J=0.01 kg*m^2, B=0.1 N*m*s/rad,
Kt=0.1 N*m/A, Ke=0.1 V*s/rad.

Entrada: `v` [V]. Perturbacion: `tau_L` [N*m]. Salida: `omega` [rad/s].
Estado: `[i, omega]`. Ganancia DC: `0.909 rad/s/V`.

### 5.2 Sistema termico (COMPLETO en models/thermal.py)

```text
C dT/dt = (T_amb - T)/R + Q_in
```

FT: `R / (R*C*s + 1)`

Parametros (SI): R=0.1 K/W, C=1000 J/K, tau=RC=100 s.

Entrada: `Q_in` [W]. Perturbacion: `T_amb` [K]. Salida: `T` [K].
Estado: `[T]`. Ganancia DC: `R = 0.1 K/W`. Polo: `-1/RC = -0.01`.

### 5.3 Masa-resorte-amortiguador (COMPLETO en models/mass_spring_damper.py)

```text
m*x'' + c*x' + k*x = F + F_dist
```

FT: `1 / (m*s^2 + c*s + k)`

Parametros (SI): m=1 kg, c=2 N*s/m, k=10 N/m. wn=3.162 rad/s,
zeta=0.316 (subamortiguado).

Entrada: `F` [N]. Perturbacion: `F_dist` [N]. Salida: `x` [m].
Estado: `[x, v]`. Ganancia DC: `1/k = 0.1 m/N`.

## 6. Controlador PID (Fase 2)

Ecuacion discreta:

```text
u[k] = Kp*e[k] + I[k] + Kd*(e[k] - e[k-1])/dt
```

Derivada filtrada (paso-bajos primer orden):

```text
d_raw[k] = (e[k] - e[k-1]) / dt
d_f[k]   = alpha * d_raw[k] + (1-alpha) * d_f[k-1]
alpha    = dt / (tau_f + dt)
```

Anti-windup (clamping condicional):

```text
if not saturated:
    I[k] = I[k-1] + Ki*e[k]*dt
else:
    I[k] = I[k-1]
```

Saturacion: `u_sat[k] = clip(u_raw[k], u_min, u_max)`

Interfaz:

```python
@dataclass
class PIDController:
    Kp: float
    Ki: float
    Kd: float
    tau_f: float = 0.01
    u_min: float = -inf
    u_max: float = +inf
    dt: float = 0.001

    def reset(self) -> None: ...
    def step(self, error: float, dt: float | None = None) -> float: ...
```

## 7. Simulacion y metricas (Fase 3)

**Diseno: ZOH paso a paso.** El PID es discreto; se actualiza cada dt y entre updates u es constante. Ver engine.py.
Para cada intervalo [t_k, t_k+1]: e_k = ref - y_k; u_k = pid.step(e_k, dt); solve_ivp integra con u_k fijo; y_{k+1} = x_{k+1}[output_index].
Respetando anti-windup y derivada filtrada del PID discreto.
Metricas en analysis/metrics.py (Fase 3.2).
Metricas a calcular:

| Metrica | Definicion |
|---|---|
| Rise time | 10% -> 90% del valor final |
| Settling time | banda +-2% del valor final |
| Sobreimpulso | (y_max - y_ss)/y_ss * 100 |
| Error estacionario | abs(ref - y_ss) |
| ISE | trapz(e(t)^2, t) |
| Esfuerzo de control | trapz(u(t)^2, t) |
| Polos | eigvals de la linealizacion en lazo cerrado |

## 8. Roadmap

| Fase | Contenido | Estado |
|---|---|---|
| 0   | venv, deps, estructura, pyproject, git+github | COMPLETA |
| 1.1 | models/dc_motor.py + 4 tests | COMPLETA |
| 1.2 | models/thermal.py + 6 tests | COMPLETA |
| 1.3 | models/mass_spring_damper.py + 6 tests | COMPLETA |
| 2   | controllers/pid.py + 7 tests | COMPLETA |
| 3   | simulation/engine.py + analysis/metrics.py | COMPLETA (3.1 + 3.2 + 3.3) |
| 4   | ui/app.py (Streamlit + Plotly) | PENDIENTE |
| 5   | report/pdf_generator.py (ReportLab) | PENDIENTE |

## 9. Gotchas

1. **Ruta con `&` y espacios:** siempre `cd "..."` con comillas.
2. **`.venv` en la raiz**, no en subcarpeta. Verificar con:
   `python -c "import sys; print(sys.executable)"` -> debe terminar
   en `PID & Dynamic Systems\.venv\Scripts\python.exe` (sin subnivel).
3. **`gh` se instala con** `winget install --id GitHub.cli`. Cerrar
   y reabrir VS Code despues para refrescar PATH.
4. **Bloques >40 lineas se truncan** al pegar en la terminal. Partir
   siempre en bloques pequenos.
5. **Ejecucion de scripts:** si `Activate.ps1` es bloqueado,
   `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
6. **`pyproject.toml` usa `pythonpath = ["src"]`**, asi pytest encuentra
   el paquete sin instalar.

## 10. Comandos utiles

```powershell
# Activar
cd "C:\Users\Home\Desktop\PYTHON\PROJECTS\PID & Dynamic Systems"
.\.venv\Scripts\Activate.ps1

# Tests
python -m pytest -v
python -m pytest tests\unit\test_dc_motor.py -v

# Git
git add .
git status
git commit -m "feat(models): descripcion"
git push

# Reinstalar deps
pip install -e ".[dev]"
```

## 11. Instrucciones para el LLM que recibe este documento

Si eres el asistente que recibe este handoff:

1. Respeta PowerShell-total. Bloques listos para copy-paste,
   incluyendo creacion de archivos, tests y git.

2. Bloques de maximo 40 lineas. Los mas largos se truncan en la
   terminal. Numerar los bloques y verificar despues de cada uno.

3. Continua por la fase pendiente de menor numero (1.2 -> 1.3 ->
   2 -> 3 -> 4 -> 5). Pregunta al usuario en que fase esta antes de
   asumir.

4. Manten la interface de modelos de la seccion 4.

5. Un commit por fase. Entregar git add + commit + push.

6. Verifica con pytest antes de cerrar cada fase. Indicar la
   salida esperada (X passed).

7. No introduzcas dependencias nuevas sin justificar.

Bienvenido al proyecto. Pregunta al usuario en que fase esta.






