# Modelos matematicos

Este documento describe los tres sistemas fisicos implementados en el
proyecto. Para cada uno se presenta la ecuacion diferencial que rige su
dinamica, su funcion de transferencia derivada, los parametros con
unidades SI, y las propiedades mas relevantes para el diseno del
controlador.

Todos los modelos implementan la misma interface (seccion 4 de
`HANDOFF.md`), lo que permite que el controlador PID, el motor de
simulacion y el modulo de metricas los traten de forma generica.

---

## 1. Motor electrico de CD

### 1.1 Ecuaciones dinamicas

Modelo de dos estados (corriente de armadura `i` y velocidad angular
`omega`):

```
L * di/dt     = v - R*i - Ke*omega
J * d(omega)/dt = Kt*i - B*omega - tau_L
```

donde `v` es el voltaje de armadura (entrada de control) y `tau_L` es
el par de carga (perturbacion externa).

### 1.2 Funcion de transferencia

Tomando transformada de Laplace con condiciones iniciales nulas y
despejando `omega(s)/v(s)`:

```
         omega(s)              Kt
G(s) = ------------ = -----------------------------------
             v(s)      L*J*s^2 + (L*B + R*J)*s + (R*B + Kt*Ke)
```

Es un sistema de **segundo orden**, tipo 0 (sin integrador natural).
Su ganancia DC es:

```
              Kt
G(0) = -----------------
        R*B + Kt*Ke
```

### 1.3 Parametros por defecto (SI)

| Parametro | Simbolo | Valor por defecto | Unidad |
|---|---|---|---|
| Resistencia de armadura | R | 1.0 | Ohm |
| Inductancia de armadura | L | 0.5 | H |
| Inercia del rotor | J | 0.01 | kg.m^2 |
| Friccion viscosa | B | 0.1 | N.m.s/rad |
| Constante de torque | Kt | 0.1 | N.m/A |
| Constante electromotriz | Ke | 0.1 | V.s/rad |

Con estos valores: `G(0) = 0.1 / (1*0.1 + 0.1*0.1) = 0.9091 rad/s/V`

### 1.4 Entradas y salidas

- Estado: `[i, omega]`
- Entrada de control: `v [V]`
- Perturbacion: `tau_L [N.m]`
- Salida controlada: `omega [rad/s]` (indice 0)
---

## 2. Sistema termico de primer orden

### 2.1 Ecuacion dinamica

Modelo de un cuerpo con capacidad termica `C` que intercambia calor
con el ambiente a traves de una resistencia termica `R`:

```
C * dT/dt = (T_amb - T)/R + Q_in
```

donde `Q_in` es la potencia de calentamiento (entrada de control) y
`T_amb` es la temperatura ambiente (perturbacion).

### 2.2 Funcion de transferencia

```
         T(s)            R
G(s) = -------- = -----------------
         Q(s)      R*C*s + 1
```

Sistema de **primer orden**, tipo 0. Ganancia DC: `G(0) = R`.
Constante de tiempo: `tau = R*C`. Polo unico en `s = -1/(R*C)`.

### 2.3 Parametros por defecto (SI)

| Parametro | Simbolo | Valor por defecto | Unidad |
|---|---|---|---|
| Resistencia termica | R | 0.1 | K/W |
| Capacidad termica | C | 1000.0 | J/K |
| Temperatura ambiente | T_amb_ref | 293.15 | K (20 C) |

Con estos valores: `G(0) = 0.1 K/W`, `tau = 100 s`, polo en `s = -0.01`.

### 2.4 Entradas y salidas

- Estado: `[T]`
- Entrada de control: `Q_in [W]`
- Perturbacion: `T_amb [K]`
- Salida controlada: `T [K]` (indice 0)

---

## 3. Masa-resorte-amortiguador

### 3.1 Ecuacion dinamica

Segunda ley de Newton sobre una masa `m` unida a un resorte de rigidez
`k` y un amortiguador viscoso `c`:

```
m * x''(t) + c * x'(t) + k * x(t) = F(t) + F_dist(t)
```

donde `F` es la fuerza aplicada (control) y `F_dist` es una fuerza
externa (perturbacion).

### 3.2 Funcion de transferencia

```
         X(s)              1
G(s) = -------- = ---------------------
         F(s)      m*s^2 + c*s + k
```

Sistema de **segundo orden**, tipo 0. Ganancia DC: `G(0) = 1/k`.

Forma canonica: `wn = sqrt(k/m)`, `zeta = c/(2*sqrt(k*m))`.

### 3.3 Parametros por defecto (SI)

| Parametro | Simbolo | Valor por defecto | Unidad |
|---|---|---|---|
| Masa | m | 1.0 | kg |
| Amortiguamiento | c | 2.0 | N.s/m |
| Rigidez | k | 10.0 | N/m |

Con estos valores: `wn = 3.162 rad/s`, `zeta = 0.316` (subamortiguado),
`G(0) = 0.1 m/N`.

### 3.4 Entradas y salidas

- Estado: `[x, v]` (posicion y velocidad)
- Entrada de control: `F [N]`
- Perturbacion: `F_dist [N]`
- Salida controlada: `x [m]` (indice 0)

---

## Notas sobre la implementacion

Todos los modelos exponen la misma interface (`derivatives`,
`transfer_function`, `dc_gain`, `steady_state_from_*`). Esto permite:

- Simular cualquier modelo con el mismo motor de simulacion
- Aplicar el mismo controlador PID sin cambios
- Calcular metricas y estabilidad con codigo generico

Las constantes fisicas son valores tipicos de laboratorio, elegidos
para que los tres sistemas tengan constantes de tiempo comparables
(~1 a ~100 s) y sean didacticos con los parametros por defecto.