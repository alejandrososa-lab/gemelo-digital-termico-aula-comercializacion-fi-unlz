
import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Gemelo Digital del Aula", layout="wide")

st.title("Gemelo Digital simplificado de un aula")
st.caption("Modelo didáctico para simular temperatura, ocupación y capacidad de climatización.")

with st.sidebar:
    st.header("Condiciones del aula")
    largo = st.number_input("Largo del aula (m)", 3.0, 20.0, 8.0, 0.5)
    ancho = st.number_input("Ancho del aula (m)", 3.0, 20.0, 5.0, 0.5)
    alto = st.number_input("Alto del aula (m)", 2.0, 5.0, 2.7, 0.1)

    st.header("Condiciones ambientales")
    temp_inicial = st.slider("Temperatura interior inicial (°C)", 18.0, 35.0, 27.0, 0.5)
    temp_exterior = st.slider("Temperatura exterior (°C)", 10.0, 45.0, 32.0, 0.5)
    temp_objetivo = st.slider("Temperatura objetivo (°C)", 18.0, 28.0, 24.0, 0.5)

    st.header("Uso del aula")
    alumnos = st.slider("Cantidad de alumnos", 0, 80, 20, 1)
    potencia_frigorias = st.slider("Potencia del aire (frigorías/h)", 1500, 12000, 6000, 250)
    persianas = st.selectbox("Persianas", ["Abiertas", "Cerradas"])
    sol = st.selectbox("Radiación solar", ["Baja", "Media", "Alta"])

# ----------------------------
# MODELO DIDÁCTICO SIMPLIFICADO
# ----------------------------
volumen = largo * ancho * alto

# Capacidad térmica efectiva del recinto.
# Incluye aire + masa térmica simplificada de paredes/muebles.
capacidad_termica_kj_c = volumen * 1.2 * 1.005 * 8.0

# Ganancia térmica aproximada por persona (W)
ganancia_personas_w = alumnos * 100.0

# Ganancia por transmisión con el exterior, simplificada
area_envolvente = 2*(largo*alto + ancho*alto) + largo*ancho
u_global = 1.2  # W/m2K, valor didáctico
ganancia_transmision_w = max(0.0, u_global * area_envolvente * (temp_exterior - temp_inicial))

# Ganancia solar simplificada
solar_factor = {"Baja": 4.0, "Media": 8.0, "Alta": 14.0}[sol]
if persianas == "Cerradas":
    solar_factor *= 0.45
ganancia_solar_w = largo * ancho * solar_factor

# Conversión aproximada: 1 frigoría/h ≈ 1.163 W
potencia_frio_w = potencia_frigorias * 1.163

ganancia_total_w = ganancia_personas_w + ganancia_transmision_w + ganancia_solar_w
balance_neto_w = potencia_frio_w - ganancia_total_w

# Simulación minuto a minuto
minutos = list(range(0, 121))
temps = [temp_inicial]
temp = temp_inicial

for m in minutos[1:]:
    # pérdidas/ganancias cambian con la diferencia térmica
    transmision = u_global * area_envolvente * (temp_exterior - temp)
    solar = ganancia_solar_w
    personas = ganancia_personas_w

    neto_w = potencia_frio_w - (max(0, transmision) + solar + personas)

    # kJ por minuto
    energia_neta_kj = neto_w * 60 / 1000
    delta_t = energia_neta_kj / capacidad_termica_kj_c

    # No permitimos enfriar indefinidamente por debajo del objetivo:
    # el equipo modula cerca del setpoint.
    if temp > temp_objetivo:
        temp = max(temp_objetivo, temp - max(0, delta_t))
    else:
        temp = temp_objetivo

    temps.append(temp)

df = pd.DataFrame({"Minutos": minutos, "Temperatura (°C)": temps})

tiempo_obj = None
for minuto, t in zip(minutos, temps):
    if t <= temp_objetivo + 0.05:
        tiempo_obj = minuto
        break

if balance_neto_w > 0:
    estado = "Capacidad suficiente"
else:
    estado = "Capacidad insuficiente"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Volumen", f"{volumen:.0f} m³")
col2.metric("Carga térmica estimada", f"{ganancia_total_w/1000:.1f} kW")
col3.metric("Potencia de frío", f"{potencia_frio_w/1000:.1f} kW")
col4.metric("Estado", estado)

st.subheader("Evolución simulada de la temperatura")
st.line_chart(df.set_index("Minutos"))

c1, c2 = st.columns(2)

with c1:
    st.subheader("Resultado")
    if tiempo_obj is not None:
        st.success(f"El modelo estima que se llega a {temp_objetivo:.1f} °C en aproximadamente {tiempo_obj} minutos.")
    else:
        st.error(f"Con estas condiciones no se llega a {temp_objetivo:.1f} °C dentro de 120 minutos.")

with c2:
    st.subheader("¿Qué está cargando térmicamente el aula?")
    cargas = pd.DataFrame({
        "Fuente": ["Personas", "Exterior", "Radiación solar"],
        "Potencia térmica (W)": [
            ganancia_personas_w,
            ganancia_transmision_w,
            ganancia_solar_w
        ]
    })
    st.bar_chart(cargas.set_index("Fuente"))

st.divider()
st.subheader("Probá escenarios")

st.markdown("""
Cambiá una variable en el panel izquierdo y observá qué pasa:

- **20 → 40 alumnos**
- **32 → 38 °C exterior**
- **Persianas abiertas → cerradas**
- **6000 → 9000 frigorías/h**

Eso permite mostrar la idea central del gemelo digital:

**Realidad → datos → modelo digital → simulación → decisión**
""")

st.info(
    "Este es un modelo didáctico simplificado. Sirve para enseñar el concepto de gemelo digital, "
    "pero no reemplaza un cálculo profesional de climatización."
)
