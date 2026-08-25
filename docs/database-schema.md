# Employ Research — schema do banco

Migration inicial: `backend/alembic/versions/20260824_0001_complete_employ_research_schema.py`.

O schema usa UUIDs, `timestamptz`, `jsonb` validado, chaves estrangeiras com comportamento de exclusão explícito, índices nas relações e filas, e RLS em todas as 21 tabelas da aplicação. O acesso pela Data API fica fechado por padrão: não existem políticas para `anon` ou `authenticated`, pois a arquitetura exige acesso pelo backend.

## Diagrama textual

```text
users
 ├─1:1─ candidate_profiles
 ├─1:N─ resumes
 ├─1:N─ search_profiles ─1:N─ search_keywords
 ├─1:1─ user_settings
 ├─1:N─ daily_usage
 ├─1:N─ email_templates
 ├─1:N─ job_scores ─N:1─ jobs
 ├─1:N─ email_drafts ─N:1─ jobs / contacts / templates / resumes
 │                    └─1:1─ email_queue
 │                    └─1:N─ email_sends
 ├─1:N─ applications ─N:1─ jobs
 │                    └─1:N─ application_events
 └─1:N─ automation_runs ─1:N─ scraping_logs

companies
 ├─1:N─ jobs
 └─1:N─ company_contacts

jobs ─1:N─ job_source_links ─N:1─ job_sources
```

## Tabelas e responsabilidades

| Tabela | Responsabilidade | Regras principais |
|---|---|---|
| `users` | Identidade autenticada pelo backend | E-mail único sem diferenciar maiúsculas; senha somente como hash |
| `candidate_profiles` | Perfil profissional consolidado | Uma linha por usuário; experiência, skills, idiomas, certificações e educação em JSON arrays |
| `resumes` | Múltiplos currículos rotulados | Rótulo e SHA-256 únicos por usuário; no máximo um currículo padrão |
| `search_profiles` | Objetivo e parâmetros de busca | País, regiões, cidades, cargos, áreas, idiomas, flexibilidade e imigração |
| `search_keywords` | Termos derivados | Original, tradução, sinônimo, cargo expandido ou termo negativo; origem manual/determinística/IA |
| `job_sources` | Catálogo de conectores | Greenhouse, Lever, Ashby, Job Bank, Québec Emploi e scraping próprio pré-carregados |
| `companies` | Empresa normalizada e enriquecida | Unicidade por nome normalizado + país; payload de enriquecimento opcional |
| `jobs` | Vaga normalizada | `fingerprint` SHA-256 único entre todas as fontes; localização, salário, idioma e imigração |
| `job_source_links` | Ocorrências da vaga nas fontes | N:N entre vaga e fonte; URL única por fonte e payload bruto auditável |
| `company_contacts` | Contatos encontrados | Tipo institucional/pessoal; contato aprovado exige data de aprovação; pessoal deve usar tipo `personal` |
| `job_scores` | Resultados de scoring | Scores determinístico, IA, objetivo, imigração e final entre 0–100; versão do algoritmo |
| `email_templates` | Modelos do usuário | Variáveis declaradas, idioma e um padrão por idioma |
| `email_drafts` | Conteúdo antes do envio | Destinatário materializado, currículo, template, validação e método de geração |
| `email_queue` | Fila transacional | Agendamento, prioridade, lock, tentativas, erros e estados controlados |
| `email_sends` | Histórico imutável de tentativas | IDs do Gmail, destinatário/assunto enviados, resultado e erro |
| `applications` | Candidatura consolidada | Uma candidatura por usuário/vaga e estado atual |
| `application_events` | Linha do tempo da candidatura | Envio, resposta, entrevista, rejeição, retirada, contratação e notas |
| `user_settings` | Preferências e credenciais | Meta somente 3/5/10/15/20 e teto técnico 20; janela, fuso, IA e validação |
| `daily_usage` | Auditoria diária de limites | Uma linha usuário/dia; contadores nunca negativos |
| `automation_runs` | Execuções assíncronas | Tipo, estado, tempos, parâmetros e contagens de sucesso/falha |
| `scraping_logs` | Eventos detalhados de coleta | Execução/fonte, nível, URL, HTTP status e detalhes JSON |

## Segurança e invariantes

- `daily_email_target` possui `CHECK` no PostgreSQL para os valores `3, 5, 10, 15, 20` e teto técnico fixo `20`. O service layer deverá validar a mesma regra antes da persistência.
- Contatos pessoais começam como candidatos à revisão; qualquer contato aprovado precisa registrar `approved_at`.
- `jobs.fingerprint` é globalmente único e `job_source_links` preserva todas as fontes da mesma vaga.
- `ai_api_key_encrypted`, `google_access_token_encrypted` e `google_refresh_token_encrypted` são colunas separadas. A aplicação deve criptografar antes do `INSERT/UPDATE`; não há coluna alternativa para texto puro.
- Não existem tabelas de planos, assinaturas, cobranças ou pagamentos.
- A função de `updated_at` fica no schema privado `app_private` e não usa `SECURITY DEFINER`.

## Execução

```text
cd backend
alembic upgrade head
alembic current
```

No Docker, o backend executa `alembic upgrade head` automaticamente antes de iniciar o Uvicorn. Para Supabase, configure `DATABASE_URL` com a conexão PostgreSQL do projeto e execute o mesmo comando em um ambiente seguro de deploy.
