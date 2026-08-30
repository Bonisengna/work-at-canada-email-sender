# Employ Research

Plataforma pessoal para pesquisar vagas automaticamente, consolidar oportunidades de diferentes fontes, enriquecer dados de empresas e auxiliar ou automatizar candidaturas por e-mail via Gmail.

O sistema atende especialmente pessoas que procuram trabalho no exterior e podem informar tanto sua experiência atual quanto o tipo de oportunidade que desejam, inclusive objetivos relacionados à imigração.

> **Estado atual:** fundação técnica, autenticação, banco completo, migrations e páginas-base estão implementados. Scraping, interpretação de currículo, scoring, enriquecimento, IA e Gmail fazem parte do escopo planejado, mas ainda não estão implementados.

## Objetivo do produto

Reduzir o trabalho manual necessário para:

1. descrever o perfil profissional e o objetivo de busca;
2. encontrar vagas em múltiplas fontes;
3. eliminar oportunidades duplicadas;
4. avaliar a compatibilidade de cada vaga;
5. localizar e validar contatos de empresas;
6. preparar candidaturas personalizadas;
7. enviar e acompanhar e-mails dentro de limites seguros.

O currículo é opcional. O usuário poderá:

- enviar vários currículos PDF ou DOCX, com rótulos como `TI`, `Hotelaria` ou `Produção`;
- descrever em texto livre sua experiência e competências;
- descrever somente o trabalho que procura;
- combinar currículo e objetivo manual, separando **o que já fez** de **o que deseja fazer agora**.

## Regras inegociáveis

### Regras de negócio no backend

Toda decisão funcional ou de segurança pertence ao backend. O frontend apenas apresenta informações e envia a intenção do usuário.

O backend valida:

- autenticação e permissões;
- limites técnicos e contadores diários;
- meta diária de e-mails;
- scoring e critérios de elegibilidade;
- validade da vaga e do contato;
- necessidade de aprovação manual;
- conexão e autorização do Gmail;
- agendamento, fila e envio de e-mails;
- estados das candidaturas e automações.

Valores enviados pelo navegador nunca são fonte de verdade.

### Funcionalidades essenciais sem API paga

Nenhuma função essencial do MVP poderá depender de API paga. O fluxo principal deverá funcionar com Python, PostgreSQL, Redis, scraping permitido e regras determinísticas.

Serviços externos pagos, incluindo IA e enriquecimento de terceiros, serão opcionais e configuráveis pelo usuário, com alternativas gratuitas ou manuais quando fizerem parte de um fluxo essencial.

### Segurança de credenciais

- Senhas são armazenadas somente como hash Argon2.
- Chaves de IA e tokens OAuth do Google ficam em colunas separadas.
- Segredos devem ser criptografados antes da persistência.
- Tokens e chaves nunca podem ser armazenados ou registrados em texto puro.
- As tabelas usam Row-Level Security no PostgreSQL/Supabase e não são expostas diretamente ao frontend.

## Escopo funcional

### 1. Autenticação e conta

- cadastro com e-mail e senha;
- login com JWT;
- validação de usuário ativo;
- preferências individuais;
- armazenamento criptografado das integrações do usuário.

### 2. Perfil profissional

O perfil profissional consolidará:

- resumo profissional;
- experiências e tempo total de experiência;
- competências e ferramentas;
- idiomas e proficiência;
- certificações;
- formação acadêmica;
- texto livre fornecido pelo usuário;
- dados extraídos dos currículos.

### 3. Currículos

- múltiplos currículos por usuário;
- rótulo por área ou objetivo;
- currículo padrão opcional;
- armazenamento do arquivo e metadados;
- SHA-256 para evitar duplicidade;
- extração futura de texto de PDF e DOCX;
- estado de processamento.

### 4. Perfis de busca

Cada perfil poderá definir país, províncias/estados/regiões, cidades, cargos, áreas, objetivo livre, flexibilidade, idiomas de busca, objetivo de imigração e preferências relacionadas.

Um usuário poderá manter vários perfis, por exemplo `Canadá — Hotelaria` e `Québec — Atendimento`.

### 5. Termos de busca

O sistema transformará cargos e objetivos em:

- termos originais;
- traduções;
- sinônimos;
- cargos equivalentes ou expandidos;
- termos negativos;
- termos manuais, determinísticos ou sugeridos por IA opcional.

Exemplo: produção, hotelaria ou logística poderá gerar `production worker`, `factory worker`, `warehouse worker`, `room attendant`, `housekeeper` e `material handler`.

### 6. Fontes de vagas

Conectores previstos:

- Greenhouse;
- Lever;
- Ashby;
- Job Bank Canada;
- Québec Emploi;
- scraping próprio para fontes compatíveis.

A coleta utilizará `httpx`/`requests`, BeautifulSoup e lxml. Playwright será reservado para páginas que dependem de JavaScript. Cada fonte deverá respeitar seus termos e limites técnicos; falhas e eventos serão auditáveis.

### 7. Normalização e deduplicação

As vagas serão convertidas para um formato comum com título, empresa, descrição, contrato, modalidade, localização, salário, idiomas, sinais de imigração e datas relevantes.

Cada vaga possui um `fingerprint` único. `job_source_links` preserva todas as fontes e URLs onde a mesma oportunidade apareceu.

### 8. Empresas e contatos

O sistema poderá consolidar nome, setor, descrição, site, página de carreiras, endereço, localização, origem do enriquecimento e contatos encontrados.

Tipos de contato: `careers`, `hr`, `rh`, `talent`, `contact` e `personal`.

