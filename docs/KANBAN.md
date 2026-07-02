# Kanban do projeto

Este quadro organiza a execucao do Compliance App / AI Governance API. Ele deve
ser atualizado a cada mudanca relevante de status, seguindo o fluxo Git Flow do
repositorio.

## Como usar

- Cada item representa um card de trabalho.
- Ao iniciar uma tarefa, mova o card de `A fazer` para `Em andamento`.
- Ao abrir pull request ou pedir revisao, mova para `Em revisao`.
- Ao mergear e validar, mova para `Concluido`.
- Cards bloqueados devem ir para `Bloqueado` com motivo claro.
- Todo card de codigo deve terminar com testes passando.

## Legenda

Prioridade:

- `P0`: bloqueia o inicio ou o deploy.
- `P1`: essencial para o MVP.
- `P2`: importante, mas pode vir depois da base.
- `P3`: melhoria futura.

Tipo:

- `data`: modelagem, migrations, qualidade e governanca de dados.
- `backend`: Django, API, permissions e serializers.
- `frontend`: TypeScript e experiencia de usuario.
- `infra`: deploy, ambientes e operacao.
- `docs`: documentacao e processos.
- `qa`: testes, validacao e qualidade.

## Backlog

### DATA-010 - Definir framework inicial de governanca de IA

- Prioridade: `P1`
- Tipo: `data`
- Responsavel: Engenheiro de dados + Produto
- Descricao: escolher o primeiro framework de avaliacao que sera cadastrado no
  sistema.
- Entregaveis:
  - lista de dimensoes;
  - lista inicial de perguntas;
  - criterio de pontuacao;
  - versao inicial do framework.
- Pronto quando:
  - estrutura estiver documentada;
  - perguntas estiverem aptas para virar seed/migration.

### DATA-011 - Definir taxonomia de riscos e controles

- Prioridade: `P1`
- Tipo: `data`
- Responsavel: Engenheiro de dados
- Descricao: padronizar nomes, severidade, status e dominios de controle.
- Entregaveis:
  - status de risco;
  - escala de likelihood;
  - escala de impact;
  - matriz de severidade;
  - dominios de controle.
- Pronto quando:
  - taxonomia estiver versionada em docs;
  - valores estiverem prontos para seeds.

### DATA-012 - Definir politica de retencao de dados

- Prioridade: `P2`
- Tipo: `data`
- Responsavel: Engenheiro de dados + Produto
- Descricao: documentar o tempo de retencao de auditoria, evidencias, logs e
  respostas de assessment.
- Entregaveis:
  - matriz de retencao;
  - dados que podem ser apagados;
  - dados que devem ser anonimizados;
  - eventos que devem ser preservados.
- Pronto quando:
  - regras estiverem documentadas;
  - impactos em LGPD estiverem mapeados.

### BACKEND-020 - Implementar endpoints de inventario de IA

- Prioridade: `P1`
- Tipo: `backend`
- Responsavel: Backend
- Descricao: criar APIs para fornecedores, ferramentas e casos de uso de IA.
- Dependencias:
  - `DATA-004`
  - `BACKEND-004`
- Pronto quando:
  - endpoints CRUD existirem;
  - filtros por organizacao, status e risco existirem;
  - Swagger mostrar contratos;
  - testes cobrirem isolamento por organizacao.

### BACKEND-021 - Implementar endpoints de assessments

- Prioridade: `P1`
- Tipo: `backend`
- Responsavel: Backend
- Descricao: criar APIs para frameworks, perguntas, assessments e respostas.
- Dependencias:
  - `DATA-005`
  - `BACKEND-004`
- Pronto quando:
  - assessment puder ser iniciado;
  - respostas puderem ser salvas;
  - score inicial puder ser calculado;
  - testes cobrirem fluxo principal.

### FRONTEND-001 - Definir stack do frontend TypeScript

- Prioridade: `P1`
- Tipo: `frontend`
- Responsavel: Frontend + Produto
- Descricao: decidir entre Vite/React e Next.js.
- Entregaveis:
  - decisao documentada;
  - estrutura inicial do projeto frontend;
  - variavel de ambiente para API.
