# Plano de execucao da camada de dados

Este documento orienta o trabalho do engenheiro de dados responsavel por
estruturar a camada de dados do Compliance App / AI Governance API.

O objetivo e transformar o esqueleto atual em uma base confiavel para cadastro
de organizacoes, inventario de uso de IA, avaliacoes de maturidade, evidencias,
riscos, controles e metricas.

## Contexto do projeto

Stack atual:

- Backend: Python 3.14, Django 6, Django REST Framework.
- Banco transacional: PostgreSQL.
- Ambiente local: Docker Compose com PostgreSQL e Redis.
- Deploy gratuito atual: Render com web service, PostgreSQL free e Key Value free.
- Jobs futuros: Celery com Redis/Key Value, quando houver plano com worker.
- Frontend planejado: TypeScript.
- Documentacao da API: Swagger em `/api/docs/`.

Restricoes atuais:

- O banco gratuito do Render deve ser usado apenas para MVP e validacao.
- O banco gratuito expira em 30 dias; nao armazenar dados importantes nele.
- O deploy gratuito nao possui worker Celery.
- Rotinas assincronas devem ser planejadas, mas nao depender do worker em producao
  gratuita.

## Objetivos da camada de dados

1. Criar um modelo relacional consistente para os dominios do produto.
2. Garantir rastreabilidade de alteracoes relevantes.
3. Permitir avaliacao de maturidade e compliance de IA por organizacao.
4. Preparar a base para relatorios, dashboards e metricas historicas.
5. Separar dados transacionais, eventos de auditoria e metricas derivadas.
6. Definir regras de seguranca, retencao, qualidade e governanca.
7. Criar uma base simples para o frontend consumir via API.

## Principios de modelagem

- Toda entidade de negocio deve ter `created_at` e `updated_at`.
- Preferir `UUIDField` como chave publica exposta em APIs.
- Usar `BigAutoField` apenas como detalhe interno quando fizer sentido.
- Toda entidade multi-tenant deve estar ligada a uma `organization`.
- Nao guardar segredo, token ou credencial em texto puro.
- Nao depender de campos `JSONField` para dados que precisam de filtro,
  ordenacao, relacionamento ou relatorio frequente.
- Usar `JSONField` apenas para respostas flexiveis, payloads externos ou
  snapshots historicos.
- Criar constraints no banco para invariantes criticas.
- Criar indices apenas para consultas reais ou previstas.
- Manter migrations pequenas, revisaveis e reversiveis quando possivel.

## Apps Django sugeridos

Criar os apps abaixo dentro de `apps/`:

```text
apps/
  organizations/
  accounts/
  ai_assets/
  assessments/
  compliance/
  evidence/
  analytics/
  audit/
```

Ordem recomendada de implementacao:

1. `organizations`
2. `accounts`
3. `audit`
4. `ai_assets`
5. `assessments`
6. `compliance`
7. `evidence`
8. `analytics`

## Modelo de dominio inicial

### Organizations

Responsavel por separar empresas, unidades e usuarios.

Entidades sugeridas:

- `Organization`
- `OrganizationUnit`
- `Membership`
- `Role`
- `Invitation`

Campos minimos:

```text
Organization
- id
- uuid
- name
- slug
- tax_id opcional
- status
- created_at
- updated_at

OrganizationUnit
- id
- uuid
- organization_id
- parent_id opcional
- name
- slug
- created_at
- updated_at

Membership
- id
- uuid
- organization_id
- user_id
- role
- status
- created_at
- updated_at
```

Regras:

- `slug` deve ser unico por organizacao quando aplicavel.
- Usuario pode pertencer a mais de uma organizacao.
- Toda consulta de dominio deve filtrar por organizacao.

### Accounts

Responsavel por identidade, perfil e preferencia de usuarios.

Entidades sugeridas:

- `UserProfile`
- `UserPreference`

No inicio, usar `django.contrib.auth.User` ou trocar para user customizado antes
de criar muitas migrations de dominio. Se houver chance de login corporativo,
vale decidir cedo se o projeto usara `AUTH_USER_MODEL` customizado.

Campos minimos:

```text
UserProfile
- id
- uuid
- user_id
- display_name
- job_title
- phone opcional
- created_at
- updated_at
```

