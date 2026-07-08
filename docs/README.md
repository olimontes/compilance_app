# AI Governance API

Backend Django para uma plataforma SaaS de governanca e maturidade no uso corporativo de IA.

Este repositorio comecou como esqueleto de deploy e agora possui a primeira
versao da camada de dados da plataforma.

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
- Apps de dominio para organizacoes, contas, inventario de IA, avaliacoes,
  compliance, evidencias, auditoria e analytics
- Models, migrations, admin Django e endpoints REST da camada de dados
- Testes de isolamento multi-tenant por organizacao
- Eventos de auditoria para criacoes principais
- Commands para seeds, qualidade de dados e snapshots de metricas
- Sentry opcional para capturar erros em producao
- Celery configurado para quando os jobs forem adicionados
- Docker Compose com PostgreSQL e Redis
- Blueprint gratuito do Render
- Guia de Git Flow em `docs/GITFLOW.md`
- Plano de execucao de dados em `docs/PLANO_DADOS.md`
- Status da camada de dados em `docs/STATUS_CAMADA_DADOS.md`
- Controle de passos do projeto em `docs/PASSOS_PROJETO.md`
- README principal na raiz do repositorio

## O que ainda nao existe

- Frontend TypeScript
- Motor de regras
- Integracao com IA
- Jobs Celery em producao gratuita
- Upload real de arquivos de evidencia em storage externo

## Rodar local com PostgreSQL

Suba PostgreSQL e Redis:

```bash
docker compose up -d db redis
```

Crie um `.env` local:

```text
DJANGO_ENV=local
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=unsafe-local-dev-key-change-me
DATABASE_URL=postgres://governance:governance@localhost:5433/governance
POSTGRES_PORT=5433
REDIS_URL=redis://localhost:6379/0
```

Use `5432` em `POSTGRES_PORT` e `DATABASE_URL` se essa porta estiver livre.

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_assessment_frameworks
python manage.py runserver
```

SQLite segue disponivel apenas como fallback local quando `DATABASE_URL` nao
estiver definida.

## Rodar local com Docker

```bash
docker compose up --build
```

Depois acesse:

- API: `http://localhost:8000/api/health/`
- Admin: `http://localhost:8000/admin/`
- Docs: `http://localhost:8000/api/docs/`

## Deploy

O deploy gratuito recomendado para a stack atual e Render, porque o projeto ja inclui:

- `Dockerfile` para deploy via container
- `Procfile` para plataformas estilo Heroku/Railway
- `render.yaml` para Render Blueprint com web service, PostgreSQL e Redis/Key Value gratuitos
- health check em `/api/health/`
- migrations executadas no start do servico

O Blueprint gratuito nao cria background worker Celery, porque workers nao possuem
plano `free` no Render.

O Blueprint gratuito tambem nao usa `preDeployCommand`, porque esse recurso nao
esta disponivel para web services `free` no Render. As migrations rodam no
`startCommand`, antes do Gunicorn.

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

O `render.yaml` atual usa somente planos gratuitos:

- web service `free`;
- PostgreSQL `free`;
- Redis/Key Value `free`;
- sem worker Celery.

Limitacoes importantes:

- o web service gratuito pode dormir quando fica sem trafego;
- o banco PostgreSQL gratuito expira 30 dias apos a criacao;
- o Redis/Key Value gratuito nao persiste dados em disco;
- workers Celery exigem plano pago no Render.
- `preDeployCommand` exige sair do plano gratuito.

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

Para trabalhar com a camada de dados:

```bash
python manage.py migrate
python manage.py seed_assessment_frameworks
python manage.py seed_controls --organization-slug=<slug-da-organizacao>
python manage.py run_data_quality_checks
python manage.py generate_metric_snapshots
```

A documentacao detalhada fica em `docs/CAMADA_DADOS.md` e
`docs/STATUS_CAMADA_DADOS.md`.

Para acompanhar o que ja foi feito e os proximos passos do produto, use
`docs/PASSOS_PROJETO.md`.
