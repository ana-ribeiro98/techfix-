"""
TechFix Informática - Painel do Gerente (Streamlit)
CRUD completo de clientes e ordens de serviço (OS) no Supabase.
"""

import os
import re

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

# ---------------------------------------------------------------------
# 1) Configuração da página e conexão com o Supabase
# As credenciais vêm de .streamlit/secrets.toml OU do arquivo .env.
# ---------------------------------------------------------------------
st.set_page_config(page_title="TechFix - Painel do Gerente", page_icon="🔧", layout="wide")

load_dotenv()

STATUS = ["Aberto", "Em análise", "Aguardando peça", "Concluído", "Entregue"]
PADRAO_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def ler_credencial(nome):
    """Procura primeiro em secrets.toml e, se não houver, nas variáveis de ambiente (.env)."""
    try:
        if nome in st.secrets:
            return st.secrets[nome]
    except Exception:
        pass
    return os.getenv(nome)


@st.cache_resource
def conectar():
    url = ler_credencial("SUPABASE_URL")
    chave = ler_credencial("SUPABASE_KEY")
    return create_client(url, chave)


try:
    supabase = conectar()
except Exception as erro:
    st.error("❌ Não foi possível conectar ao banco de dados. Verifique o arquivo .env.")
    print(f"[ERRO] Conexão: {erro}")
    st.stop()


# ---------------------------------------------------------------------
# 2) Funções de acesso ao banco (todas com try/except)
# ---------------------------------------------------------------------
def carregar_os():
    """Lista as OS já com os dados do cliente, em um DataFrame."""
    try:
        resp = (
            supabase.table("ordens_servico")
            .select("*, clientes(nome, email, celular_whatsapp, endereco)")
            .order("id")
            .execute()
        )
    except Exception as erro:
        print(f"[ERRO] carregar_os: {erro}")
        st.error("❌ Não foi possível carregar as ordens de serviço.")
        return pd.DataFrame()

    linhas = []
    for r in resp.data:
        cli = r.get("clientes") or {}
        linhas.append(
            {
                "OS": r["id"],
                "Cliente": cli.get("nome", ""),
                "E-mail": cli.get("email", ""),
                "Celular": cli.get("celular_whatsapp", ""),
                "Modelo": r["modelo_computador"],
                "Problema": r["problema_relatado"],
                "Status": r["status"],
                "Abertura": r["data_abertura"],
                "Atualização": r["data_atualizacao"],
            }
        )

    df = pd.DataFrame(linhas)
    if not df.empty:
        for col in ["Abertura", "Atualização"]:
            df[col] = (
                pd.to_datetime(df[col], utc=True)
                .dt.tz_convert("America/Sao_Paulo")
                .dt.strftime("%d/%m/%Y %H:%M")
            )
    return df


def carregar_clientes():
    """Lista de clientes (lista de dicionários)."""
    try:
        resp = supabase.table("clientes").select("*").order("nome").execute()
        return resp.data
    except Exception as erro:
        print(f"[ERRO] carregar_clientes: {erro}")
        st.error("❌ Não foi possível carregar os clientes.")
        return []


def validar_cliente(nome, endereco, email, celular):
    erros = []
    if len(nome.strip()) < 3:
        erros.append("Nome: mínimo 3 letras.")
    if not endereco.strip():
        erros.append("Endereço: campo obrigatório.")
    if not PADRAO_EMAIL.match(email.strip()):
        erros.append("E-mail: formato inválido.")
    if not (celular.strip().isdigit() and 10 <= len(celular.strip()) <= 13):
        erros.append("Celular: somente números, de 10 a 13 dígitos.")
    return erros


def aviso(tipo, texto):
    """Guarda uma mensagem para aparecer no topo depois de recarregar a página."""
    st.session_state["aviso"] = (tipo, texto)
    st.rerun()


# ---------------------------------------------------------------------
# 3) Título e mensagem de retorno
# ---------------------------------------------------------------------
st.title("🔧 TechFix Informática")
st.caption("Painel do gerente - ordens de serviço")

if "aviso" in st.session_state:
    tipo, texto = st.session_state.pop("aviso")
    if tipo == "sucesso":
        st.success(texto)
    else:
        st.error(texto)

df = carregar_os()
clientes = carregar_clientes()

# ---------------------------------------------------------------------
# 4) Barra lateral: filtros
# ---------------------------------------------------------------------
st.sidebar.header("Filtros")
filtro_nome = st.sidebar.text_input("Nome do cliente", placeholder="Digite parte do nome")
filtro_email = st.sidebar.text_input("E-mail", placeholder="Digite parte do e-mail")
filtro_status = st.sidebar.multiselect("Status", STATUS)