### Audit

Responsavel por rastreabilidade operacional e eventos relevantes.

Entidades sugeridas:

- `AuditEvent`
- `DataChangeLog`

Campos minimos:

```text
AuditEvent
- id
- uuid
- organization_id opcional
- actor_user_id opcional
- event_type
- entity_type
- entity_uuid
- ip_address opcional
- user_agent opcional
- metadata JSON
- created_at
```

Eventos iniciais:

- `organization.created`
- `membership.invited`
- `ai_asset.created`
- `assessment.started`
- `assessment.submitted`
- `evidence.uploaded`
- `risk.created`
- `control.status_changed`

Regras:

- Eventos de auditoria devem ser append-only.
- Evitar update/delete de eventos.
- Nao registrar segredos, senhas, tokens ou conteudo sensivel desnecessario.

### AI Assets

Responsavel pelo inventario de ferramentas, modelos, fornecedores e casos de uso
de IA.

Entidades sugeridas:

- `AiVendor`
- `AiTool`
- `AiModel`
- `AiUseCase`
- `DataSource`
- `AiAssetOwner`

Campos minimos:

```text
AiVendor
- id
- uuid
- organization_id
- name
- website opcional
- risk_level
- created_at
- updated_at

AiTool
- id
- uuid
- organization_id
- vendor_id opcional
- name
- category
- description
- status
- handles_personal_data
- handles_sensitive_data
- created_at
- updated_at

AiUseCase
- id
- uuid
- organization_id
- ai_tool_id opcional
- owner_membership_id opcional
- name
- business_area
- purpose
- data_classification
- risk_level
- lifecycle_stage
- created_at
- updated_at
```

Classificacoes iniciais:

- `data_classification`: public, internal, confidential, restricted.
- `risk_level`: low, medium, high, critical.
- `lifecycle_stage`: idea, pilot, production, suspended, retired.

### Assessments

Responsavel pelas avaliacoes de maturidade, questionarios, respostas e
pontuacoes.

Entidades sugeridas:

- `AssessmentFramework`
- `AssessmentDimension`
- `AssessmentQuestion`
- `Assessment`
- `AssessmentAnswer`
- `MaturityScore`
- `Recommendation`

Campos minimos:

```text
AssessmentFramework
- id
- uuid
- code
- name
- version
- status
- created_at
- updated_at

AssessmentQuestion
- id
- uuid
- framework_id
- dimension_id
- code
- text
- answer_type
- weight
- is_required
- created_at
- updated_at

Assessment
- id
- uuid
- organization_id
- framework_id
- title
- status
- started_at
- submitted_at opcional
- created_by_id
- created_at
- updated_at

AssessmentAnswer
- id
- uuid
- assessment_id
- question_id
- value JSON
- score
- notes
- answered_by_id
- created_at
- updated_at
```

Regras:

- Framework e perguntas devem ser versionados.
- Respostas devem apontar para a versao exata da pergunta.
- Alterar uma pergunta publicada deve criar nova versao, nao sobrescrever a
  versao anterior.
- Scores derivados devem ser recalculaveis.

### Compliance

Responsavel por controles, riscos, politicas, planos de acao e aderencia.

Entidades sugeridas:

- `Control`
- `ControlRequirement`
- `Risk`
- `RiskAssessment`
- `Policy`
- `ActionPlan`
- `ActionItem`

Campos minimos:

```text
Control
- id
- uuid
- organization_id
- code
- title
- description
- domain
- status
- created_at
- updated_at

Risk
- id
- uuid
- organization_id
- ai_use_case_id opcional
- title
- description
- likelihood
- impact
- severity
- status
- owner_membership_id opcional
- created_at
- updated_at

ActionItem
- id
- uuid
- organization_id
- risk_id opcional
- control_id opcional
- title
- description
- status
- due_date opcional
- owner_membership_id opcional
- created_at
- updated_at
```

Regras:

- `severity` deve ser derivada de `likelihood` e `impact` ou ter criterio
  documentado.
- Mudancas de status devem gerar evento de auditoria.
- Planos de acao devem permitir acompanhamento historico.

### Evidence

Responsavel por evidencias, documentos e anexos que comprovam controles.

Entidades sugeridas:

- `Evidence`
- `EvidenceLink`
- `EvidenceReview`

Campos minimos:

```text
Evidence
- id
- uuid
- organization_id
- title
- description
- evidence_type
- storage_backend
- file_path opcional
- external_url opcional
- checksum opcional
- status
- uploaded_by_id opcional
- created_at
- updated_at
```

Regras:

- No MVP, preferir evidencias por link externo antes de upload de arquivos.
- Quando houver upload, definir storage separado e politicas de retencao.
- Registrar checksum para arquivos quando possivel.
- Controlar acesso por organizacao.

### Analytics

Responsavel por metricas derivadas, snapshots e leituras para dashboard.

Entidades sugeridas:

- `MetricDefinition`
- `MetricSnapshot`
- `DataQualityCheck`
- `IngestionRun`

Campos minimos:

```text
MetricSnapshot
- id
- uuid
- organization_id
- metric_key
- metric_value
- dimensions JSON
- period_start
- period_end
- computed_at

DataQualityCheck
- id
- uuid
- check_key
- target_table
- status
- result JSON
- executed_at

IngestionRun
- id
- uuid
- source_name
- status
- started_at
- finished_at opcional
- rows_read
- rows_written
- error_message opcional
```

Regras:

- Metric snapshots devem ser recriaveis a partir do transacional sempre que
  possivel.
- Dashboards nao devem depender de consultas pesadas em tabelas transacionais
  sem indices.

## Padrao tecnico para models

Criar um mixin comum para modelos de dominio:

```text
UUID
created_at
updated_at
```

Exemplo conceitual:

```python
class TimestampedModel(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

Decidir se esse mixin fica em:

```text
apps/core/models.py
```

ou em um app tecnico:

```text
apps/common/models.py
```

## Convencoes de banco

Nomes:

- Tabelas: usar o padrao do Django ou nomes explicitos em `db_table` apenas se
  houver motivo.
- Campos booleanos: prefixar com `is_`, `has_` ou `can_`.
- Datas: usar `*_at` para timestamps e `*_date` para datas sem hora.
- Chaves externas: nomes de dominio claros, como `organization`,
  `framework`, `question`.

Constraints:

- Unicidade de slugs por organizacao.
- Unicidade de codigos por framework e versao.
- Campos obrigatorios com `null=False` quando a regra de negocio exigir.
- `CheckConstraint` para status e classificacoes quando aplicavel.

Indices iniciais:

- `organization_id` nas tabelas multi-tenant.
- `created_at` em tabelas com listagem temporal.
- `status` em entidades filtradas por fluxo.
- Pares como `(organization_id, status)` e `(organization_id, created_at)` onde
  houver telas de listagem.

## Seguranca, privacidade e LGPD

Classificar dados por sensibilidade:

- Publico
- Interno
- Confidencial
- Restrito
- Dado pessoal
- Dado pessoal sensivel

Regras:

- Nao armazenar senhas, tokens de API ou credenciais em tabelas de negocio.
- Evitar PII em logs, eventos de auditoria e campos `metadata`.
- Definir politica de retencao para evidencias e auditoria.
- Separar dados por organizacao em todas as consultas.
- Criar testes para impedir acesso cruzado entre organizacoes.
- Documentar bases legais e finalidade de uso quando dados pessoais forem
  armazenados.

## Qualidade de dados

Checks minimos:

- Organizacao sem slug duplicado.
- Membership sem usuario ou organizacao inexistente.
- AI use case sem organizacao.
- Assessment sem framework.
- Answer sem question.
- Risk sem severity valida.
- Evidence sem link ou arquivo.

Implementacao:

- Comecar com testes Django e constraints no banco.
- Depois criar `DataQualityCheck` para checks executaveis.
- Registrar resultados em `analytics.DataQualityCheck`.

## Ingestao de dados

No MVP, evitar pipelines complexos. Priorizar:

1. CRUD via API.
2. Imports manuais por management command.
3. Seeds controladas para frameworks e perguntas.
4. Jobs Celery apenas quando houver worker disponivel.

Fontes futuras:

- planilhas CSV/XLSX;
- ferramentas de inventario interno;
- provedores SaaS;
- sistemas de GRC;
- logs de uso de IA;
- integracoes com provedores de LLM.

Padrao para cada ingestao:

- registrar `IngestionRun`;
- validar schema de entrada;
- normalizar dados;
- aplicar upsert idempotente;
- registrar erros por linha quando possivel;
- gerar evento de auditoria para mudancas relevantes.

## Seeds e dados de referencia

Dados que devem ser versionados:

- frameworks de avaliacao;
- dimensoes;
- perguntas;
- tipos de controle;
- categorias de risco;
- classificacoes de dados;
- status padroes.

Formato recomendado:

- migrations de dados para valores essenciais;
- fixtures JSON apenas para dados de demo;
- management commands para cargas maiores.

## APIs esperadas pelo frontend

Priorizar endpoints REST com filtros por organizacao.

Primeiros endpoints:

```text
GET /api/organizations/
GET /api/organizations/{uuid}/
GET /api/ai-tools/
GET /api/ai-use-cases/
GET /api/assessment-frameworks/
GET /api/assessments/
GET /api/assessments/{uuid}/answers/
GET /api/risks/
GET /api/evidence/
GET /api/metrics/overview/
```

Regras:

- Nunca expor IDs internos quando `uuid` resolver.
- Paginar listagens.
- Permitir filtros por `status`, `risk_level`, `created_at` e `owner`.
- Garantir que o usuario so veja dados das organizacoes em que e membro.

## Observabilidade e operacao

Adicionar logs estruturados para:

- criacao de organizacao;
- criacao/alteracao de AI assets;
- inicio e submissao de assessments;
- falhas de integracao;
- falhas de ingestion;
- falhas de data quality.

Adicionar metricas futuras:

- total de casos de uso de IA por organizacao;
- riscos por severidade;
- assessments abertos por status;
- controles pendentes;
- evidencias vencidas;
- score medio de maturidade.

## Backup e ambientes

Ambientes:

- Local: Docker Compose com Postgres.
- Preview/MVP: Render free.
- Producao real: Render pago ou outro provedor com backup persistente.

Regras:

- Nao considerar Render Postgres free como banco permanente.
- Antes de dados reais, migrar para banco pago com backup.
- Definir rotina de backup e restore testado.
- Criar dump local antes de migrations destrutivas.

Comandos uteis:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py dumpdata --natural-foreign --natural-primary > backup.json
python manage.py loaddata backup.json
```

