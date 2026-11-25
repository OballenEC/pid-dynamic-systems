# Documentacion tecnica

Este documento describe la arquitectura del proyecto, las decisiones de
diseno principales y las justificaciones detras de cada una. Su
objetivo es que otro ingeniero (o el autor en el futuro) pueda entender
por que el codigo esta estructurado como esta, sin tener que leer todo
el codigo fuente primero.

---

## 1. Arquitectura general

El proyecto sigue una separacion estricta entre logica de dominio y
presentacion:

```
src/pid_dynamic_systems/
  models/          # Modelos fisicos (dominio puro, sin Streamlit)
  controllers/     # PID discreto (dominio puro)
  simulation/      # Motor de simulacion (dominio puro)
  analysis/        # Metricas y estabilidad (dominio puro)
  ui/              # Streamlit (unica capa que importa plotly/streamlit)
  report/          # Generacion de PDF (importa reportlab/matplotlib)
tests/
  unit/            # 10 archivos de test, 59 tests
  integration/     # Reservado para futuras pruebas end-to-end
```

**Regla dura:** ningun modulo dentro de `models/`, `controllers/`,
`simulation/` o `analysis/` importa `streamlit`, `plotly` ni
`reportlab`. Esta regla se verifica mirando los imports de esos
archivos.

**Beneficio:** los tests de logica no dependen de la UI. Si Streamlit
cambia de API o si migramos la UI a FastAPI en el futuro, la logica no
se toca.

---

## 2. Contrato de modelos

Todos los modelos implementan la misma interface:

| Miembro | Tipo | Proposito |
|---|---|---|
| `state_names` | `list[str]` (property) | Nombres de los estados |
| `input_names` | `list[str]` (property) | Nombres de entradas `[control, perturbacion]` |
| `output_index` | `int` (property) | Indice del estado que se controla |
| `derivatives(t, x, u)` | `np.ndarray` | RHS del sistema de EDOs |
| `transfer_function()` | `(num, den)` | Coeficientes de la FT |
| `dc_gain()` | `float` | Ganancia en frecuencia cero |
| `steady_state_from_*()` | `tuple` o `float` | Estado de equilibrio para entrada dada |

**Beneficio:** el motor de simulacion, el PID y las metricas son
genericos. Agregar un cuarto modelo (ej. pendulo invertido) solo
requiere implementar la interface, no tocar el resto.

---

## 3. Controlador PID discreto

### 3.1 Por que discreto y no continuo

El PID se implementa como **ecuacion en diferencias**, no como
ecuacion diferencial. Razon: en la practica industrial, el controlador
corre en un microcontrolador con periodo de muestreo fijo. Un PID
continuo es una abstraccion matematica que no respeta esta realidad.

### 3.2 Derivada filtrada

La derivada pura `(e[k] - e[k-1]) / dt` amplifica ruido de medicion.
Se aplica un filtro pasa-bajos de primer orden:

```
d_raw[k] = (e[k] - e[k-1]) / dt
d_f[k]   = alpha * d_raw[k] + (1 - alpha) * d_f[k-1]
alpha    = dt / (tau_f + dt)
```

Con `tau_f = 0.01 s` (por defecto), el filtro suaviza variaciones
rapidas de error sin perder la accion derivativa sobre tendencias
lentas.

**Detalle:** en el primer paso (`k=0`), no existe `e[k-1]`, y usar
`e[-1] = 0` produce un spike artificial. El codigo setea `d_raw = 0`
en el primer paso para evitarlo.

### 3.3 Anti-windup

Sin anti-windup, la integral crece indefinidamente cuando el actuador
esta saturado. Al salir de saturacion, el termino integral enorme
provoca sobreimpulso severo.

Se usa **clamping condicional**:

```
if u_raw == u_sat:  # NO saturado
    I[k] = I[k-1] + Ki * e[k] * dt
else:               # saturado
    I[k] = I[k-1]   # no acumular
```

Es mas simple que back-calculation y suficiente para este proyecto.
---

## 4. Motor de simulacion: ZOH paso a paso

### 4.1 Por que no `solve_ivp` con `t_eval`

La forma naive seria:

```python
t_eval = np.linspace(0, t_final, n_steps)
def rhs(t, x): 
    return model.derivatives(t, x, [pid.step(ref - x[idx]), dist])
sol = solve_ivp(rhs, (0, t_final), x0, t_eval=t_eval)
```

Problema: el PID tiene **estado interno** (integral, derivada previa)
y su salida no es una funcion continua de `x`. `solve_ivp` evalua el
`rhs` en puntos arbitrarios (no necesariamente en `t_eval`), lo que
haria que el PID se actualice multiples veces por paso, rompiendo la
coherencia entre `u` y el avance temporal.

