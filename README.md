# Compliance App / AI Governance API

Backend Django para uma plataforma SaaS de governanca, compliance e maturidade
no uso corporativo de IA.

O projeto esta em fase inicial de produto: a base backend, camada de dados,
motor inicial de assessment/mitigacao e primeira interface web ja existem.

## Stack

- Backend: Python 3.14, Django 6, Django REST Framework.
- API docs: drf-spectacular com Swagger em `/api/docs/`.
- Banco de dados: PostgreSQL em producao e desenvolvimento; SQLite apenas como fallback local.
- Jobs e fila: Celery com Redis/Key Value Redis-compatible.
- Servidor de aplicacao: Gunicorn.
- Static files do Django: WhiteNoise.
- Frontend: TypeScript, React e Vite.
- Observabilidade: Sentry opcional.
- Deploy gratuito recomendado: Render para backend, Postgres e Redis/Key Value.
- Deploy de producao recomendado: Render pago com worker Celery e Postgres persistente.
- Deploy opcional do frontend: Render Static Site ou Vercel.

## O que ja existe

- Configuracao Django pronta para local/producao.
- Health check em `/api/health/`.
- Swagger em `/api/docs/`.
- Dockerfile para deploy via container.
- Docker Compose com API, worker, PostgreSQL e Redis para ambiente local.
- `render.yaml` com Blueprint gratuito para web service, Postgres e Redis/Key Value.
- `Procfile` para plataformas estilo Heroku/Railway.
- Guia de Git Flow em `docs/GITFLOW.md`.
- Plano de execucao da camada de dados em `docs/PLANO_DADOS.md`.
- Controle de passos do projeto em `docs/PASSOS_PROJETO.md`.
- Primeira SPA em `frontend/` para assessment, questionario, resumo e relatorio.

## O que ainda nao existe

- Login/registro pensado para usuario final.
- Onboarding guiado de organizacao.
- Dashboard de maturidade completo.
- Integracoes com IA.

## Rodar local com PostgreSQL

Suba PostgreSQL e Redis:

```bash
docker compose up -d db redis
```

Crie um arquivo `.env` local com as variaveis abaixo:

```text
DJANGO_ENV=local
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=unsafe-local-dev-key-change-me
DATABASE_URL=postgres://governance:governance@localhost:5433/governance
POSTGRES_PORT=5433
REDIS_URL=redis://localhost:6379/0
```

Use `5432` em `POSTGRES_PORT` e `DATABASE_URL` se essa porta estiver livre na
sua maquina.

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

## Rodar frontend local

Com o backend Django rodando em `http://127.0.0.1:8000`:

```bash
cd frontend
npm install
npm run dev
```

Depois acesse:

- Frontend: `http://127.0.0.1:5173`

O Vite faz proxy de `/api` para o backend local. A autenticacao atual da tela
usa Basic Auth de desenvolvimento com um usuario Django que tenha `Membership`
ativo em uma organizacao.

## Rodar local com SQLite

SQLite e apenas fallback para testes rapidos sem `DATABASE_URL`:

```bash
python manage.py migrate
python manage.py runserver
```

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

A melhor opcao sem custo para testar a stack atual e usar Render com instancias
free. O projeto ja possui `render.yaml`, entao o deploy pode ser feito como
Blueprint gratuito, criando:

- web service Django;
- banco PostgreSQL free;
- Redis/Key Value free;
- health check;
- migrations executadas no start do servico.

No modo gratuito, o Blueprint nao cria background worker Celery, porque workers
nao possuem instancia `free` no Render. Quando houver jobs assincronos reais,
crie um worker pago ou mova os jobs para outro provedor gratuito.

O plano free tambem nao aceita `preDeployCommand`, entao o Blueprint executa
`python manage.py migrate --noinput` dentro do `startCommand`, antes de iniciar
o Gunicorn. Em um plano pago, o ideal e voltar a usar `preDeployCommand`.

Para o frontend TypeScript, existem duas boas opcoes:

- Render Static Site: melhor quando a prioridade for simplicidade operacional,
  com backend e frontend na mesma plataforma.
- Vercel: melhor experiencia para frontend TypeScript/React/Next.js, previews
  por pull request e CDN global, mas com a infraestrutura dividida entre duas
  plataformas.

Decisao recomendada para este projeto:

- Comecar com Render free para backend, Postgres e Redis/Key Value, e, se o
  frontend for SPA com Vite, tambem hospedar o frontend no Render Static Site.
- Usar Vercel para o frontend se o app for Next.js, tiver SSR, ou se previews e
  experiencia frontend forem prioridade.
- Migrar para planos pagos somente quando o projeto precisar de banco persistente
  de producao, worker Celery ou maior estabilidade.

## Deploy do backend no Render

1. Garanta que a branch `main` esta atualizada no GitHub.
2. Acesse o Render Dashboard.
3. Crie um novo Blueprint.
4. Conecte o repositorio `olimontes/compilance_app`.
5. Selecione a branch `main`.
6. Aplique o Blueprint usando o arquivo `render.yaml`.
7. Aguarde o build e start dos servicos.
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

O `render.yaml` atual prioriza custo zero:

- web service `free`;
- Postgres `free`;
- Redis/Key Value `free`;
- sem worker Celery.

Limitacoes importantes do plano gratuito do Render:

- o web service pode "dormir" apos um periodo sem trafego e demorar cerca de um
  minuto para responder na primeira requisicao;
- o Postgres free expira 30 dias apos a criacao;
- o Key Value free nao persiste dados em disco;
- workers Celery nao estao disponiveis no plano free.
- `preDeployCommand` nao esta disponivel no plano free.

Para evitar cobrancas acidentais, nao selecione planos `starter`, `basic-*`,
`standard`, `pro` ou similares enquanto o objetivo for custo zero.

Variaveis recomendadas:

```text
DJANGO_CORS_ALLOWED_ORIGINS=<frontend-url>
DJANGO_CSRF_TRUSTED_ORIGINS=<frontend-url>
SENTRY_DSN=<dsn-do-projeto-sentry>
```

## Deploy do frontend TypeScript

Estrutura atual:

```text
frontend/
  package.json
  vite.config.ts
  src/
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
VITE_API_BASE_URL=https://<api-domain>/api
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
5. Confirme nos logs que `python manage.py migrate --noinput` executou antes do Gunicorn.
