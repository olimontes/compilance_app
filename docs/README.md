# AI Governance API

Backend Django para uma plataforma SaaS de governanca e maturidade no uso corporativo de IA.

Este repositorio esta propositalmente como esqueleto de deploy. Ele ainda nao possui modelos,
migrations ou endpoints de dominio da plataforma.

## Stack

- Backend em Django + Django REST Framework
- Frontend planejado em TypeScript
- PostgreSQL em producao
- Redis + Celery para jobs assincronos
- Gunicorn em producao
- WhiteNoise para static files do Django
- Sentry opcional para erros em producao
- Swagger em `/api/docs/`
- Health check em `/api/health/`

## O que ja existe

- Configuracao Django pronta para local/producao
- Health check com teste de conexao ao banco
- Sentry opcional para capturar erros em producao
- Celery configurado para quando os jobs forem adicionados
- Docker Compose com PostgreSQL e Redis
- Blueprint do Render
- Guia de Git Flow em `docs/GITFLOW.md`
- README principal na raiz do repositorio

## O que ainda nao existe

- Frontend TypeScript
- Tabelas de negocio
- Apps de dominio
- Endpoints da plataforma
- Motor de regras
- Integracao com IA

## Rodar local com SQLite

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Rodar local com Docker

```bash
docker compose up --build
```

Depois acesse:

- API: `http://localhost:8000/api/health/`
- Admin: `http://localhost:8000/admin/`
- Docs: `http://localhost:8000/api/docs/`

## Deploy

O deploy recomendado para a stack atual e Render, porque o projeto ja inclui:

- `Dockerfile` para deploy via container
- `Procfile` para plataformas estilo Heroku/Railway
- `render.yaml` para Render Blueprint com web service, worker, PostgreSQL e Redis
- health check em `/api/health/`
- migrations no pre-deploy

Para o frontend TypeScript, use uma das abordagens:

- Render Static Site, se o frontend for SPA com Vite/React e voce quiser manter tudo na mesma plataforma.
- Vercel, se o frontend for Next.js ou se previews de pull request e experiencia frontend forem prioridade.

Deploy de producao deve usar a branch `main`.

Variaveis obrigatorias em producao:

```text
DJANGO_ENV=production
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<secret>
DJANGO_ALLOWED_HOSTS=<api-domain>
DATABASE_URL=<postgres-url>
REDIS_URL=<redis-url>
```

No Render Blueprint, `REDIS_HOST` e `REDIS_PORT` sao preenchidos automaticamente e o Django monta a URL interna.

Variaveis recomendadas:

```text
DJANGO_CORS_ALLOWED_ORIGINS=<frontend-url>
DJANGO_CSRF_TRUSTED_ORIGINS=<frontend-url>
SENTRY_DSN=<dsn-do-projeto-sentry>
```

## Smoke test em producao

1. Abra `/api/health/`.
2. Acesse `/admin/` para validar que o Django carregou.
3. Abra `/api/docs/` para testar a documentacao da API.
4. Para testar captura de erro no Sentry, faca `POST /api/health/error-probe/` autenticado como admin.

## Como comecar as tabelas depois

Quando for modelar o dominio:

```bash
python manage.py startapp organizations apps/organizations
python manage.py makemigrations
python manage.py migrate
```

Depois registre o app em `INSTALLED_APPS` e exponha as rotas em `config/urls.py`.
