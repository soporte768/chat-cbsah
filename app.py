import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq
import urllib.parse

# 1. CONFIGURACIÓN
st.set_page_config(page_title="IA Intranet CBSAH", page_icon="⚡")
st.title("⚡ Chat CBSAH (Llama 3.3)")
st.markdown("Usando el nuevo modelo Llama 3.3 (El más potente y gratis).")

# 2. ENTRADA DE CLAVE
api_key = st.sidebar.text_input("Pega tu Groq API Key (gsk_...):", type="password")

# 3. DATOS DE CONEXIÓN
db_host = '51.79.9.184'
db_user = 'intranet_cbsah'
db_pass_raw = 'cbsah3202@'
db_name = 'intranet_cbsah'
db_password = urllib.parse.quote_plus(db_pass_raw)

# 4. LÓGICA DEL CHAT
if api_key:
    try:
        db_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
        db = SQLDatabase.from_uri(db_uri)
        
        # --- ACTUALIZACIÓN: USAMOS EL NUEVO LLAMA 3.3 ---
        llm = ChatGroq(
            temperature=0, 
            groq_api_key=api_key, 
            model_name="llama-3.3-70b-versatile" # <--- ESTE ES EL NUEVO NOMBRE CORRECTO
        )

        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="zero-shot-react-description",
            verbose=True,
            handle_parsing_errors=True
        )
        
        st.success("✅ Conectado a Llama 3.3")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ej: ¿Cuántos alumnos hay en total?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analizando..."):
                    try:
                        response = agent_executor.invoke(prompt)
                        st.markdown(response["output"])
                        st.session_state.messages.append({"role": "assistant", "content": response["output"]})
                    except Exception as e:
                        st.error(f"Error: {e}")

    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")

else:
    st.warning("👈 Pega tu clave de Groq en el menú lateral.")