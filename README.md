# TechFix Informática - Sistema de Ordens de Serviço

Sistema web para substituir o atendimento em papel da loja fictícia **TechFix Informática**.
Duas aplicações compartilham o mesmo banco de dados na nuvem:

- **Atendimento (Gradio):** cadastro do cliente e abertura da ordem de serviço (OS), pelo computador ou celular.
- **Painel do gerente (Streamlit):** consulta, filtros, edição, exclusão e indicadores.
- **Banco de dados (Supabase / PostgreSQL):** armazena clientes e ordens de serviço.

> Todos os dados usados nos testes são **fictícios** (LGPD).

## Estrutura do projeto

```
techfix/
├── sql/
│   ├── schema.sql          # criação das tabelas, restrições, índices e políticas
│   └── dados_teste.sql     # dados fictícios para testes (opcional)
├── app_gradio.py           # interface de cadastro
├── app_streamlit.py        # painel de gerenciamento
├── requirements.txt        # dependências
├── .env.example            # nomes das variáveis (sem valores)
├── .gitignore              # impede o envio do .env
├── README.md
└── evidencias/             # prints das telas e das tabelas
```

## Requisitos

- Python 3.10 ou superior
- Conta gratuita no [Supabase](https://supabase.com)

## 1. Banco de dados (Supabase)

1. Crie um projeto no Supabase.
2. Abra **SQL Editor** > **New query**, cole o conteúdo de `sql/schema.sql` e clique em **Run**.
3. (Opcional) Rode `sql/dados_teste.sql` para inserir clientes e OS fictícios.
4. Em **Project Settings > API**, copie a **Project URL** e a chave **anon / publishable**.

## 2. Instalação

Na pasta do projeto, instale as dependências:

```
python -m pip install -r requirements.txt
```

## 3. Credenciais

Copie o arquivo `.env.example` para `.env` e preencha com os valores do seu projeto:

```
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon-ou-publishable
```

O arquivo `.env` não deve ser enviado ao GitHub (já está no `.gitignore`).
O painel Streamlit também aceita `.streamlit/secrets.toml` com as mesmas duas variáveis.

## 4. Executar

**Aplicação de atendimento (Gradio):**

```
python app_gradio.py
```

Abre em `http://127.0.0.1:7860`. Com `share=True`, o Gradio também gera um link público temporário para testar no celular.

**Painel do gerente (Streamlit):**

```
python -m streamlit run app_streamlit.py
```

Abre em `http://localhost:8501`.

## Funcionalidades

### Gradio (app_gradio.py)
- Formulário responsivo com `gr.Blocks`.
- Validação: campos obrigatórios, e-mail com formato válido, celular somente com números (10 a 13 dígitos).
- Reaproveita o cliente pelo e-mail; se não existir, cria um novo.
- Abre a OS com status **Aberto** e informa o número gerado.
- Botão **Limpar**.

### Streamlit (app_streamlit.py)
- **Consultar:** tabela de OS com dados do cliente e filtros na barra lateral (nome, e-mail, status).
- **Cadastrar:** nova OS pelo painel.
- **Editar/Excluir:** alterar status da OS, editar endereço, e-mail e celular do cliente, excluir OS ou cliente (sempre com confirmação).
- **Indicadores:** total de OS, métricas por status e gráfico de barras.
- **Bônus:** exportação dos dados filtrados em CSV.

## Banco de dados

- `clientes`: `id` (PK), `nome`, `endereco`, `email` (único), `celular_whatsapp`, `data_cadastro`.
- `ordens_servico`: `id` (PK), `cliente_id` (FK para `clientes`, `ON DELETE CASCADE`), `modelo_computador`, `problema_relatado`, `status`, `data_abertura`, `data_atualizacao`.
- `status` aceita apenas: Aberto, Em análise, Aguardando peça, Concluído, Entregue.
- Validações no banco: e-mail em formato válido e minúsculo, celular com 10 a 13 dígitos.
- Um gatilho atualiza `data_atualizacao` automaticamente a cada alteração da OS.

## Boas práticas aplicadas

- Chaves do Supabase fora do código (`.env` ou `secrets.toml`).
- `try/except` em todos os acessos ao banco, com mensagens amigáveis ao usuário.
- Apenas dados fictícios nos testes.
- Observação: as políticas de acesso (RLS) liberam a chave `anon` para leitura e escrita. Isso é adequado para esta atividade acadêmica; em um sistema real seria necessário login e políticas mais restritivas.

## Evidências

A pasta `evidencias/` contém os prints do formulário Gradio, da mensagem de cadastro, das tabelas no Supabase e do painel Streamlit (consulta, edição e indicadores).