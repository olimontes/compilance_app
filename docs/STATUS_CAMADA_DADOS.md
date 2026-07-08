# Status da camada de dados

Este documento resume o que foi entregue na primeira versao da camada de dados
do Compliance App / AI Governance API e quais sao os proximos passos apos o MVP.

## Situacao atual

A camada de dados inicial esta implementada na branch:

```text
feature/core-data-models
```

O PR aberto para integrar na `develop` e:

```text
https://github.com/olimontes/compilance_app/pull/1
```

Validacao local mais recente:

```powershell
.\.venv\Scripts\python manage.py test
```

Resultado:

```text
69 tests OK
```

## Decisoes importantes

### Usuario customizado

O projeto usa usuario customizado desde o inicio:

```python
AUTH_USER_MODEL = "accounts.User"
```

Isso evita retrabalho de migrations no futuro e prepara a base para login
corporativo, perfil de usuario e preferencias.

Entidades criadas em `apps.accounts`:

- `User`
- `UserProfile`
- `UserPreference`

Endpoints principais:

- `/api/user-profile/me/`
- `/api/user-preferences/me/`

### Multi-tenancy

A plataforma foi modelada como multi-tenant no mesmo banco.

A entidade central e `Organization`, e o acesso do usuario e definido por
`Membership` ativo.

Regra aplicada:

- usuario comum so acessa dados das organizacoes em que possui membership ativo;
- superuser pode acessar todas as organizacoes;
- entidades de dominio expostas por API usam `uuid`, nao o `id` interno.

Helper central criado:

```text
apps/common/tenancy.py
```

## Apps implementados

### Common

App tecnico com base comum para models:

- `TimestampedUUIDModel`

Campos padronizados:

- `uuid`
- `created_at`
- `updated_at`

### Organizations

Responsavel por empresas, unidades e memberships.

Entidades:

- `Organization`
- `OrganizationUnit`
- `Membership`

Endpoints:

- `/api/organizations/`
- `/api/organization-units/`
- `/api/memberships/`

### AI Assets

Responsavel pelo inventario de IA.

Entidades:

- `AiVendor`
- `AiTool`
- `AiModel`
- `AiUseCase`
- `DataSource`
- `AiAssetOwner`

Endpoints:

- `/api/ai-vendors/`
- `/api/ai-tools/`
- `/api/ai-models/`
- `/api/ai-use-cases/`
- `/api/data-sources/`
- `/api/ai-asset-owners/`

### Assessments

Responsavel por frameworks, perguntas, respostas, pontuacoes e recomendacoes.

Entidades:

- `AssessmentFramework`
- `AssessmentDimension`
- `AssessmentQuestion`
- `Assessment`
- `AssessmentAnswer`
- `MaturityScore`
- `Recommendation`

Endpoints:

- `/api/assessment-frameworks/`
- `/api/assessment-dimensions/`
- `/api/assessment-questions/`
- `/api/assessments/`
- `/api/assessment-answers/`
- `/api/maturity-scores/`
- `/api/recommendations/`

Command criado:

```powershell
.\.venv\Scripts\python manage.py seed_assessment_frameworks
```

### Compliance

Responsavel por riscos, controles, politicas e planos de acao.

Entidades:

- `Control`
- `Risk`
- `RiskControl`
- `RiskAssessment`
- `Policy`
- `ActionPlan`
- `ActionItem`

Endpoints:

- `/api/controls/`
- `/api/risks/`
- `/api/risk-controls/`
- `/api/risk-assessments/`
- `/api/policies/`
- `/api/action-plans/`
- `/api/action-items/`

Command criado:

```powershell
.\.venv\Scripts\python manage.py seed_controls --organization-slug=<slug-da-organizacao>
```

### Evidence

Responsavel por evidencias, links e revisoes.

Entidades:

- `Evidence`
- `EvidenceLink`
- `EvidenceReview`

Endpoints:

- `/api/evidence/`
- `/api/evidence-links/`
- `/api/evidence-reviews/`

No MVP, a prioridade e evidencia por link externo. Upload real de arquivo fica
para uma etapa posterior.

### Audit

Responsavel por rastreabilidade.

Entidades:

- `AuditEvent`
- `DataChangeLog`

Endpoints somente leitura:

- `/api/audit-events/`
- `/api/data-change-logs/`

Eventos de criacao ja registrados pelas APIs principais, por exemplo:

- `organization.created`
- `ai_tool.created`
- `assessment.started`
- `assessment_answer.created`
- `risk.created`
- `control.created`
- `evidence.uploaded`
- `evidence_review.created`

### Analytics

Responsavel por metricas, snapshots, checks de qualidade e ingestion runs.

Entidades:

- `MetricDefinition`
- `MetricSnapshot`
- `DataQualityCheck`
- `IngestionRun`

Endpoints:

- `/api/metric-definitions/`
- `/api/metric-snapshots/`
- `/api/data-quality-checks/`
- `/api/ingestion-runs/`
- `/api/metrics/overview/`

Commands criados:

```powershell
.\.venv\Scripts\python manage.py run_data_quality_checks
.\.venv\Scripts\python manage.py generate_metric_snapshots
```

## Qualidade e testes

Foram criados testes para:

- models principais;
- endpoints REST;
- isolamento multi-tenant;
- rejeicao de relacoes entre organizacoes diferentes;
- commands de seed;
- checks de qualidade de dados;
- geracao de snapshots de metricas;
- auditoria somente leitura.

Validacao atual:

```text
69 tests OK
```

## Ordem sugerida para rodar local

Depois de atualizar a branch e instalar dependencias:

```powershell
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py createsuperuser
.\.venv\Scripts\python manage.py seed_assessment_frameworks
.\.venv\Scripts\python manage.py seed_controls --organization-slug=<slug-da-organizacao>
.\.venv\Scripts\python manage.py run_data_quality_checks
.\.venv\Scripts\python manage.py generate_metric_snapshots
.\.venv\Scripts\python manage.py test
```

Observacao: `seed_controls` exige que a organizacao ja exista.

## Proximos passos

### Processo

1. Revisar o PR com o time.
2. Aprovar o PR no GitHub.
3. Mergear `feature/core-data-models` em `develop`.
4. Rodar `migrate` no ambiente compartilhado.
5. Rodar os commands de seed e metricas quando houver organizacao criada.

### Melhorias tecnicas pos-MVP

- Calcular `Risk.severity` automaticamente a partir de `likelihood` e `impact`.
- Recalcular `MaturityScore` automaticamente a partir de `AssessmentAnswer`.
- Auditar updates relevantes, principalmente mudancas de status.
- Definir politica de retencao para auditoria e evidencias.
- Implementar upload real de arquivos em storage externo.
- Criar imports CSV/XLSX quando o formato de entrada for definido.
- Adicionar jobs Celery quando houver worker disponivel no ambiente.
- Melhorar filtros de API conforme as telas do frontend forem definidas.

## Observacoes importantes

- O banco gratuito do Render nao deve ser tratado como permanente.
- Nao guardar tokens, senhas ou credenciais em tabelas de negocio.
- Evitar PII em logs, eventos de auditoria e campos livres.
- O frontend deve consumir UUIDs, nao IDs internos.
- Toda nova entidade multi-tenant deve ter ligacao clara com `Organization`.
