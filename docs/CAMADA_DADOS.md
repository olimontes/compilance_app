# Camada de dados

Este documento resume a primeira versao da camada de dados do Compliance App /
AI Governance API.

## Apps criados

- `apps.accounts`: usuario customizado, perfil e preferencias.
- `apps.common`: mixin abstrato com `uuid`, `created_at` e `updated_at`.
- `apps.organizations`: organizacoes, unidades e memberships.
- `apps.ai_assets`: fornecedores, ferramentas, modelos, fontes de dados, casos de uso e responsaveis.
- `apps.assessments`: frameworks, dimensoes, perguntas, avaliacoes, respostas, scores e recomendacoes.
- `apps.compliance`: riscos, controles e vinculo risco-controle.
- `apps.evidence`: evidencias e links para riscos, controles ou respostas.
- `apps.audit`: eventos de auditoria e logs de alteracao.
- `apps.analytics`: definicoes de metricas, snapshots, checks e ingestion runs.

## Comandos uteis

Aplicar migrations:

```powershell
.\.venv\Scripts\python manage.py migrate
```

Rodar testes:

```powershell
.\.venv\Scripts\python manage.py test
```

Criar superusuario local:

```powershell
.\.venv\Scripts\python manage.py createsuperuser
```

Carregar framework inicial de assessment:

```powershell
.\.venv\Scripts\python manage.py seed_assessment_frameworks
```

Carregar controles padrao para uma organizacao:

```powershell
.\.venv\Scripts\python manage.py seed_controls --organization-slug=<slug-da-organizacao>
```

## Endpoints principais

- `/api/organizations/`
- `/api/user-profile/me/`
- `/api/user-preferences/me/`
- `/api/organization-units/`
- `/api/memberships/`
- `/api/ai-vendors/`
- `/api/ai-tools/`
- `/api/ai-models/`
- `/api/ai-use-cases/`
- `/api/data-sources/`
- `/api/ai-asset-owners/`
- `/api/assessment-frameworks/`
- `/api/assessment-dimensions/`
- `/api/assessment-questions/`
- `/api/assessments/`
- `/api/assessment-answers/`
- `/api/maturity-scores/`
- `/api/recommendations/`
- `/api/controls/`
- `/api/risks/`
- `/api/risk-controls/`
- `/api/evidence/`
- `/api/evidence-links/`
- `/api/metric-definitions/`
- `/api/metric-snapshots/`
- `/api/data-quality-checks/`
- `/api/ingestion-runs/`
- `/api/audit-events/`
- `/api/data-change-logs/`

## Regras implementadas

- Entidades de negocio usam UUID publico.
- Consultas de dominio sao filtradas por organizacao do usuario.
- `Membership` ativo define acesso comum a dados de organizacao.
- `EvidenceLink` deve apontar para exatamente um alvo.
- `RiskControl` liga riscos e controles sem duplicar pares.
- Eventos de auditoria sao expostos como API somente leitura.

## Validacao atual

Validacoes executadas nesta entrega:

```text
python manage.py check
python manage.py test
GET /api/schema/
GET /api/docs/
GET /api/health/
```
