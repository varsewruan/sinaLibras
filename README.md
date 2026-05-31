# SINALibras

Aplicativo de aprendizado de Libras (Língua Brasileira de Sinais) no estilo Duolingo — fases, lições com exercícios, dicionário pesquisável, sequência (streak) e XP.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React 19, CRA + craco, React Router 7, TanStack Query 5, Tailwind + shadcn/ui (Radix), framer-motion, axios |
| Backend | FastAPI, Motor (MongoDB assíncrono), pydantic-settings, slowapi (rate limit), JWT em cookie httpOnly |
| Banco | MongoDB 7 |
| Infra | Docker Compose (dev), Fly.io + MongoDB Atlas (prod), GitHub Actions (CI) |

## Subir o ambiente de dev

Pré-requisitos: Docker Desktop.

```powershell
docker compose up
```

- Frontend: http://localhost:3000
- Backend:  http://localhost:8000 (Swagger em `/docs`)
- Mongo:    localhost:27017

O primeiro boot baixa imagens e instala `node_modules` (lento). Boots seguintes são rápidos por causa do volume nomeado `frontend-node-modules`.

Subir só o backend + banco (e rodar o frontend nativo, mais rápido pra desenvolver UI):

```powershell
docker compose up backend mongo
cd frontend
yarn install
yarn start
```

### Popular o banco com dados de exemplo

```powershell
docker compose exec backend python -m scripts.seed
# Saída esperada: seeded 3 phases / 9 lessons / 36 signs
```

Reset (apaga e repopula):

```powershell
docker compose exec backend python -m scripts.seed --reset
```

## Rodar os testes

Backend (pytest contra um Mongo real):

```powershell
docker compose exec backend python -m pytest -v
```

Ou nativo, se preferir:

```powershell
cd backend
pip install -r requirements.txt
$env:MONGO_URL = "mongodb://localhost:27017"
$env:JWT_SECRET = "test-secret-pelo-menos-32-caracteres-aqui"
python -m pytest -v
```

## Estrutura

```
backend/
  app/
    main.py              # create_app factory + lifespan
    core/                # config, logging, security, rate limit
    db/mongo.py          # cliente Motor + índices
    models/              # schemas Pydantic
    repositories/        # acesso a dados (um por agregado)
    services/            # regras de negócio (auth, learning, progress)
    routers/             # endpoints (/api/auth, /api/learning, /api/progress, /api/status, /api/healthz)
  scripts/
    seed.py              # popula o banco
    build_sign_assets.py # gera os SVGs de fallback dos sinais
  static/signs/          # SVGs dos 36 sinais (gerados; servidos em /signs/*)
  tests/                 # pytest — usa Mongo real (não mocks)

frontend/
  src/
    App.js               # rotas + AnimatePresence
    context/             # AuthContext
    components/          # AppShell, Header, Sidebar, BottomNav, LibrasButton, ProtectedRoute + ui/
    pages/               # Login, Register, Home, Lessons, Lesson, Dictionary, Profile
    lib/
      api.js             # axios wrapper com refresh em 401
      query.js           # QueryClient
      env.js             # valida REACT_APP_BACKEND_URL no boot
      hooks/             # useLearning, useSummary, useSearchSigns, useDebouncedValue
```

## Deploy em produção

Ver [DEPLOY.md](./DEPLOY.md) — guia passo a passo para Fly.io + MongoDB Atlas (free tier). A imagem final (`Dockerfile.deploy`) serve SPA e API no mesmo host (sem CORS).

## Notas

- **VLibras**: o player 3D oficial foi removido em 2026-05-26 — o endpoint `vlibras.gov.br/dict-static` está respondendo 403 e não há mirror público. O `LibrasButton` hoje abre um modal com um SVG estático (gerado por `scripts/build_sign_assets.py`). Não tentar reativar.
- **Cookies / CORS**: a API usa cookies `httpOnly` para os JWTs. Em produção, mesma origem = sem CORS. Em dev, `CORS_ORIGINS=http://localhost:3000` é setado no `docker-compose.yml`.
- **Rate limit**: `slowapi` em `/api/auth/login`, `/register`, `/refresh`. Configurável em `backend/.env`.
