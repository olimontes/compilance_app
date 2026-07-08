# Frontend

Primeira interface web do Compliance App / AI Governance API.

Stack:

- Vite
- React
- TypeScript

## Rodar local

Com o backend Django rodando em `http://127.0.0.1:8000`:

```bash
cd frontend
npm install
npm run dev
```

Acesse:

```text
http://127.0.0.1:5173
```

Em desenvolvimento, o Vite faz proxy de `/api` para o Django local.

## Autenticacao atual

A tela usa Basic Auth de desenvolvimento, aproveitando a autenticacao ja
habilitada no Django REST Framework.

Para usar:

1. Crie um usuario no Django Admin ou via `createsuperuser`.
2. Garanta que o usuario tenha `Membership` ativo em uma organizacao.
3. Rode os seeds:

```bash
python manage.py seed_assessment_frameworks
python manage.py seed_controls --organization-slug=<slug-da-organizacao>
```

Depois informe usuario e senha na tela inicial do frontend.

## Build

```bash
npm run build
```

## API remota

Para apontar para uma API remota, crie `frontend/.env`:

```text
VITE_API_BASE_URL=https://<api-domain>/api
```