## Roadmap de execucao

### Fase 0 - Preparacao

Entregaveis:

- Confirmar se o projeto usara `AUTH_USER_MODEL` customizado.
- Definir apps de dominio.
- Criar mixins comuns.
- Criar convencoes de models, serializers e permissions.
- Desenhar ERD inicial.

Checklist:

- [x] Decidir user model.
- [x] Criar `apps/common` ou equivalente.
- [x] Criar documento ERD inicial.
- [x] Definir padrao de UUID nas APIs.
- [x] Definir padrao de auditoria.

### Fase 1 - Multi-tenancy e identidade

Entregaveis:

- Apps `organizations` e `accounts`.
- Models de organizacao, unidade e membership.
- Admin Django basico.
- Testes de acesso por organizacao.

Checklist:

- [x] `Organization`
- [x] `OrganizationUnit`
- [x] `Membership`
- [x] `UserProfile`
- [x] Permissoes por organizacao
- [x] Testes de isolamento multi-tenant

### Fase 2 - Inventario de IA

Entregaveis:

- App `ai_assets`.
- Cadastro de fornecedores, ferramentas e casos de uso.
- Classificacao de risco e dados.
- Endpoints REST iniciais.

Checklist:

- [x] `AiVendor`
- [x] `AiTool`
- [x] `AiModel`
- [x] `AiUseCase`
- [x] `DataSource`
- [x] Filtros por organizacao/status/risco

### Fase 3 - Avaliacoes

Entregaveis:

- App `assessments`.
- Framework versionado.
- Perguntas e respostas.
- Calculo inicial de score.
- Seeds do primeiro framework.

Checklist:

- [x] `AssessmentFramework`
- [x] `AssessmentDimension`
- [x] `AssessmentQuestion`
- [x] `Assessment`
- [x] `AssessmentAnswer`
- [x] `MaturityScore`
- [x] Seed inicial de framework

