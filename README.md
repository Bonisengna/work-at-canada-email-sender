# Employ Research

Fundação da plataforma para busca de vagas e auxílio a candidaturas. Nesta etapa existem somente autenticação e páginas-base; scraping, IA e Gmail não foram implementados.

## Executar localmente

1. Copie `.env.example` para `.env` e substitua os segredos de exemplo.
2. Execute `docker compose up --build`.
3. Acesse http://localhost:3000 e a API em http://localhost:8000/docs.

O cadastro e login são processados integralmente pelo backend. Nenhuma funcionalidade essencial depende de API paga.

## Arquitetura

- `backend/app/routers`: HTTP sem decisões de negócio.
- `backend/app/services`: regras de negócio.
- `backend/app/models`, `schemas`, `core`: dados, contratos, configuração e segurança.
- `backend/app/workers`, `connectors`: reservados, sem scraping, IA ou Gmail nesta etapa.
- `frontend/app`: páginas Next.js do MVP.
