import streamlit as st
import pandas as pd
import io
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
import urllib.parse

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="IA Analista CBSAH", page_icon="🚀", layout="centered")

try:
    # Ahora esta clave es la de OPENROUTER
    OPENROUTER_API_KEY = st.secrets["OPENAI_API_KEY"] 
    DB_HOST = st.secrets["DB_HOST"]
    DB_USER = st.secrets["DB_USER"]
    DB_PASSWORD = st.secrets["DB_PASSWORD"]
    DB_NAME = st.secrets["DB_NAME"]
except Exception:
    st.error("🚨 Error: Faltan credenciales en secrets.toml")
    st.stop()

# ==========================================
# 2. CONTEXTO
# ==========================================
query_params = st.query_params
usuario_raw = query_params.get("usuario", "Usuario")
usuario_actual = urllib.parse.unquote(usuario_raw).replace('+', ' ')

st.markdown(f"### 🚀 Analista Potente (DeepSeek): **{usuario_actual}**")
st.caption("🤖 Cerebro: **DeepSeek-V3** (Más inteligente, mismo precio)")

# ==========================================
# 3. TABLAS CLAVE
# ==========================================
tablas_gestion_escolar = [
    "alumnos", "alumnos_informacion_adicional", "alumnos_pie",
    "cursos", "asignaturas", "curso_asignatura", "notas", "evaluaciones",
    "anotaciones_convivencia", "atrasos_alumnos", 
    "inasistencias", "medidas_disciplinarias", 
    "funcionarios", "atrasos_funcionarios"
]

# ==========================================
# 4. CEREBRO IA (CONFIGURADO PARA DEEPSEEK)
# ==========================================
instrucciones_sistema = """
Eres un experto DBA y Científico de Datos del colegio CBSAH.
Responde de forma concisa y profesional.

🕵️ **ESTRATEGIA DE NOMBRES:**
Si buscan "Juan Perez", DIVIDE LA BÚSQUEDA:
`WHERE nombres LIKE '%Juan%' AND apellido_paterno LIKE '%Perez%'`
(Nunca busques el nombre completo junto en una sola columna).

🗺️ **REGLAS SQL OBLIGATORIAS:**
1. **AÑO:** Si no especifican año, asume el año escolar vigente.
2. **RELACIONES:**
   - `alumnos` <-> `cursos`: `ON alumnos.curso_id = cursos.id`
   - `atrasos_funcionarios` <-> `funcionarios`: `ON atrasos_funcionarios.funcionario_rut = funcionarios.rut`
   - `notas` <-> `asignaturas`: `ON notas.id_asignatura = asignaturas.id`

🎯 **COMPORTAMIENTO:**
1. **DATO ÚNICO:** Responde solo con texto plano.
2. **LISTAS/TABLAS:** Entrega una **TABLA MARKDOWN**.

📊 **FORMATO DE TABLA:**
| Columna 1 | Columna 2 |
|-----------|-----------|
| Dato A    | Dato B    |
"""

# ==========================================
# 5. FUNCIONES VISUALES (EXCEL Y GRÁFICOS)
# ==========================================
def generar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos_IA')
    return output.getvalue()

def intentar_graficar(texto_respuesta, prompt_usuario):
    try:
        if "|" in texto_respuesta and "---" in texto_respuesta:
            lineas = texto_respuesta.split('\n')
            tabla_lineas = [linea for linea in lineas if "|" in linea]
            tabla_limpia = "\n".join(tabla_lineas)
            
            df = pd.read_csv(io.StringIO(tabla_limpia), sep="|", skipinitialspace=True)
            df = df.dropna(axis=1, how='all')
            df.columns = df.columns.str.strip()
            
            if not df.empty and len(df) > 0:
                palabras_grafico = ["gráfico", "grafico", "barras", "lineas", "evolucion", "torta", "visualizar"]
                pide_grafico = any(p in prompt_usuario.lower() for p in palabras_grafico)
                
                cols_num = df.select_dtypes(include=['float', 'int']).columns
                cols_str = df.select_dtypes(include=['object']).columns
                
                if pide_grafico and len(cols_num) > 0:
                    st.success("📊 Visualización Generada")
                    tab_graf, tab_datos = st.tabs(["📈 Gráfico", "📄 Datos y Descarga"])
                    with tab_graf:
                        if len(cols_str) > 0:
                            st.bar_chart(df.set_index(cols_str[0])[cols_num[0]])
                        else:
                            st.line_chart(df)
                    with tab_datos:
                        st.dataframe(df)
                        excel_data = generar_excel(df)
                        st.download_button("📥 Descargar Excel (.xlsx)", excel_data, "reporte.xlsx")
                else:
                    with st.expander("📂 Ver Tabla de Datos y Descargar Excel"):
                        st.dataframe(df)
                        excel_data = generar_excel(df)
                        st.download_button("📥 Descargar Excel (.xlsx)", excel_data, "reporte.xlsx")
    except Exception:
        pass

# ==========================================
# 6. EJECUCIÓN
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hola. Estoy potenciado con DeepSeek. ¿Qué analizamos hoy?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ej: Atrasos de Juan Perez, Lista del 1° A..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando con DeepSeek..."):
            try:
                password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
                db_uri = f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}/{DB_NAME}"
                
                db = SQLDatabase.from_uri(
                    db_uri,
                    sample_rows_in_table_info=2,
                    include_tables=tablas_gestion_escolar
                )

                # --- AQUÍ ESTÁ EL CAMBIO DE POTENCIA ---
                # Usamos OpenRouter para acceder a DeepSeek
                llm = ChatOpenAI(
                    temperature=0,
                    model="deepseek/deepseek-chat", # Este es el modelo potente y barato
                    api_key=OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1" # Redireccionamos a OpenRouter
                )

                agent_executor = create_sql_agent(
                    llm=llm,
                    db=db,
                    agent_type="openai-tools",
                    verbose=True,
                    handle_parsing_errors=True,
                    prefix=instrucciones_sistema
                )

                response = agent_executor.invoke(prompt)
                output_text = response["output"]
                
                st.markdown(output_text)
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                
                intentar_graficar(output_text, prompt)

            except Exception as e:
                st.error("Error técnico o de conexión.")
                # st.error(f"Detalle: {e}")
