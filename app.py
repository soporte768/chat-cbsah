import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
import urllib.parse

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="IA CBSAH", page_icon="🎓", layout="wide")

# --- LEER SECRETOS ---
try:
    openai_key = st.secrets["OPENAI_API_KEY"]
    db_host = st.secrets["DB_HOST"]
    db_user = st.secrets["DB_USER"]
    db_pass = st.secrets["DB_PASSWORD"]
    db_name = st.secrets["DB_NAME"]
except:
    st.error("❌ Error: Faltan configurar los secretos (API Key o Base de Datos).")
    st.stop()

# ==========================================
# 2. CAPTURA DE USUARIO (Arreglado)
# ==========================================
query_params = st.query_params
# Decodificamos el nombre para quitar %20 y símbolos raros
usuario_raw = query_params.get("usuario", "Usuario")
usuario_actual = urllib.parse.unquote(usuario_raw).replace('+', ' ')
anio_actual = query_params.get("anio", "2026")

st.markdown(f"### 👋 Hola, **{usuario_actual}**")
st.caption(f"Conectado a Intranet CBSAH | Año Académico: **{anio_actual}**")

# ==========================================
# 3. EL CEREBRO (Instrucciones GPT-4o)
# ==========================================
instrucciones = f"""
Eres un asistente administrativo experto del Colegio CBSAH.
Tu objetivo es consultar la base de datos MySQL y responder en español chileno formal.

REGLAS OBLIGATORIAS:
1. **FILTRO DE AÑO:** SIEMPRE, sin excepción, filtra tus consultas por `ano_escolar = {anio_actual}`.
2. **TABLA 'funcionarios':**
   - El nombre completo está en la columna `nombre` (Ej: 'Ignacio Luis...').
   - El cargo está en la columna `funcion` (Ej: 'DOCENTE', 'ASISTENTE').
   - El rut está en `rut`.
3. **TABLA 'alumnos' (si te preguntan):**
   - Usa `activo = 1` para alumnos vigentes.
   - Relaciona con tabla `cursos` si piden el grado.
4. **FORMATO:**
   - Si piden listas, usa una tabla Markdown bien ordenada.
   - Si no hay datos, di: "No encontré registros para el año {anio_actual}".
"""

# ==========================================
# 4. CONEXIÓN Y CHAT
# ==========================================
if openai_key:
    try:
        # Conexión a Base de Datos
        password_encoded = urllib.parse.quote_plus(db_pass)
        db_uri = f"mysql+pymysql://{db_user}:{password_encoded}@{db_host}/{db_name}"
        db = SQLDatabase.from_uri(db_uri)
        
        # --- USAMOS GPT-4o-mini (El mejor calidad/precio) ---
        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini", 
            api_key=openai_key
        )

        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="openai-tools", # GPT usa herramientas nativas, es muy preciso
            verbose=True,
            handle_parsing_errors=True,
            prefix=instrucciones
        )

        # Interfaz de Chat
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ej: Dame la lista de docentes activos..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Consultando..."):
                    try:
                        response = agent_executor.invoke(prompt)
                        st.markdown(response["output"])
                        st.session_state.messages.append({"role": "assistant", "content": response["output"]})
                    except Exception as e:
                        st.error("Ocurrió un error al procesar tu consulta.")
                        print(e) 

    except Exception as e:
        st.error(f"Error de conexión: {e}")
