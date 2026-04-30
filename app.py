import streamlit as st
import psycopg2
from datetime import datetime

def get_connection():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )


def validar_login(usuario, senha):
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Verifica se o usuário e senha existem na tabela usuarios_sistema
        cur.execute("SELECT usuario FROM usuarios_sistema WHERE usuario = %s AND senha = %s", (usuario, senha))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user is not None
    except Exception as e:
        st.error(f"Erro ao validar login: {e}")
        return False    

def tela_login():
    st.container()
    with st.columns([1, 2, 1])[1]: # Centraliza o formulário na tela
        st.subheader("Acesso ao Sistema")
        with st.form("login_form"):
            user = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if validar_login(user, password):
                    st.session_state["logado"] = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas")


def main():
    # 1. Inicializa o estado de segurança
    if "logado" not in st.session_state:
        st.session_state["logado"] = False

    # 2. Verifica se o usuário precisa fazer login
    if not st.session_state["logado"]:
        tela_login()
        return  # Interrompe a execução para não mostrar o app abaixo

    # 3. Adiciona opção de sair na barra lateral
    if st.sidebar.button("Sair do Sistema"):
        st.session_state["logado"] = False
        st.rerun()

    # --- O SEU CÓDIGO ATUAL COMEÇA AQUI ---
    st.title("Sistema de Cadastro")
    st.subheader("Inserir Novo Registro no PostgreSQL")

    # Formulário de Cadastro
    with st.form("cadastro_form", clear_on_submit=True):
        nome = st.text_input("Nome completo", max_chars=50)
        email = st.text_input("E-mail", max_chars=50)
        
        data_nasc = st.date_input(
            "Data de Nascimento", 
            min_value=datetime(1900, 1, 1),
            format="DD/MM/YYYY" 
        )
        
        submit_button = st.form_submit_button("Cadastrar")

    if submit_button:
        if nome and email:
            try:
                conn = get_connection()
                cur = conn.cursor()
                insert_query = """
                INSERT INTO usuarios (nome, email, data_nascimento, data_criacao)
                VALUES (%s, %s, %s, %s)
                """
                valores = (nome, email, data_nasc, datetime.now())
                cur.execute(insert_query, valores)
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"Cadastro de {nome} realizado com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro: {e}")
        else:
            st.warning("Preencha os campos obrigatórios.")

    st.divider()
    st.subheader("📜 Histórico de Cadastros")

    # Filtro de busca simples por nome
    busca_nome = st.text_input("🔍 Buscar por nome no histórico")

    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Query com filtro (ILIKE permite busca parcial ignorando maiúsculas/minúsculas)
        query_historico = """
            SELECT 
                id, 
                nome, 
                email, 
                TO_CHAR(data_nascimento, 'DD/MM/YYYY') as "Data Nasc.",
                TO_CHAR(data_criacao, 'DD/MM/YYYY HH24:MI') as "Data de Cadastro"
            FROM usuarios 
            WHERE nome ILIKE %s
            ORDER BY data_criacao DESC
        """
        cur.execute(query_historico, (f"%{busca_nome}%",))
        dados = cur.fetchall()
        
        if dados:
            # st.data_editor permite que você visualize e até ordene clicando nas colunas
            # Ele é mais moderno que o st.table
            st.dataframe(
                dados, 
                use_container_width=True,
                column_config={
                    "0": "ID",
                    "1": "Nome Completo",
                    "2": "E-mail Principal",
                    "3": "Nascimento",
                    "4": "Momento do Registro"
                }
            )
            
            # Contador de registros
            st.caption(f"Total de {len(dados)} registro(s) encontrado(s).")
            
        else:
            st.info("Nenhum cadastro encontrado com este nome.")
            
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")

if __name__ == "__main__":
    main()