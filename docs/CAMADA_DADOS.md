# Camada de dados

Este documento resume a primeira versao da camada de dados do Compliance App /
AI Governance API.

## Apps criados

- `apps.accounts`: usuario customizado, perfil e preferencias.
- `apps.common`: mixin abstrato com `uuid`, `created_at` e `updated_at`.
- `apps.organizations`: organizacoes, unidades e memberships.
- `apps.ai_assets`: fornecedores, ferramentas, modelos, fontes de dados, casos de uso e responsaveis.
- `apps.assessments`: frameworks, dimensoes, perguntas, avaliacoes, respostas, scores e recomendacoes.
- `apps.compliance`: riscos, controles, politicas, avaliacoes de risco e planos de acao.
- `apps.evidence`: evidencias, revisoes e links para riscos, controles ou respostas.
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

Executar checks de qualidade de dados:

```powershell
.\.venv\Scripts\python manage.py run_data_quality_checks
```

Gerar snapshots de metricas para dashboards:

```powershell
.\.venv\Scripts\python manage.py generate_metric_snapshots
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
- `/api/assessments/{uuid}/questionnaire/`
- `/api/assessments/{uuid}/submit/`
- `/api/assessments/{uuid}/summary/`
- `/api/assessments/{uuid}/generate-mitigation-plan/`
- `/api/assessments/{uuid}/executive-report/`
- `/api/assessment-answers/`
- `/api/maturity-scores/`
- `/api/recommendations/`
- `/api/controls/`
- `/api/risks/`
- `/api/risk-controls/`
- `/api/risk-assessments/`
- `/api/policies/`
- `/api/action-plans/`
- `/api/action-items/`
- `/api/evidence/`
- `/api/evidence-links/`
- `/api/evidence-reviews/`
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
- O framework inicial `AIGOV` cobre os blocos do MVP de avaliacao guiada.
- Respostas descritivas de finalidade e dados compartilhados sao obrigatorias.
- A submissao de assessment recalcula `MaturityScore` e gera recomendacoes
  iniciais por dimensao com maturidade abaixo de 80%.
- A geracao de plano de mitigacao cria riscos, avaliacoes de risco, vinculos
  com controles, planos de acao e itens de acao para dimensoes abaixo de 80%.
- A severidade de riscos gerados e derivada de `likelihood * impact`.
- A geracao de mitigacao e idempotente para o mesmo assessment.
- O plano de mitigacao gerado inclui objetivo, justificativa, beneficios
  esperados, complexidade, areas impactadas, indicadores de sucesso e
  evidencias esperadas.
- O relatorio executivo exige assessment submetido e retorna resumo, riscos
  identificados, consequencias juridicas, financeiras, operacionais e
  reputacionais, plano de mitigacao e proximos passos recomendados.

## Formato do relatorio executivo

Endpoint:

```text
GET /api/assessments/{uuid}/executive-report/
```

Estrutura principal:

```json
{
  "assessment": {
    "uuid": "...",
    "title": "...",
    "status": "submitted",
    "submitted_at": "..."
  },
  "organization": {
    "uuid": "...",
    "name": "..."
  },
  "framework": {
    "code": "AIGOV",
    "version": "1.0",
    "name": "AI Governance Maturity"
  },
  "generated_at": "...",
  "executive_summary": {
    "headline": "...",
    "overall_score": {
      "score": "8.00",
      "max_score": "23.00",
      "percentage": "34.78",
      "computed_at": "..."
    },
    "maturity_level": "low",
    "identified_risk_count": 2,
    "priority_risk_count": 2,
    "recommended_focus": []
  },
  "identified_risks": [
    {
      "uuid": "...",
      "title": "...",
      "dimension": {
        "uuid": "...",
        "code": "data-sharing",
        "name": "Data sharing"
      },
      "maturity_percentage": "0.00",
      "likelihood": 5,
      "impact": 5,
      "severity": "critical",
      "status": "open",
      "controls": [],
      "consequences": {
        "legal": "...",
        "financial": "...",
        "operational": "...",
        "reputational": "..."
      }
    }
  ],
  "mitigation_plan": [
    {
      "uuid": "...",
      "title": "...",
      "dimension": {
        "uuid": "...",
        "code": "data-sharing",
        "name": "Data sharing"
      },
      "status": "open",
      "due_date": "2026-08-07",
      "suggested_deadline": "2026-08-07",
      "objective": "...",
      "justification": "...",
      "expected_benefits": [],
      "complexity": "high",
      "impacted_areas": [],
      "success_indicators": [],
      "expected_evidence": [],
      "items": []
    }
  ],
  "recommended_next_steps": []
}
```

## Validacao atual

Validacoes executadas nesta entrega:

```text
python manage.py check
python manage.py test
GET /api/schema/
GET /api/docs/
GET /api/health/
```