df_filtrado = df.copy()
if not df_filtrado.empty:
    if filtro_nome:
        df_filtrado = df_filtrado[df_filtrado["Cliente"].str.contains(filtro_nome, case=False, na=False)]
    if filtro_email:
        df_filtrado = df_filtrado[df_filtrado["E-mail"].str.contains(filtro_email, case=False, na=False)]
    if filtro_status:
        df_filtrado = df_filtrado[df_filtrado["Status"].isin(filtro_status)]

# ---------------------------------------------------------------------
# 5) Abas
# ---------------------------------------------------------------------
aba_consultar, aba_cadastrar, aba_editar, aba_indicadores = st.tabs(
    ["📋 Consultar", "➕ Cadastrar", "✏️ Editar/Excluir", "📊 Indicadores"]
)

# ===================== ABA CONSULTAR =====================
with aba_consultar:
    st.subheader("Ordens de serviço")
    if df_filtrado.empty:
        st.info("Nenhuma ordem de serviço encontrada.")
    else:
        st.write(f"{len(df_filtrado)} ordem(ns) de serviço")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

        # Bônus: exportar os dados filtrados em CSV
        csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Exportar CSV (dados filtrados)",
            data=csv,
            file_name="ordens_servico.csv",
            mime="text/csv",
        )

# ===================== ABA CADASTRAR =====================
with aba_cadastrar:
    st.subheader("Cadastrar nova OS")
    st.caption("Se o e-mail já existir, o cliente é reaproveitado.")

    with st.form("form_cadastro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome do cliente")
            email = st.text_input("E-mail")
            celular = st.text_input("Celular/WhatsApp (somente números)")
        with c2:
            endereco = st.text_input("Endereço")
            modelo = st.text_input("Modelo do computador")
            status_novo = st.selectbox("Status inicial", STATUS)
        problema = st.text_area("Problema apresentado")
        enviar = st.form_submit_button("Cadastrar OS", type="primary")

    if enviar:
        erros = validar_cliente(nome, endereco, email, celular)
        if len(modelo.strip()) < 2:
            erros.append("Modelo do computador: campo obrigatório.")
        if len(problema.strip()) < 5:
            erros.append("Problema: descreva o problema (mínimo 5 letras).")

        if erros:
            st.error("Corrija os campos:\n\n- " + "\n- ".join(erros))
        else:
            email_ok = email.strip().lower()
            try:
                busca = supabase.table("clientes").select("id").eq("email", email_ok).execute()
                if busca.data:
                    cliente_id = busca.data[0]["id"]
                else:
                    novo = (
                        supabase.table("clientes")
                        .insert(
                            {
                                "nome": nome.strip(),
                                "endereco": endereco.strip(),
                                "email": email_ok,
                                "celular_whatsapp": celular.strip(),
                            }
                        )
                        .execute()
                    )
                    cliente_id = novo.data[0]["id"]

                nova_os = (
                    supabase.table("ordens_servico")
                    .insert(
                        {
                            "cliente_id": cliente_id,
                            "modelo_computador": modelo.strip(),
                            "problema_relatado": problema.strip(),
                            "status": status_novo,
                        }
                    )
                    .execute()
                )
                aviso("sucesso", f"✅ OS nº {nova_os.data[0]['id']} cadastrada com sucesso!")
            except Exception as erro:
                print(f"[ERRO] cadastrar OS: {erro}")
                st.error("❌ Não foi possível cadastrar. Tente novamente.")