- Pronto quando:
  - app inicial renderizar;
  - deploy escolhido estiver documentado.

### INFRA-010 - Planejar migracao para banco persistente

- Prioridade: `P2`
- Tipo: `infra`
- Responsavel: Infra + Dados
- Descricao: definir quando sair do Postgres free do Render.
- Pronto quando:
  - plano de migracao estiver documentado;
  - custo estimado estiver aprovado;
  - estrategia de backup/restore estiver definida.

## A fazer

### DATA-001 - Decidir modelo de usuario

- Prioridade: `P0`
- Tipo: `data`
- Responsavel: Backend + Dados
- Descricao: decidir se o projeto usara `AUTH_USER_MODEL` customizado antes de
  criar migrations de dominio.
- Entregaveis:
  - decisao documentada;
  - impacto em `accounts` definido;
  - caminho de migration definido.
- Pronto quando:
  - decisao estiver registrada;
  - `settings.py` estiver pronto para a abordagem escolhida;
  - riscos de troca futura estiverem claros.

### DATA-002 - Criar app comum de modelos base

- Prioridade: `P0`
- Tipo: `data`
- Responsavel: Backend + Dados
- Descricao: criar app tecnico para mixins e utilitarios comuns.
- Entregaveis:
  - app `apps/common` ou equivalente;
  - mixin com `uuid`, `created_at`, `updated_at`;
  - testes basicos.
- Pronto quando:
  - app estiver em `INSTALLED_APPS`;
  - mixin estiver reutilizavel;
  - testes passarem.

### DATA-003 - Criar base de organizacoes e membership

- Prioridade: `P0`
- Tipo: `data`
- Responsavel: Engenheiro de dados + Backend
- Descricao: implementar `Organization`, `OrganizationUnit` e `Membership`.
- Dependencias:
  - `DATA-001`
  - `DATA-002`
- Entregaveis:
  - models;
  - migrations;
  - admin Django;
  - constraints basicas.
- Pronto quando:
  - `python manage.py test` passar;
  - organizacao puder ser criada no admin;
  - membership ligar usuario e organizacao;
  - constraints impedirem duplicidade obvia.

### DATA-004 - Criar inventario inicial de IA

- Prioridade: `P1`
- Tipo: `data`
- Responsavel: Engenheiro de dados
- Descricao: modelar fornecedores, ferramentas e casos de uso de IA.
- Dependencias:
  - `DATA-003`
- Entregaveis:
  - `AiVendor`;
  - `AiTool`;
  - `AiUseCase`;
  - migrations;
  - admin.
- Pronto quando:
  - entidades estiverem ligadas a organizacao;
  - filtros esperados estiverem mapeados;
  - testes cobrirem criacao basica.

### DATA-005 - Criar estrutura de assessment versionado

- Prioridade: `P1`
- Tipo: `data`
- Responsavel: Engenheiro de dados
- Descricao: criar tabelas para framework, dimensoes, perguntas, assessments e
  respostas.
- Dependencias:
  - `DATA-003`
  - `DATA-010`
- Entregaveis:
  - models;
  - migrations;
  - admin;
  - seed inicial planejado.
- Pronto quando:
  - perguntas apontarem para framework e dimensao;
  - assessment guardar respostas;
  - versionamento basico estiver definido.

### DATA-006 - Criar modelo de auditoria append-only

- Prioridade: `P1`
- Tipo: `data`
- Responsavel: Engenheiro de dados + Backend
- Descricao: criar `AuditEvent` para registrar eventos relevantes do dominio.
- Dependencias:
  - `DATA-003`
- Entregaveis:
  - model `AuditEvent`;
  - indices por organizacao e data;
  - helper de registro de evento;
  - testes.
- Pronto quando:
  - eventos puderem ser criados;
  - eventos nao exigirem usuario sempre;
  - metadata nao armazenar segredos.

### BACKEND-001 - Criar permissoes multi-tenant

- Prioridade: `P0`
- Tipo: `backend`
- Responsavel: Backend
- Descricao: garantir que usuarios so acessem dados das organizacoes em que sao
  membros.