E-mails pessoais ou não institucionais exigem revisão manual. Um contato só poderá ser aprovado quando houver registro explícito da aprovação.

### 9. Scoring de vagas

O sistema armazenará separadamente:

- score determinístico em Python;
- score opcional de IA;
- score de aderência ao objetivo;
- score de imigração quando aplicável;
- score final;
- detalhamento e versão do algoritmo.

O score determinístico é essencial; IA externa nunca será obrigatória.

### 10. Modelos, rascunhos e e-mails

- modelos por usuário e idioma;
- variáveis de personalização;
- geração manual, por template ou IA opcional;
- seleção do currículo adequado;
- validação manual, semiautomática ou automática;
- fila com prioridade, agendamento, locks, tentativas e erros;
- envio futuro via Gmail OAuth;
- histórico com IDs de mensagem/thread;
- registro de falhas, respostas e devoluções quando disponíveis.

### 11. Candidaturas

Cada candidatura reunirá usuário, vaga, currículo, rascunho e último envio. A linha do tempo poderá registrar criação, fila, envio, resposta, entrevista, rejeição, retirada, contratação e notas.

### 12. Meta diária e limites técnicos

O usuário poderá escolher `3`, `5`, `10`, `15` ou `20` e-mails por dia.

`daily_email_target` representa a meta desejada, não uma autorização do frontend. Backend e PostgreSQL revalidam os valores e aplicam o teto técnico fixo de 20 e-mails/dia.

Também serão configuráveis janela de envio, fuso horário, provedor opcional de IA e modo de validação.

**Não existem planos, assinaturas, cobranças ou pagamentos nesta etapa.**

### 13. Auditoria e automações

- contagem diária de e-mails enfileirados, enviados e com falha;
- contagem de análises determinísticas e de IA;
- busca diária, scraping, scoring, geração/envio e enriquecimento;
- estados, tempos, parâmetros e resultados das execuções;
- logs detalhados de scraping e erros.

## Arquitetura

```text
Next.js
   │ envia intenção
   ▼
FastAPI / routers
   ▼
Services / regras de negócio
   ├── PostgreSQL / Supabase
   ├── Redis / filas e cache
   ├── Workers Python
   └── Connectors externos
```

### Stack obrigatória

| Camada | Tecnologia |
|---|---|
| Backend | Python + FastAPI |
| Banco | PostgreSQL, compatível com Supabase |
| Migrations | Alembic |
| Cache e filas | Redis |
| Workers | Python assíncrono |
| Frontend | React + Next.js + TypeScript |
| Coleta | httpx/requests, BeautifulSoup, lxml e Playwright quando necessário |
| E-mail | Gmail OAuth, em etapa futura |
| Execução local | Docker Compose |

### Estrutura do repositório

```text
backend/
  alembic/        migrations
  app/
    connectors/   integrações e fontes
    core/         configuração, banco e segurança
    models/       persistência
    routers/      HTTP sem regra de negócio
    schemas/      contratos de entrada e saída
    services/     casos de uso e regras
    workers/      tarefas assíncronas
  tests/
frontend/
  app/
    onboarding/
    dashboard/
    ajustes/
docs/
  database-schema.md
compose.yaml
```

## Banco de dados

O schema contém:

- `users`, `candidate_profiles`, `resumes`;
- `search_profiles`, `search_keywords`;
- `job_sources`, `jobs`, `job_source_links`;
- `companies`, `company_contacts`, `job_scores`;
- `email_templates`, `email_drafts`, `email_queue`, `email_sends`;
- `applications`, `application_events`;
- `user_settings`, `daily_usage`;
- `automation_runs`, `scraping_logs`.

Diagrama e invariantes: [`docs/database-schema.md`](docs/database-schema.md).

## Estado de implementação

### Implementado e validado

- estrutura FastAPI por camadas;
- registro/login, Argon2 e JWT;
- frontend Next.js com páginas de login, onboarding, dashboard e ajustes;
- Docker Compose com backend, frontend, PostgreSQL e Redis;
- migrations Alembic automáticas no início do backend;
- schema completo com constraints, índices, triggers e RLS;
- catálogo inicial das seis fontes;
- testes de autenticação e invariantes do banco;
- execução local validada em contêineres.

### Planejado — ainda não implementado

- upload e interpretação de currículos;
- editores de perfil profissional e busca;
- expansão de palavras-chave;
- conectores e scraping;
- deduplicação operacional;
- enriquecimento e descoberta de contatos;
- scoring;
- templates e rascunhos;
- Gmail OAuth e envio;
- workers, filas e automações;
- acompanhamento completo de candidaturas;
- interface final das áreas autenticadas.

## Executar localmente

Pré-requisitos: Docker Desktop e portas `3000`, `8000`, `5432` e `6379` disponíveis.

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Substitua os segredos de exemplo no `.env` antes de usar. O backend executa `alembic upgrade head` antes de iniciar.

- aplicação: http://localhost:3000
- documentação da API: http://localhost:8000/docs
- saúde da API: http://localhost:8000/health

### Testes

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Para incluir o teste da migration no PostgreSQL real, defina `TEST_DATABASE_URL` com uma conexão de teste.

## Limites atuais

- Desenvolvimento local; não há confirmação de deploy público.
- Migration pronta para PostgreSQL/Supabase, ainda não aplicada a um projeto Supabase remoto por este repositório.
- Google OAuth, scraping e IA ainda não são executados.
- Credenciais de produção nunca devem ser versionadas.

## Documentação

- [`docs/database-schema.md`](docs/database-schema.md) — entidades, relacionamentos, regras, índices e segurança.
