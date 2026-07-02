# Compliance App / AI Governance API

Backend Django para uma plataforma SaaS de governanca, compliance e maturidade
no uso corporativo de IA.

O projeto ainda esta em fase inicial: a base de deploy, configuracao e health
check ja existe, mas os apps de dominio, modelos de negocio e frontend ainda
serao implementados.

## Stack

- Backend: Python 3.14, Django 6, Django REST Framework.
- API docs: drf-spectacular com Swagger em `/api/docs/`.
- Banco de dados: PostgreSQL em producao; SQLite apenas como fallback local.
- Jobs e fila: Celery com Redis/Key Value Redis-compatible.
- Servidor de aplicacao: Gunicorn.
- Static files do Django: WhiteNoise.
- Frontend planejado: TypeScript, preferencialmente React com Vite ou Next.js.
- Observabilidade: Sentry opcional.
- Deploy recomendado: Render para backend, Postgres, Redis e worker.
- Deploy opcional do frontend: Render Static Site ou Vercel.

## O que ja existe

- Configuracao Django pronta para local/producao.
- Health check em `/api/health/`.
- Swagger em `/api/docs/`.
- Dockerfile para deploy via container.
- Docker Compose com API, worker, PostgreSQL e Redis para ambiente local.
- `render.yaml` com Blueprint para web service, worker, Postgres e Redis.
- `Procfile` para plataformas estilo Heroku/Railway.
- Guia de Git Flow em `docs/GITFLOW.md`.

## O que ainda nao existe

- Frontend TypeScript.
- Apps de dominio.
- Modelos e migrations de negocio.
- Endpoints da plataforma.
- Motor de regras.
- Integracoes com IA.

## Rodar local com SQLite

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Depois acesse:

- API: `http://localhost:8000/api/health/`
- Admin: `http://localhost:8000/admin/`
- Docs: `http://localhost:8000/api/docs/`

## Rodar local com Docker

```bash
docker compose up --build
```

Esse comando sobe:

- `api`: Django.
- `worker`: Celery.
- `db`: PostgreSQL.
- `redis`: Redis.

## Estrategia de deploy recomendada

A melhor opcao para a stack atual e usar Render como plataforma principal do
backend. O projeto ja possui `render.yaml`, entao o deploy pode ser feito como
Blueprint, criando de uma vez:

- web service Django;
- background worker Celery;
- banco PostgreSQL gerenciado;
- Redis/Key Value gerenciado;
- health check;
- comando de migrations antes do deploy.

Para o frontend TypeScript, existem duas boas opcoes:

- Render Static Site: melhor quando a prioridade for simplicidade operacional,
  com backend e frontend na mesma plataforma.
- Vercel: melhor experiencia para frontend TypeScript/React/Next.js, previews
  por pull request e CDN global, mas com a infraestrutura dividida entre duas
  plataformas.

Decisao recomendada para este projeto:

- Comecar com Render para backend, Postgres, Redis, worker e, se o frontend for
  SPA com Vite, tambem hospedar o frontend no Render Static Site.
- Usar Vercel para o frontend se o app for Next.js, tiver SSR, ou se previews e
  experiencia frontend forem prioridade.

## Deploy do backend no Render

1. Garanta que a branch `main` esta atualizada no GitHub.
2. Acesse o Render Dashboard.
3. Crie um novo Blueprint.
4. Conecte o repositorio `olimontes/compilance_app`.
5. Selecione a branch `main`.
6. Aplique o Blueprint usando o arquivo `render.yaml`.
7. Aguarde o build, migrations e start dos servicos.
8. Valide `/api/health/`, `/admin/` e `/api/docs/`.

Variaveis obrigatorias em producao:

```text
DJANGO_ENV=production
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<secret>
DJANGO_ALLOWED_HOSTS=<api-domain>
DATABASE_URL=<postgres-url>
REDIS_URL=<redis-url>
```

No Blueprint atual, `DATABASE_URL`, `REDIS_HOST`, `REDIS_PORT` e
`DJANGO_SECRET_KEY` sao preenchidos automaticamente pelo Render.

Variaveis recomendadas:

```text
DJANGO_CORS_ALLOWED_ORIGINS=<frontend-url>
DJANGO_CSRF_TRUSTED_ORIGINS=<frontend-url>
SENTRY_DSN=<dsn-do-projeto-sentry>
```

## Deploy do frontend TypeScript

Quando o frontend for criado, a estrutura recomendada e:

```text
frontend/
  package.json
  src/
  vite.config.ts ou next.config.ts
```

Para frontend Vite/React em Render Static Site:

```text
Root Directory: frontend
Build Command: npm ci && npm run build
Publish Directory: dist
Production Branch: main
```

Variavel esperada no frontend:

```text
VITE_API_BASE_URL=https://<api-domain>
```

Para frontend Next.js em Vercel:

```text
Root Directory: frontend
Production Branch: main
Build Command: definido automaticamente pelo preset Next.js
```

Variavel esperada no frontend:

```text
NEXT_PUBLIC_API_BASE_URL=https://<api-domain>
```

Depois de publicar o frontend, atualize no backend:

```text
DJANGO_CORS_ALLOWED_ORIGINS=https://<frontend-domain>
DJANGO_CSRF_TRUSTED_ORIGINS=https://<frontend-domain>
```

## Deploy e Git Flow

- Desenvolvimento acontece em `develop` ou `feature/*`.
- Producao usa `main`.
- O Render deve ficar conectado na branch `main`.
- Antes de mergear para `main`, rode:

```bash
python manage.py test
```

Para detalhes de commits, branches e pull requests, veja `docs/GITFLOW.md`.

## Smoke test em producao

1. Acesse `/api/health/`.
2. Acesse `/admin/`.
3. Acesse `/api/docs/`.
4. Verifique logs do web service e worker.
5. Confirme que migrations foram executadas no deploy.