### 4.2 Solucion: ZOH paso a paso

```
for k in range(n_steps - 1):
    e = ref - y[k]
    u = pid.step(e, dt)       # actualizar PID una vez por paso
    sol = solve_ivp(rhs_con_u_fija, (t[k], t[k+1]), x)
    x = sol.y[:, -1]
    y[k+1] = x[output_index]
```

Entre `t[k]` y `t[k+1]`, la senal `u` se mantiene constante
(**Zero-Order Hold**). El integrador solo ve la dinamica del modelo, no
la del PID. Esto respeta el caracter discreto del controlador y es el
comportamiento real de un sistema con actuador digital.

---

## 5. Metricas de respuesta temporal

Las funciones en `analysis/metrics.py` son **puras** (sin estado) y
reciben `y_ss` como argumento explicito, no lo calculan con `y[-1]`.

**Razon:** en sistemas con oscilacion sostenida o con perturbacion al
final de la simulacion, `y[-1]` no coincide con el estado estacionario
real. Forzar al caller a pasar `y_ss` evita errores silenciosos.

Metricas implementadas:

| Metrica | Definicion | Metodo |
|---|---|---|
| Rise time | t(90%) - t(10%) | Interpolacion lineal entre muestras |
| Settling time | Ultimo t fuera de +-2% | Busqueda inversa del ultimo cruce |
| Overshoot | (y_max - y_ss)/y_ss * 100 | Maximo de la respuesta |
| SSE | \|ref - y_ss\| | Diferencia directa |
| ISE | Integral de e^2 dt | Trapecio (`np.trapezoid`) |

Todas tienen tests unitarios con casos analiticos conocidos (ej. primer
orden: `tr = 2.197 s`, `ts = 3.912 s`).

---

## 6. Estabilidad: polos del lazo cerrado

### 6.1 Por que no `control.feedback`

El PID ideal continuo es `C(s) = (Kd*s^2 + Kp*s + Ki)/s`, que es
**impropio** (grado del numerador > grado del denominador). Algunas
versiones de `control` rechazan TFs impropias, lo que rompe la
portabilidad.

### 6.2 Solucion: algebra polinomial directa

La FT del lazo cerrado es:

```
       G*C
T(s) = -----
       1+G*C
     = num_G * num_C
       -------------------------
       den_G * den_C + num_G * num_C
```

Los polos son las raices del denominador:

```python
num_cl = np.convolve(num_G, num_C)
den_cl = np.polyadd(np.convolve(den_G, den_C), num_cl)
poles = np.roots(den_cl)
```

**Ventaja:** funciona para cualquier combinacion modelo + PID, sin
depender de `control.tf`. Ademas, es exactamente lo que `control`
hace internamente cuando no rechaza la TF.

### 6.3 Analisis de estabilidad

- **Estable:** todos los polos tienen `Re < 0`
- **Margen:** si el polo dominante tiene `Re > -0.1`, se reporta como
  "margen pequeno"
- **Amortiguamiento:** `zeta = -Re(p) / |p|` por polo
- **Frecuencia natural:** `wn = |p|`

---

## 7. Estrategia de testing

**Cobertura:** 59 tests unitarios distribuidos:

| Modulo | Tests | Tipo |
|---|---|---|
| `test_dc_motor.py` | 4 | Modelo + FT + DC gain |
| `test_thermal.py` | 6 | Modelo + FT + constante de tiempo |
| `test_msd.py` | 6 | Modelo + FT + wn/zeta |
| `test_pid.py` | 7 | P/I/D + saturacion + anti-windup |
| `test_engine.py` | 6 | Simulacion + casos analiticos |
| `test_metrics.py` | 6 | Metricas vs soluciones analiticas |
| `test_stability.py` | 7 | Polos + estabilidad |
| `test_plotly_charts.py` | 3 | Estructura de figuras |
| `test_stability_plots.py` | 3 | Polos + step + Bode |
| `test_explanations.py` | 8 | Texto dinamico |
| `test_pdf_generator.py` | 3 | PDF valido (header + EOF) |

**Filosofia:** tests contra **soluciones analiticas conocidas**, no
contra outputs previos del codigo. Un test que solo verifica "el codigo
produce lo mismo que antes" no prueba correccion, solo no-regresion.

Ejemplo: `test_p_control_reaches_analytic_steady_state` verifica que
un P puro converge a `y_ss = G0*Kp*ref / (1 + G0*Kp)`, formula
derivada de control clasico. Si el motor de simulacion, el modelo o el
PID tienen bugs, este test falla.