# ===================== ABA EDITAR/EXCLUIR =====================
with aba_editar:
    # ---------- Alterar status de uma OS ----------
    st.subheader("Alterar status de uma OS")
    if df.empty:
        st.info("Não há ordens de serviço.")
    else:
        opcoes_os = df["OS"].tolist()

        def rotulo_os(os_id):
            linha = df[df["OS"] == os_id].iloc[0]
            return f"OS {os_id} - {linha['Cliente']} - {linha['Modelo']} ({linha['Status']})"

        os_escolhida = st.selectbox("Escolha a OS", opcoes_os, format_func=rotulo_os, key="sel_os_status")
        status_atual = df[df["OS"] == os_escolhida].iloc[0]["Status"]
        novo_status = st.selectbox("Novo status", STATUS, index=STATUS.index(status_atual))

        if st.button("Salvar status", type="primary"):
            try:
                supabase.table("ordens_servico").update({"status": novo_status}).eq("id", os_escolhida).execute()
                aviso("sucesso", f"✅ Status da OS {os_escolhida} atualizado para '{novo_status}'.")
            except Exception as erro:
                print(f"[ERRO] atualizar status: {erro}")
                st.error("❌ Não foi possível atualizar o status.")

    st.divider()

    # ---------- Editar dados do cliente ----------
    st.subheader("Editar dados do cliente")
    if not clientes:
        st.info("Não há clientes.")
    else:
        mapa_clientes = {c["id"]: c for c in clientes}
        cli_escolhido = st.selectbox(
            "Escolha o cliente",
            list(mapa_clientes.keys()),
            format_func=lambda i: f"{mapa_clientes[i]['nome']} ({mapa_clientes[i]['email']})",
            key="sel_cli_editar",
        )
        cli = mapa_clientes[cli_escolhido]

        # A chave inclui o id, para os campos refletirem o cliente escolhido
        novo_end = st.text_input("Endereço", value=cli["endereco"], key=f"end_{cli_escolhido}")
        novo_email = st.text_input("E-mail", value=cli["email"], key=f"email_{cli_escolhido}")
        novo_cel = st.text_input("Celular/WhatsApp", value=cli["celular_whatsapp"], key=f"cel_{cli_escolhido}")

        if st.button("Salvar dados do cliente", type="primary"):
            erros = validar_cliente(cli["nome"], novo_end, novo_email, novo_cel)
            if erros:
                st.error("Corrija os campos:\n\n- " + "\n- ".join(erros))
            else:
                try:
                    supabase.table("clientes").update(
                        {
                            "endereco": novo_end.strip(),
                            "email": novo_email.strip().lower(),
                            "celular_whatsapp": novo_cel.strip(),
                        }
                    ).eq("id", cli_escolhido).execute()
                    aviso("sucesso", f"✅ Dados de {cli['nome']} atualizados.")
                except Exception as erro:
                    print(f"[ERRO] atualizar cliente: {erro}")
                    st.error("❌ Não foi possível atualizar. O e-mail pode já estar em uso por outro cliente.")

    st.divider()

    # ---------- Excluir uma OS (com confirmação) ----------
    st.subheader("Excluir uma OS")
    if df.empty:
        st.info("Não há ordens de serviço.")
    else:
        os_excluir = st.selectbox("Escolha a OS a excluir", opcoes_os, format_func=rotulo_os, key="sel_os_excluir")

        if st.button("🗑️ Excluir OS"):
            st.session_state["confirmar_os"] = os_excluir

        if st.session_state.get("confirmar_os") == os_excluir:
            st.warning(f"Tem certeza que deseja excluir a OS {os_excluir}? Essa ação não pode ser desfeita.")
            col_sim, col_nao = st.columns(2)
            if col_sim.button("Sim, excluir", key="sim_os"):
                try:
                    supabase.table("ordens_servico").delete().eq("id", os_excluir).execute()
                    st.session_state.pop("confirmar_os", None)
                    aviso("sucesso", f"✅ OS {os_excluir} excluída.")
                except Exception as erro:
                    print(f"[ERRO] excluir OS: {erro}")
                    st.error("❌ Não foi possível excluir a OS.")
            if col_nao.button("Cancelar", key="nao_os"):
                st.session_state.pop("confirmar_os", None)
                st.rerun()

    st.divider()

    # ---------- Excluir um cliente (com confirmação) ----------
    st.subheader("Excluir um cliente")
    if not clientes:
        st.info("Não há clientes.")
    else:
        cli_excluir = st.selectbox(
            "Escolha o cliente a excluir",
            list(mapa_clientes.keys()),
            format_func=lambda i: f"{mapa_clientes[i]['nome']} ({mapa_clientes[i]['email']})",
            key="sel_cli_excluir",
        )

        if st.button("🗑️ Excluir cliente"):
            st.session_state["confirmar_cli"] = cli_excluir

        if st.session_state.get("confirmar_cli") == cli_excluir:
            st.warning(
                f"Tem certeza que deseja excluir {mapa_clientes[cli_excluir]['nome']}? "
                "Todas as OS desse cliente também serão excluídas. Essa ação não pode ser desfeita."
            )
            col_sim, col_nao = st.columns(2)
            if col_sim.button("Sim, excluir", key="sim_cli"):
                try:
                    supabase.table("clientes").delete().eq("id", cli_excluir).execute()
                    st.session_state.pop("confirmar_cli", None)
                    aviso("sucesso", "✅ Cliente excluído (e as OS dele também).")
                except Exception as erro:
                    print(f"[ERRO] excluir cliente: {erro}")
                    st.error("❌ Não foi possível excluir o cliente.")
            if col_nao.button("Cancelar", key="nao_cli"):
                st.session_state.pop("confirmar_cli", None)
                st.rerun()

# ===================== ABA INDICADORES =====================
with aba_indicadores:
    st.subheader("Indicadores")
    if df.empty:
        st.info("Ainda não há dados para exibir.")
    else:
        contagem = df["Status"].value_counts().reindex(STATUS, fill_value=0)

        colunas = st.columns(len(STATUS) + 1)
        colunas[0].metric("Total de OS", len(df))
        for coluna, nome_status in zip(colunas[1:], STATUS):
            coluna.metric(nome_status, int(contagem[nome_status]))

        st.write("**Ordens de serviço por status**")
        st.bar_chart(contagem)