# AI Governance API

Backend Django para uma plataforma SaaS de governanca e maturidade no uso corporativo de IA.

Este repositorio esta propositalmente como esqueleto de deploy. Ele ainda nao possui modelos,
migrations ou endpoints de dominio da plataforma.

## Stack

- Django + Django REST Framework
- PostgreSQL em producao
- Redis + Celery para jobs
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

## O que ainda nao existe

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

O projeto ja inclui:

- `Dockerfile` para deploy via container
- `Procfile` para plataformas estilo Heroku/Railway
- `render.yaml` para Render Blueprint

Variaveis obrigatorias em producao:

```text
DJANGO_ENV=production
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<secret>
DJANGO_ALLOWED_HOSTS=<seu-dominio>
DATABASE_URL=<postgres-url>
REDIS_URL=<redis-url>
```

No Render Blueprint, `REDIS_HOST` e `REDIS_PORT` sao preenchidos automaticamente e o Django monta a URL interna.

Variavel recomendada:

```text
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
