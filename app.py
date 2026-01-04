import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq
import urllib.parse

# 1. CONFIGURACIÓN
st.set_page_config(page_title="IA Intranet", page_icon="⚡")
st.title("⚡ Chat CBSAH")

# 2. OBTENER CLAVES SECRETAS (Automático)
try:
    # Leemos las claves de la "Caja Fuerte" de Streamlit
    api_key = st.secrets["GROQ_API_KEY"]
    db_host = st.secrets["DB_HOST"]
    db_user = st.secrets["DB_USER"]
    db_pass = st.secrets["DB_PASSWORD"]
    db_name = st.secrets["DB_NAME"]
except Exception:
    st.error("❌ Error: No se encontraron los secretos. Configúralos en Streamlit Cloud.")
    st.stop()

# 3. CONEXIÓN Y CHAT
if api_key:
    try:
        # Codificar contraseña por seguridad
        password_encoded = urllib.parse.quote_plus(db_pass)
        db_uri = f"mysql+pymysql://{db_user}:{password_encoded}@{db_host}/{db_name}"
        db = SQLDatabase.from_uri(db_uri)
        
        # Usamos Llama 3.3
        llm = ChatGroq(
            temperature=0, 
            groq_api_key=api_key, 
            model_name="llama-3.3-70b-versatile"
        )

        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="zero-shot-react-description",
            verbose=True,
            handle_parsing_errors=True
        )
        
        st.success("✅ Conectado y Listo")

        # Historial de mensajes
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Caja de entrada
        if prompt := st.chat_input("Consulta tu base de datos aquí..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Procesando..."):
                    try:
                        response = agent_executor.invoke(prompt)
                        st.markdown(response["output"])
                        st.session_state.messages.append({"role": "assistant", "content": response["output"]})
                    except Exception as e:
                        st.error(f"Error: {e}")

    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
