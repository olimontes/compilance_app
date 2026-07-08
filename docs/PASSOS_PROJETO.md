# Passos do projeto

Este documento e o controle operacional do Compliance App / AI Governance API.
Ele transforma a visao de produto de `docs/ideia_plataforma_governanca_ia.md`
em passos acompanhaveis.

Atualizado em: 2026-07-08.

## Como usar

Legenda:

- `[x]` feito
- `[>]` proximo foco
- `[ ]` pendente

Regra pratica:

- `ideia_plataforma_governanca_ia.md` guarda o norte do produto.
- `PLANO_DADOS.md` guarda a arquitetura da camada de dados.
- `STATUS_CAMADA_DADOS.md` resume a entrega tecnica da camada de dados.
- Este documento guarda a sequencia de produto e engenharia.

## Norte do produto

O fluxo central descrito na ideia do produto e:

```text
Login
Cadastro da empresa
Cadastro das ferramentas de IA utilizadas
Questionario estruturado
Campos descritivos complementares
Analise inteligente dos riscos
Relatorio executivo
Plano de mitigacao
Dashboard de maturidade
Reavaliacao periodica
```

O diferencial nao deve ser apenas cadastro ou questionario. O valor principal e:

- identificar riscos reais de uso corporativo de IA;
- explicar consequencias juridicas, financeiras, operacionais e reputacionais;
- gerar plano de mitigacao personalizado;
- acompanhar evolucao de maturidade;
- fundamentar recomendacoes em legislacao e boas praticas.

## Situacao atual

### Infraestrutura e deploy

- [x] Projeto Django configurado.
- [x] Django REST Framework instalado.
- [x] Swagger em `/api/docs/`.
- [x] Health check em `/api/health/`.
- [x] Dockerfile criado.
- [x] Docker Compose com PostgreSQL e Redis.
- [x] Render Blueprint com web service, PostgreSQL e Key Value.
- [x] `main` preparada para producao no Render.
- [x] `develop` usada para desenvolvimento.
- [x] Ambiente local configurado para PostgreSQL.

### Camada de dados

- [x] Usuario customizado em `accounts.User`.
- [x] Multi-tenancy por `Organization` e `Membership`.
- [x] Apps de dominio criados:
  - `accounts`
  - `organizations`
  - `ai_assets`
  - `assessments`
  - `compliance`
  - `evidence`
  - `audit`
  - `analytics`
- [x] Models e migrations iniciais.
- [x] Admin Django basico.
- [x] Endpoints REST iniciais.
- [x] Uso de UUID nas APIs.
- [x] Testes de isolamento por organizacao.
- [x] Seeds iniciais de assessment e controles.
- [x] Checks de qualidade de dados.
- [x] Snapshots de metricas.
- [x] Auditoria de criacoes principais.
- [x] Testes passando.

### O que ainda nao existe como produto usavel

- [ ] Frontend TypeScript.
- [ ] Fluxo guiado de onboarding.
- [ ] Login/registro pensado para usuario final.
- [ ] Convites de usuarios para organizacoes.
- [ ] Interface para o questionario estruturado.
- [ ] Enriquecimento narrativo do plano de mitigacao.
- [ ] Relatorio executivo.
- [ ] Dashboard de maturidade orientado ao usuario.
- [ ] Reavaliacao periodica.
- [ ] Geracao de documentos corporativos.
- [ ] Integracao real com IA generativa.
- [ ] Upload real de evidencias em storage externo.

## Passo concluido mais recente

[x] Criar motor inicial de riscos e plano de mitigacao.

Entregue:

- matriz simples de severidade por `likelihood * impact`;
- regras iniciais que convertem maturidade baixa em `Risk`;
- vinculo automatico entre riscos e controles seedados;
- geracao de `ActionPlan` e `ActionItem`;
- endpoint de geracao de plano de mitigacao por assessment submetido;
- geracao idempotente para evitar duplicidade no mesmo assessment;
- testes de geracao, idempotencia e bloqueio para assessment nao submetido.

## Proximo passo recomendado

[>] Enriquecer plano de mitigacao com indicadores, evidencias esperadas e relatorio executivo.

Motivo:

- o assessment ja gera score, recomendacoes, riscos e plano inicial;
- o diferencial descrito na ideia do produto depende de consequencias
  detalhadas, indicadores de sucesso e evidencias esperadas;
- o relatorio executivo e a proxima forma clara de entregar valor ao usuario.

Escopo recomendado para o proximo PR:

- [ ] Padronizar campos narrativos do plano: objetivo, justificativa,
  beneficios esperados, complexidade, prazo sugerido, areas impactadas,
  indicadores de sucesso e evidencias esperadas.
- [ ] Definir consequencias juridicas, financeiras, operacionais e
  reputacionais por tipo de risco.
- [ ] Criar servico de resumo executivo por assessment.
- [ ] Expor endpoint de relatorio executivo em JSON.
- [ ] Criar testes para conteudo minimo do relatorio e isolamento multi-tenant.
- [ ] Documentar o formato do relatorio em `docs/CAMADA_DADOS.md`.

Entrega minima aceitavel:

- selecionar um assessment submetido;
- retornar resumo executivo;
- listar riscos identificados;
- explicar consequencias por categoria;
- listar acoes de mitigacao com indicadores e evidencias esperadas.

