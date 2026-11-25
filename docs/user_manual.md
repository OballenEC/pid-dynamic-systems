# Manual de usuario

Guia practica para instalar, ejecutar y aprovechar el simulador.

---

## 1. Requisitos

- Windows, Linux o macOS
- Python 3.10 o superior
- Git (para clonar el repositorio)

---

## 2. Instalacion

```powershell
git clone https://github.com/OballenEC/pid-dynamic-systems.git
cd "pid-dynamic-systems"
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # Windows PowerShell
# source .venv/bin/activate     # Linux / macOS
pip install -e ".[dev]"
```

Verificar que todo esta bien:

```powershell
python -m pytest -v
```

Debe reportar `59 passed`.

---

## 3. Ejecutar la aplicacion

```powershell
streamlit run src\pid_dynamic_systems\ui\app.py
```

Se abre automaticamente en `http://localhost:8501`.

---

## 4. Flujo de trabajo recomendado

### 4.1 Primera simulacion

1. En la **barra lateral** selecciona un modelo (ej. `Motor DC`)
2. Deja los parametros fisicos por defecto
3. Configura el PID: `Kp=1.0`, `Ki=1.0`, `Kd=0.0`
4. Setpoint: `10.0`, `t_final: 10.0`, `dt: 0.001`
5. Presiona **Simular**

### 4.2 Explorar los tres tabs

- **Simulacion:** graficas de respuesta, control y error. Tabla de
  metricas (rise time, settling time, overshoot, SSE, ISE). Descarga
  CSV.
- **Analisis:** polos del lazo cerrado en el plano complejo, tabla
  con Re/Im/wn/zeta, step del lazo cerrado, Bode.
- **Aprender:** explicaciones generadas dinamicamente segun los
  resultados reales de tu simulacion.

### 4.3 Experimento sugerido

Cambia solo `Kp` de 1 a 10 y presiona **Simular** despues de cada
cambio. Observa:

- Como cambia el **rise time** (deberia reducirse)
- Como cambia el **overshoot** (deberia aumentar)
- Como cambian los **polos** en el tab Analisis (se acercan al eje
  imaginario)
- Como cambia el texto del tab **Aprender** (deberia mencionar
  sobreimpulso mayor)

Este ejercicio demuestra la relacion clasica `Kp↑ → velocidad↑,
overshoot↑`.

---

## 5. Como interpretar las metricas

| Metrica | Que significa | Como mejorarla |
|---|---|---|
| Rise time | Que tan rapido llega al 90% | Aumentar Kp |
| Settling time | Cuando entra y queda en +-2% | Aumentar Kd |
| Overshoot | Cuanto rebasa el setpoint | Aumentar Kd, reducir Kp |
| SSE | Error final respecto a la referencia | Aumentar Ki |
| ISE | Error acumulado (penaliza errores grandes) | Sintonizar los tres |

---

## 6. Como interpretar el tab Analisis

- **Polos con Re < 0:** el sistema es estable
- **Polos cerca del eje imaginario:** margen pequeno, oscilaciones lentas
- **Polos con Re > 0:** sistema INESTABLE, reduce ganancias
- **Bode:** muestra el ancho de banda (que tan rapido sigue referencias)
  y la fase (margen de estabilidad)

---

## 7. Generar el reporte PDF

1. Despues de simular, ve al tab **Simulacion**
2. Seccion "Reporte PDF" -> **Preparar PDF**
3. Una vez generado, aparece **Descargar PDF**
4. El PDF contiene: portada, parametros, graficas, metricas,
   interpretacion

---

## 8. Problemas comunes

**`streamlit: command not found`**  
Activa el venv primero: `.\.venv\Scripts\Activate.ps1`

**La app no carga tras un cambio de codigo**  
Streamlit detecta cambios automaticamente. Si no, `Ctrl+C` y vuelve
a lanzar `streamlit run ...`

**Warning `LF will be replaced by CRLF`**  
Normal en Windows con git. No afecta funcionalidad.

**`SyntaxError: invalid non-printable character U+FEFF`**  
Algun archivo tiene BOM. Ver la seccion 9 de `HANDOFF.md` (gotcha #7).

**El PDF tarda mucho**  
La primera generacion incluye renderizado de matplotlib. Es normal
(2-3 s). Generaciones posteriores usan cache.