# CLAUDE.md

Notas para a próxima sessão do Claude Code neste repositório.

## Idioma

O usuário fala português. Responda em português.

## Stack (resumo)

- **Frontend**: React 19 + CRA/craco + React Router 7 + TanStack Query 5 + Tailwind/shadcn + framer-motion (em `frontend/`).
- **Backend**: FastAPI + Motor (Mongo async) + slowapi + JWT em cookie httpOnly (em `backend/app/`).
- **Banco**: MongoDB 7.
- **Deploy**: imagem única (`Dockerfile.deploy`) que faz build do SPA com yarn e serve pelo FastAPI; alvo é Fly.io (`fly.toml`) + MongoDB Atlas. CI em `.github/workflows/ci.yml`.

`backend/server.py` é só um shim que importa `app.main:app`.

## Comandos mais usados

```powershell
docker compose up                                  # tudo (front:3000, back:8000, mongo:27017)
docker compose up backend mongo                    # só back + db (rodar front nativo é mais rápido)
docker compose exec backend python -m scripts.seed # popula o banco
docker compose exec backend python -m pytest -v    # testa backend
docker compose down -v                             # derruba + apaga volume do mongo
```

Frontend nativo: `cd frontend && yarn install && yarn start`.

## Convenções a respeitar

- **Cookies httpOnly para JWT**, não localStorage. `frontend/src/lib/api.js` faz refresh transparente em 401.
- **Mesma origem em prod** (FastAPI serve o build do SPA). CORS só é relevante em dev.
- **Repositories + services**: routers chamam services, services chamam repositories. Não acessar `db` direto no router.
- **Mongo nos testes é real**, não mock — `backend/tests/conftest.py` usa um banco isolado por sessão. Não introduzir mocks aqui.
- **Sinais**: nomes em kebab-case (`bom-dia`, `tudo-bem`). Os SVGs em `backend/static/signs/` são gerados por `backend/scripts/build_sign_assets.py`; servidos em `/signs/<nome>.svg`.

## Pegadinhas / decisões fixas

- **VLibras está morto**. O player 3D oficial (`vlibras-player-webjs`) e o proxy `backend/app/routers/vlibras.py` foram removidos em 2026-05-26 porque `vlibras.gov.br/dict-static` responde 403 sem mirror público. O `LibrasButton` atual abre um `<Dialog>` com o SVG estático. **Não tentar reativar.** Alternativas viáveis: hostar bundles localmente (se conseguir os `.bundle`), ou trocar por outro avatar 3D.
- **CRA + craco**, não Vite. Não migrar sem combinar.
- **Yarn 1**, não npm. `yarn.lock` é o lockfile autoritativo.
- **`min_machines_running = 0`** no `fly.toml` (cold start ~5-15s). Já discutido como trade-off de custo; mudar só se acordado.

## Workflow de sprints

Quando há um plano de múltiplos sprints já acordado: terminou um sprint → `docker compose build` + `up` + verificar → próximo sprint na mesma volta. Não pedir confirmação entre sprints já planejados. Pausar só se: erro no docker, decisão nova não prevista, ou bug encontrado.

Sprints que só mexem em docs (README, este arquivo) podem pular o `docker compose` — não há código para verificar.

## Onde olhar

| Procurando… | Comece por… |
|---|---|
| Login / refresh / cookies | `backend/app/services/auth_service.py`, `backend/app/routers/auth.py`, `frontend/src/context/AuthContext.jsx`, `frontend/src/lib/api.js` |
| XP / streak / lições concluídas | `backend/app/services/progress_service.py`, `frontend/src/lib/hooks/useLearning.js` |
| Layout / shell / nav | `frontend/src/components/AppShell.jsx`, `Header.jsx`, `Sidebar.jsx`, `BottomNav.jsx` |
| Sinais / dicionário | `backend/app/repositories/sign_repo.py`, `frontend/src/pages/Dictionary.jsx`, `frontend/src/lib/hooks/useSearchSigns.js` |
| Configuração / env | `backend/app/core/config.py`, `backend/.env.example`, `frontend/src/lib/env.js`, `frontend/.env.example` |