### Fase 4 - Riscos, controles e evidencias

Entregaveis:

- Apps `compliance` e `evidence`.
- Riscos associados a casos de uso.
- Controles e planos de acao.
- Evidencias por link externo no MVP.

Checklist:

- [x] `Control`
- [x] `Risk`
- [x] `RiskAssessment`
- [x] `Policy`
- [x] `ActionPlan`
- [x] `ActionItem`
- [x] `Evidence`

### Fase 5 - Auditoria e qualidade

Entregaveis:

- App `audit`.
- Eventos append-only.
- Checks de qualidade.
- Registro de ingestion runs.

Checklist:

- [x] `AuditEvent`
- [x] Eventos principais de dominio
- [x] `DataQualityCheck`
- [x] `IngestionRun`
- [x] Testes para nao vazar dados entre organizacoes

### Fase 6 - Analytics e dashboards

Entregaveis:

- App `analytics`.
- Snapshots de metricas.
- Endpoints para dashboard.
- Definicao de indicadores principais.

Checklist:

- [x] `MetricDefinition`
- [x] `MetricSnapshot`
- [x] Endpoint `/api/metrics/overview/`
- [x] Metricas por organizacao
- [x] Metricas por periodo

## Status atual da implementacao

A primeira versao da camada de dados foi implementada em branch de feature.
O resumo operacional da entrega esta em `docs/STATUS_CAMADA_DADOS.md`.

Entregas concluidas:

- apps de dominio criados e registrados em `INSTALLED_APPS`;
- models, migrations, admin e endpoints REST;
- isolamento multi-tenant por `Membership` ativo;
- eventos de auditoria para criacoes principais;
- seeds de framework de assessment e controles base;
- checks executaveis de qualidade de dados;
- snapshots de metricas recriaveis para dashboard;
- documentacao operacional em `docs/CAMADA_DADOS.md`;
- suite de testes Django passando.

Pendencias para evolucao apos o MVP:

- calcular `severity` automaticamente a partir de `likelihood` e `impact`;
- recalcular `MaturityScore` automaticamente a partir das respostas;
- auditar tambem updates relevantes, como mudancas de status;
- definir politica formal de retencao de evidencias e auditoria;
- implementar upload real de arquivos em storage externo;
- criar imports manuais CSV/XLSX quando houver formato definido.

## Definicao de pronto

Uma entrega da camada de dados so deve ser considerada pronta quando:

- migrations foram criadas e revisadas;
- `python manage.py test` passa;
- constraints e indices basicos foram definidos;
- endpoints respeitam organizacao e permissoes;
- admin Django permite inspecao operacional;
- Swagger mostra os contratos de API;
- README ou docs foram atualizados quando houver decisao de arquitetura;
- dados sensiveis nao aparecem em logs, eventos ou respostas de API;
- ha pelo menos testes de criacao, listagem e isolamento por organizacao.

## Riscos tecnicos

- Criar user model tarde demais pode gerar migrations complexas.
- Usar `JSONField` em excesso pode dificultar relatorios.
- Ignorar multi-tenancy no inicio pode causar retrabalho grande.
- Banco gratuito do Render nao serve para dados reais permanentes.
- Worker Celery ausente no free tier limita rotinas automaticas.
- Falta de auditoria desde o inicio reduz confiabilidade para compliance.

## Decisoes pendentes

- O projeto tera `AUTH_USER_MODEL` customizado?
- A plataforma sera single-tenant por deploy ou multi-tenant no mesmo banco?
- Quais frameworks de governanca de IA serao suportados primeiro?
- Evidencias serao apenas links no MVP ou tambem upload de arquivo?
- Qual nivel minimo de auditoria sera obrigatorio?
- Havera integracao com provedores externos ainda no MVP?
- O frontend sera Vite/React ou Next.js?

## Primeira semana sugerida

1. Decidir `AUTH_USER_MODEL`.
2. Criar app comum com mixins.
3. Criar `organizations` e `accounts`.
4. Criar models e migrations de organizacao e membership.
5. Criar testes de isolamento por organizacao.
6. Criar admin basico.
7. Gerar ERD inicial.
8. Abrir PR com migrations, testes e documentacao.
