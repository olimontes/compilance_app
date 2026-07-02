# Guia de commits e submissao com Git Flow

Este projeto usa um fluxo inspirado em Git Flow para manter separacao clara entre
desenvolvimento, preparacao de release e codigo estavel para deploy.

## Branches principais

- `main`: codigo estavel, pronto para deploy em producao.
- `develop`: codigo integrado de desenvolvimento, base para novas funcionalidades.

Regra geral:

- Nao desenvolver diretamente na `main`.
- Evitar commits diretos na `develop`.
- Toda alteracao deve sair de uma branch temporaria e voltar por pull request.

## Branches temporarias

Use estes prefixos:

- `feature/<nome-curto>`: nova funcionalidade.
- `fix/<nome-curto>`: correcao que ainda pode passar pela `develop`.
- `release/<versao>`: preparacao de uma versao para producao.
- `hotfix/<nome-curto>`: correcao urgente feita a partir da `main`.

Exemplos:

```bash
feature/cadastro-organizacoes
fix/healthcheck-database
release/0.1.0
hotfix/cors-producao
```

## Antes de comecar uma tarefa

Atualize a branch base:

```bash
git switch develop
git pull origin develop
```

Crie uma branch da tarefa:

```bash
git switch -c feature/nome-da-tarefa
```

Para hotfix urgente de producao, use `main` como base:

```bash
git switch main
git pull origin main
git switch -c hotfix/nome-da-correcao
```

## Padrao de commits

Prefira commits pequenos, coesos e com uma unica intencao.

Formato recomendado:

```text
tipo(escopo): descricao curta no imperativo
```

Tipos sugeridos:

- `feat`: nova funcionalidade.
- `fix`: correcao de bug.
- `docs`: mudanca de documentacao.
- `test`: testes novos ou alterados.
- `refactor`: melhoria interna sem mudar comportamento.
- `chore`: tarefas de manutencao, configuracao ou build.
- `ci`: pipeline, automacao e integracao continua.

Exemplos:

```bash
git commit -m "feat(health): add readiness endpoint"
git commit -m "fix(settings): require secret key in production"
git commit -m "docs(gitflow): document submission workflow"
git commit -m "test(health): cover degraded database response"
```

Evite mensagens vagas:

```text
ajustes
update
correcao
mudancas finais
```

## Checklist antes de cada commit

Confira os arquivos alterados:

```bash
git status --short
git diff
```

Rode os testes do projeto:

```bash
python manage.py test
```

Adicione somente arquivos relacionados a tarefa:

```bash
git add caminho/do/arquivo.py
git commit -m "tipo(escopo): descricao objetiva"
```

Depois confirme que o workspace ficou como esperado:

```bash
git status --short
```

## Submissao para o GitHub

Envie a branch temporaria:

```bash
git push -u origin feature/nome-da-tarefa
```

Abra um pull request no GitHub:

- `feature/*` ou `fix/*` deve apontar para `develop`.
- `release/*` deve apontar para `main`.
- `hotfix/*` deve apontar para `main`.

No pull request, informe:

- O que mudou.
- Como foi testado.
- Impactos em migracoes, variaveis de ambiente ou deploy.
- Prints ou exemplos de resposta da API quando forem uteis.

## Fluxo de feature

```bash
git switch develop
git pull origin develop
git switch -c feature/nome-da-tarefa

# editar arquivos
python manage.py test
git status --short
git add .
git commit -m "feat(escopo): descricao da tarefa"
git push -u origin feature/nome-da-tarefa
```

Depois, abra PR para `develop`.

## Fluxo de release

Quando a `develop` estiver pronta para deploy:

```bash
git switch develop
git pull origin develop
git switch -c release/0.1.0
```

Na branch `release/*`, faca apenas ajustes finais:

- versao;
- documentacao;
- pequenos fixes;
- validacoes de deploy.

Depois abra PR de `release/0.1.0` para `main`.

Apos merge em `main`, sincronize `develop` com o que foi para producao:

```bash
git switch develop
git pull origin develop
git merge origin/main
git push origin develop
```

Crie uma tag para a versao publicada:

```bash
git switch main
git pull origin main
git tag -a v0.1.0 -m "Release 0.1.0"
git push origin v0.1.0
```

## Fluxo de hotfix

Para correcao urgente em producao:

```bash
git switch main
git pull origin main
git switch -c hotfix/nome-da-correcao

# corrigir
python manage.py test
git add .
git commit -m "fix(escopo): descricao da correcao"
git push -u origin hotfix/nome-da-correcao
```

Abra PR para `main`.

Apos o merge em `main`, leve a correcao tambem para `develop`:

```bash
git switch develop
git pull origin develop
git merge origin/main
git push origin develop
```

## Deploy

Deploy de producao deve usar a branch `main`.

Deploys de homologacao ou ambiente de testes podem usar `develop`, se a plataforma
de deploy permitir ambientes separados.

Nunca faca deploy de producao a partir de `feature/*`, `fix/*`, `release/*` ou
`hotfix/*`.

## Regras de ouro

- Um commit deve representar uma mudanca compreensivel.
- Uma branch temporaria deve representar uma tarefa.
- Um pull request deve explicar o motivo da mudanca e como validar.
- `main` deve estar sempre pronta para deploy.
- `develop` deve estar sempre funcional para o time continuar trabalhando.