## Roadmap de produto

### Fase 0 - Fundacao tecnica

- [x] Configurar Django, DRF, Swagger e health check.
- [x] Configurar PostgreSQL e Redis local/producao.
- [x] Definir Git Flow.
- [x] Preparar deploy no Render.

Status: feito.

### Fase 1 - Base multi-tenant e inventario

- [x] Criar organizacoes.
- [x] Criar usuarios e perfis.
- [x] Criar memberships.
- [x] Criar inventario de fornecedores, ferramentas, modelos e casos de uso.
- [x] Criar fontes de dados e responsaveis por ativos de IA.
- [ ] Criar convites de usuarios para organizacoes.
- [ ] Criar permissoes por papel com regras de produto.

Status: base pronta; convites e permissoes finas pendentes.

### Fase 2 - Avaliacao guiada

- [x] Criar modelos de framework, dimensoes, perguntas, assessments e respostas.
- [x] Criar seed inicial de framework.
- [x] Completar questionario do MVP.
- [x] Validar obrigatoriedade de campos descritivos.
- [x] Criar endpoints de fluxo guiado, alem do CRUD generico.
- [x] Calcular score automaticamente.
- [x] Gerar recomendacoes iniciais.

Status: backend do fluxo guiado pronto; frontend pendente.

### Fase 3 - Riscos e plano de mitigacao

- [x] Criar modelos de riscos, controles, politicas, planos e itens de acao.
- [x] Criar seed inicial de controles.
- [x] Derivar `Risk.severity` automaticamente por `likelihood` e `impact`.
- [x] Criar motor de regras simples para gerar riscos a partir de respostas.
- [x] Gerar plano de mitigacao inicial por risco.
- [>] Criar indicadores de sucesso e evidencias esperadas por acao.

Status: motor inicial pronto; enriquecimento do plano e relatorio pendentes.

### Fase 4 - Relatorio e dashboard

- [x] Criar modelos e endpoints basicos de analytics.
- [x] Criar `/api/metrics/overview/`.
- [>] Criar resumo executivo da avaliacao.
- [ ] Criar endpoint de dashboard de maturidade.
- [ ] Criar serie historica de reavaliacoes.
- [ ] Expor riscos por severidade, status, area e ferramenta.

Status: base pronta; visao executiva pendente.

### Fase 5 - Auditoria, evidencias e compliance operacional

- [x] Criar eventos de auditoria.
- [x] Criar logs de mudanca para criacoes.
- [x] Criar evidencias por link externo.
- [ ] Auditar updates relevantes, principalmente mudancas de status.
- [ ] Definir politica de retencao.
- [ ] Implementar upload real em storage externo.
- [ ] Criar revisoes de evidencias com fluxo de aprovacao.

Status: MVP tecnico pronto; governanca operacional pendente.

### Fase 6 - Frontend

- [ ] Escolher Vite/React ou Next.js.
- [ ] Criar estrutura `frontend/`.
- [ ] Criar login.
- [ ] Criar onboarding de organizacao.
- [ ] Criar inventario de IA.
- [ ] Criar avaliacao guiada.
- [ ] Criar dashboard.
- [ ] Criar relatorio executivo.

Status: nao iniciado.

### Fase 7 - IA e documentos corporativos

- [ ] Definir provedores de IA.
- [ ] Criar templates base de documentos.
- [ ] Criar motor de regras para clausulas.
- [ ] Usar IA generativa apenas para personalizacao controlada.
- [ ] Gerar politica corporativa de uso de IA.
- [ ] Gerar procedimento de anonimizacao.
- [ ] Gerar plano de resposta a incidentes.
- [ ] Permitir upload de documentos existentes para analise de lacunas.

Status: futuro; deve vir depois do MVP de avaliacao.

## Backlog tecnico imediato

- [>] Commitar ajustes locais de PostgreSQL e `.env` loading.
- [x] Atualizar documentacao de setup local para PostgreSQL em `README.md`.
- [x] Atualizar `STATUS_CAMADA_DADOS.md` para refletir merge em `develop` e 72
  testes.
- [ ] Criar PR de `develop` para `main` quando a camada de dados estiver pronta
  para producao.
- [ ] Criar superuser local.
- [ ] Rodar seeds no banco local.

## Definicao de pronto para o MVP

O MVP deve permitir que uma empresa:

- cadastre sua organizacao;
- cadastre ferramentas e casos de uso de IA;
- responda um questionario estruturado;
- informe descricoes sobre finalidade e dados compartilhados;
- receba score inicial de maturidade;
- visualize riscos e recomendacoes;
- gere um plano de mitigacao inicial;
- acompanhe a evolucao em um dashboard simples.

## Decisoes pendentes

- O frontend sera Vite/React ou Next.js?
- O login do MVP sera session auth, token auth, JWT ou provedor externo?
- Quais papeis reais existirao alem de owner, admin, member e auditor?
- Qual framework sera o primeiro oficial: LGPD + boas praticas internas,
  NIST AI RMF, OECD AI Principles ou uma combinacao?
- O MVP tera apenas evidencias por link ou tambem upload?
- O relatorio sera gerado em HTML, PDF ou ambos?
- A primeira integracao de IA sera para recomendacoes, relatorio ou documentos?