- Dependencias:
  - `DATA-003`
- Entregaveis:
  - permissions DRF;
  - querysets filtrados por organizacao;
  - testes de acesso cruzado.
- Pronto quando:
  - usuario de uma organizacao nao conseguir listar dados de outra;
  - testes cobrirem positivo e negativo.

### QA-001 - Criar matriz de testes inicial

- Prioridade: `P1`
- Tipo: `qa`
- Responsavel: Backend + Dados
- Descricao: definir testes minimos por app de dominio.
- Entregaveis:
  - matriz em docs;
  - padrao de testes por model;
  - padrao de testes por endpoint.
- Pronto quando:
  - houver checklist reutilizavel;
  - Fase 1 estiver coberta.

## Em andamento

### DOCS-001 - Manter documentacao de execucao do projeto

- Prioridade: `P1`
- Tipo: `docs`
- Responsavel: Produto + Engenharia
- Descricao: manter `README.md`, `docs/PLANO_DADOS.md`, `docs/GITFLOW.md` e este
  kanban atualizados.
- Pronto quando:
  - documentos refletirem o estado real do projeto;
  - links principais estiverem no README.

## Em revisao

Nenhum card em revisao no momento.

## Bloqueado

### INFRA-001 - Worker Celery em producao gratuita

- Prioridade: `P2`
- Tipo: `infra`
- Responsavel: Infra
- Motivo do bloqueio: Render free tier nao oferece worker gratuito.
- Impacto:
  - jobs assincronos devem ficar fora do MVP gratuito;
  - rotinas podem ser executadas manualmente por management command;
  - quando houver necessidade real, migrar para plano pago ou outro provedor.
- Desbloqueia quando:
  - houver aprovacao de custo;
  - ou for escolhido provedor alternativo gratuito para jobs.

### INFRA-002 - Banco persistente de producao

- Prioridade: `P1`
- Tipo: `infra`
- Responsavel: Infra + Dados
- Motivo do bloqueio: Postgres free do Render expira em 30 dias.
- Impacto:
  - nao usar para dados reais permanentes;
  - MVP pode validar fluxo, mas nao armazenar operacao critica.
- Desbloqueia quando:
  - houver decisao sobre banco pago;
  - backup e restore estiverem definidos.

## Concluido

### DOCS-000 - Criar plano de dados

- Prioridade: `P1`
- Tipo: `docs`
- Responsavel: Engenharia
- Resultado:
  - `docs/PLANO_DADOS.md` criado;
  - README raiz atualizado;
  - `docs/README.md` atualizado.

### INFRA-000 - Deploy gratuito inicial no Render

- Prioridade: `P0`
- Tipo: `infra`
- Responsavel: Engenharia
- Resultado:
  - Blueprint aplicado;
  - Postgres free criado;
  - Redis/Key Value free criado;
  - web service Django no ar;
  - `/api/health/` validado.

### DOCS-002 - Criar guia Git Flow

- Prioridade: `P1`
- Tipo: `docs`
- Responsavel: Engenharia
- Resultado:
  - `docs/GITFLOW.md` criado;
  - processo de branches e commits documentado.

## Proxima sprint sugerida

Objetivo: entregar a base multi-tenant e preparar o projeto para dados reais de
dominio.

Cards sugeridos:

1. `DATA-001`
2. `DATA-002`
3. `DATA-003`
4. `BACKEND-001`
5. `QA-001`

Resultado esperado:

- projeto com base de organizacoes;
- usuario associado a organizacao;
- isolamento multi-tenant testado;
- padrao de models definido;
- proximo passo pronto para inventario de IA.

## Rotina recomendada

Diariamente:

- revisar cards em andamento;
- atualizar bloqueios;
- garantir que cada branch tenha um card associado.

A cada merge em `develop`:

- atualizar status do card;
- rodar `python manage.py test`;
- atualizar documentacao quando uma decisao mudar.

A cada merge em `main`:

- validar deploy no Render;
- testar `/api/health/`;
- registrar no card de release ou deploy.
