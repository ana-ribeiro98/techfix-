"""
TechFix Informática - Aplicação de Atendimento (Gradio)
Cadastra o cliente e abre uma Ordem de Serviço (OS) no Supabase.
"""

import os
import re

import gradio as gr
from dotenv import load_dotenv
from supabase import create_client

# ---------------------------------------------------------------------
# 1) Conexão com o Supabase
# As credenciais ficam no arquivo .env (nunca escritas no código).
# ---------------------------------------------------------------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as erro:
    supabase = None
    print(f"[ERRO] Não foi possível conectar ao Supabase: {erro}")

# Formato básico de e-mail: texto@dominio.ext
PADRAO_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


# ---------------------------------------------------------------------
# 2) Validação dos campos (antes de enviar ao banco)
# Devolve uma lista de problemas encontrados (vazia = tudo certo).
# ---------------------------------------------------------------------
def validar(nome, endereco, email, celular, modelo, problema):
    erros = []

    if len(nome.strip()) < 3:
        erros.append("Nome: informe o nome completo (mínimo 3 letras).")
    if not endereco.strip():
        erros.append("Endereço: campo obrigatório.")
    if not PADRAO_EMAIL.match(email.strip()):
        erros.append("E-mail: formato inválido (exemplo: nome@dominio.com).")
    if not (celular.strip().isdigit() and 10 <= len(celular.strip()) <= 13):
        erros.append("Celular: use somente números, de 10 a 13 dígitos (ex.: 11999990000).")
    if len(modelo.strip()) < 2:
        erros.append("Modelo do computador: campo obrigatório.")
    if len(problema.strip()) < 5:
        erros.append("Problema apresentado: descreva o problema (mínimo 5 letras).")

    return erros


# ---------------------------------------------------------------------
# 3) Cadastro: reaproveita o cliente pelo e-mail e abre a OS
# ---------------------------------------------------------------------
def cadastrar(nome, endereco, email, celular, modelo, problema):
    if supabase is None:
        return "❌ Sem conexão com o banco de dados. Verifique o arquivo .env."

    erros = validar(nome, endereco, email, celular, modelo, problema)
    if erros:
        return "⚠️ Corrija os campos abaixo:\n\n- " + "\n- ".join(erros)

    # E-mail sempre em minúsculas e sem espaços (regra do banco)
    email = email.strip().lower()

    try:
        # Procura um cliente com esse e-mail
        busca = supabase.table("clientes").select("id").eq("email", email).execute()

        if busca.data:
            # Cliente já existe: reaproveita
            cliente_id = busca.data[0]["id"]
            aviso_cliente = "Cliente já cadastrado (dados reaproveitados)."
        else:
            # Cliente novo: cadastra
            novo = (
                supabase.table("clientes")
                .insert(
                    {
                        "nome": nome.strip(),
                        "endereco": endereco.strip(),
                        "email": email,
                        "celular_whatsapp": celular.strip(),
                    }
                )
                .execute()
            )
            cliente_id = novo.data[0]["id"]
            aviso_cliente = "Novo cliente cadastrado."

        # Abre a ordem de serviço com status inicial "Aberto"
        os_nova = (
            supabase.table("ordens_servico")
            .insert(
                {
                    "cliente_id": cliente_id,
                    "modelo_computador": modelo.strip(),
                    "problema_relatado": problema.strip(),
                    "status": "Aberto",
                }
            )
            .execute()
        )
        numero_os = os_nova.data[0]["id"]

        return f"✅ OS nº {numero_os} aberta com sucesso!\n{aviso_cliente}"

    except Exception as erro:
        # Mensagem amigável para o usuário; detalhe técnico fica no terminal
        print(f"[ERRO] Falha ao cadastrar: {erro}")
        return "❌ Não foi possível concluir o cadastro. Tente novamente em instantes."


# ---------------------------------------------------------------------
# 4) Botão Limpar: esvazia todos os campos
# ---------------------------------------------------------------------
def limpar():
    return "", "", "", "", "", "", ""


# ---------------------------------------------------------------------
# 5) Interface (gr.Blocks) - funciona no computador e no celular
# ---------------------------------------------------------------------
with gr.Blocks(title="TechFix - Atendimento") as app:
    gr.Markdown(
        "# 🔧 TechFix Informática\n"
        "### Cadastro de Ordem de Serviço\n"
        "Preencha os dados do cliente e do equipamento e clique em **Cadastrar**. "
        "Todos os campos são obrigatórios."
    )

    with gr.Row():
        with gr.Column(min_width=280):
            nome = gr.Textbox(label="Nome do cliente", placeholder="Ex.: Ana Paula Ribeiro")
            email = gr.Textbox(label="E-mail", placeholder="Ex.: ana.ribeiro@exemplo.com")
            celular = gr.Textbox(
                label="Celular/WhatsApp (somente números)", placeholder="Ex.: 11999990000"
            )
        with gr.Column(min_width=280):
            endereco = gr.Textbox(label="Endereço", placeholder="Ex.: Rua das Acácias, 245 - Centro")
            modelo = gr.Textbox(
                label="Modelo do computador", placeholder="Ex.: Notebook Dell Inspiron 15"
            )

    problema = gr.Textbox(
        label="Problema apresentado",
        placeholder="Descreva o que está acontecendo com o equipamento",
        lines=4,
    )

    with gr.Row():
        botao_cadastrar = gr.Button("Cadastrar", variant="primary")
        botao_limpar = gr.Button("Limpar")

    resultado = gr.Textbox(label="Resultado", interactive=False, lines=3)

    campos = [nome, endereco, email, celular, modelo, problema]

    botao_cadastrar.click(cadastrar, inputs=campos, outputs=resultado)
    botao_limpar.click(limpar, inputs=None, outputs=campos + [resultado])


if __name__ == "__main__":
    # share=True gera um link público temporário para testar no celular
    app.launch(share=True)