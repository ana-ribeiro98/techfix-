-- =====================================================================
-- TechFix Informática - Sistema de Ordens de Serviço
-- Script de criação do banco de dados (PostgreSQL / Supabase)
-- Como usar: Supabase > SQL Editor > New query > colar tudo > Run
-- =====================================================================


-- ---------------------------------------------------------------------
-- BLOCO 1: Tabela de CLIENTES
-- Guarda os dados de cada pessoa uma única vez. Um mesmo cliente pode
-- trazer vários equipamentos ao longo do tempo (vários registros na
-- tabela de ordens de serviço apontando para ele).
-- ---------------------------------------------------------------------
create table public.clientes (
    -- PK: número único gerado automaticamente (1, 2, 3...)
    id               bigint generated always as identity primary key,

    -- NOT NULL: o campo é obrigatório, o banco recusa se vier vazio
    nome             text not null,
    endereco         text not null,

    -- UNIQUE: não permite dois clientes com o mesmo e-mail
    email            text not null unique,

    -- Celular/WhatsApp: somente dígitos, de 10 a 13 caracteres
    -- (ex.: 35999998888 ou 5535999998888, com DDI)
    celular_whatsapp text not null,

    -- Data do cadastro: preenchida sozinha com o momento atual
    data_cadastro    timestamptz not null default now(),

    -- CHECK: nome não pode ser só espaços e precisa ter ao menos 3 letras
    constraint ck_clientes_nome
        check (char_length(trim(nome)) >= 3),

    -- CHECK: formato básico de e-mail (texto@dominio.ext)
    constraint ck_clientes_email_formato
        check (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),

    -- CHECK: e-mail sempre em minúsculas, para o UNIQUE funcionar bem
    -- ("Ana@x.com" e "ana@x.com" seriam o mesmo e-mail)
    constraint ck_clientes_email_minusculo
        check (email = lower(email)),

    -- CHECK: celular só com números, entre 10 e 13 dígitos
    constraint ck_clientes_celular
        check (celular_whatsapp ~ '^[0-9]{10,13}$')
);


-- ---------------------------------------------------------------------
-- BLOCO 2: Tabela de ORDENS DE SERVIÇO (OS)
-- Cada linha é um atendimento: um equipamento com um problema.
-- ---------------------------------------------------------------------
create table public.ordens_servico (
    -- PK: número da OS, gerado automaticamente
    id                bigint generated always as identity primary key,

    -- FK: liga a OS a um cliente que exista em "clientes".
    -- ON DELETE CASCADE = se o cliente for excluído, as OS dele também
    -- são excluídas (evita OS "órfãs", sem dono).
    cliente_id        bigint not null
        references public.clientes (id) on delete cascade,

    modelo_computador text not null,
    problema_relatado text not null,

    -- Status do conserto. Começa sempre como 'Aberto'.
    status            text not null default 'Aberto',

    data_abertura     timestamptz not null default now(),
    data_atualizacao  timestamptz not null default now(),

    -- CHECK: só aceita os 5 status do fluxo da loja
    constraint ck_os_status
        check (status in ('Aberto', 'Em análise', 'Aguardando peça',
                          'Concluído', 'Entregue')),

    -- CHECK: modelo e problema não podem ser vazios
    constraint ck_os_modelo
        check (char_length(trim(modelo_computador)) >= 2),
    constraint ck_os_problema
        check (char_length(trim(problema_relatado)) >= 5)
);


-- ---------------------------------------------------------------------
-- BLOCO 3: Índices
-- Funcionam como o "índice remissivo" de um livro: deixam as buscas
-- por cliente e por status mais rápidas.
-- ---------------------------------------------------------------------
create index idx_os_cliente_id on public.ordens_servico (cliente_id);
create index idx_os_status     on public.ordens_servico (status);


-- ---------------------------------------------------------------------
-- BLOCO 4: Atualização automática de "data_atualizacao"
-- Sempre que uma OS for alterada (ex.: mudar o status), o banco grava
-- sozinho o horário da alteração. Ninguém precisa lembrar de fazer isso.
-- ---------------------------------------------------------------------
create or replace function public.atualiza_data_atualizacao()
returns trigger
language plpgsql
as $$
begin
    new.data_atualizacao = now();
    return new;
end;
$$;

create trigger trg_os_data_atualizacao
before update on public.ordens_servico
for each row
execute function public.atualiza_data_atualizacao();


-- ---------------------------------------------------------------------
-- BLOCO 5: Segurança (Row Level Security - RLS)
-- O Supabase exige RLS ligado. Com ele ligado e SEM políticas, nenhum
-- acesso pela chave "anon" funciona. As políticas abaixo liberam leitura,
-- inserção, edição e exclusão para a chave anon.
--
-- ATENÇÃO: isso é adequado para ATIVIDADE ACADÊMICA com dados fictícios.
-- Em um sistema real, o acesso exigiria login (autenticação) e políticas
-- mais restritivas.
-- ---------------------------------------------------------------------
alter table public.clientes       enable row level security;
alter table public.ordens_servico enable row level security;

-- Políticas da tabela clientes
create policy "clientes_select_anon" on public.clientes
    for select to anon using (true);
create policy "clientes_insert_anon" on public.clientes
    for insert to anon with check (true);
create policy "clientes_update_anon" on public.clientes
    for update to anon using (true) with check (true);
create policy "clientes_delete_anon" on public.clientes
    for delete to anon using (true);

-- Políticas da tabela ordens_servico
create policy "os_select_anon" on public.ordens_servico
    for select to anon using (true);
create policy "os_insert_anon" on public.ordens_servico
    for insert to anon with check (true);
create policy "os_update_anon" on public.ordens_servico
    for update to anon using (true) with check (true);
create policy "os_delete_anon" on public.ordens_servico
    for delete to anon using (true);


-- ---------------------------------------------------------------------
-- BLOCO 6 (OPCIONAL): Dados FICTÍCIOS para testar
-- Descomente (remova os "--") para rodar. Nunca use dados reais (LGPD).
-- ---------------------------------------------------------------------
-- Os dados de teste ficam no arquivo separado dados_teste.sql
-- (rodar depois deste script).


-- ---------------------------------------------------------------------
-- BLOCO 7: Conferência
-- Depois de rodar, execute estas linhas para ver se tudo foi criado.
-- ---------------------------------------------------------------------
-- select * from public.clientes;
-- select * from public.ordens_servico;