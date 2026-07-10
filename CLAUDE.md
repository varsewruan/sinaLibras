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
docker compose exec backend python -m scripts.seed # popula o banco (fases/lições/sinais)
docker compose exec backend python -m scripts.seed --demo-users  # + ~10 jogadores fake p/ o ranking
docker compose exec backend python -m pytest -v    # testa backend
docker compose down -v                             # derruba + apaga volume do mongo
```

`--demo-users` é **opt-in e nunca deve rodar em produção**. Os fakes recebem senha
aleatória (ninguém loga como eles) e são idempotentes por e-mail (`*@demo.sinalibras.dev`).

Frontend nativo: `cd frontend && yarn install && yarn start`.

## Convenções a respeitar

- **Cookies httpOnly para JWT**, não localStorage. `frontend/src/lib/api.js` faz refresh transparente em 401.
- **Mesma origem em prod** (FastAPI serve o build do SPA). CORS só é relevante em dev.
- **Repositories + services**: routers chamam services, services chamam repositories. Não acessar `db` direto no router.
- **Mongo nos testes é real**, não mock — `backend/tests/conftest.py` usa um banco isolado por sessão. Não introduzir mocks aqui.
- **Sinais**: nomes em kebab-case (`bom-dia`, `tudo-bem`). Os SVGs em `backend/static/signs/` são gerados por `backend/scripts/build_sign_assets.py`; servidos em `/signs/<nome>.svg`.
- **Avatares**: o allowlist vive no backend (`app/models/user.py::AVATAR_IDS`) e é a autoridade — um id fora dele nunca é persistido (422). O frontend (`frontend/src/lib/avatars.js`) só mapeia id → gradiente + emoji. **Manter as duas listas em sync**; não há assets de imagem.

## Pegadinhas / decisões fixas

- **O tema é DARK** (navy) desde 2026-07-09, replicando o mockup do usuário. Tudo sai dos CSS vars em `frontend/src/index.css` (`:root`) — trocar os valores lá vira o app inteiro, nenhum className muda. `darkMode: "class"` existe no tailwind mas **não é usado**: nunca setamos `.dark`.
- **Conquistas são derivadas, não armazenadas**: `achievement_service` avalia o catálogo contra xp/streak-mais-longo/lições-concluídas a cada request. Não existe registro de "desbloqueou em X". Se precisar da data, criar coleção de unlocks — não dá pra recuperar retroativamente.
- **Streak das conquistas usa `streak.longest`**, não `current` — senão a medalha some no dia em que o usuário perde a sequência.
- **Ranking usa "competition ranking"**: empatados em XP dividem o mesmo rank (1,2,2,4). Isso é obrigatório — o rank de quem está *fora* da página é derivado de `count_with_more_xp`, e um `enumerate()` posicional faria o mesmo usuário ver números diferentes conforme o `limit`. Ver `_competition_ranks` + `test_own_rank_does_not_depend_on_limit`.
- **O bloqueio das lições no caminho é só UI.** `/lesson/:id` continua acessível direto; o conteúdo é público, não há o que proteger no servidor.
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
| Layout / shell / nav | `frontend/src/components/AppShell.jsx`, `Header.jsx`, `Sidebar.jsx`, `BottomNav.jsx`, `lib/nav-items.js` |
| Tema / cores / glow | `frontend/src/index.css` (`:root`), `frontend/tailwind.config.js` |
| Avatar do usuário | `backend/app/models/user.py` (`AVATAR_IDS`), `routers/users.py`, `frontend/src/lib/avatars.js`, `components/UserAvatar.jsx` |
| Ranking | `backend/app/services/ranking_service.py`, `frontend/src/pages/Ranking.jsx` |
| Conquistas | `backend/app/models/achievement.py` (catálogo), `services/achievement_service.py`, `frontend/src/pages/Achievements.jsx` |
| Caminho de fases (estilo Duolingo) | `frontend/src/pages/Lessons.jsx`, `components/LessonNode.jsx`, `components/PhaseBanner.jsx` |
| Nível / gemas a partir do XP | `frontend/src/lib/level.js` |
| Sinais / dicionário | `backend/app/repositories/sign_repo.py`, `frontend/src/pages/Dictionary.jsx`, `frontend/src/lib/hooks/useSearchSigns.js` |
| Configuração / env | `backend/app/core/config.py`, `backend/.env.example`, `frontend/src/lib/env.js`, `frontend/.env.example` |
| Rodar / verificar o app end-to-end | `.claude/skills/run-app/SKILL.md` (docker + seed + dirige o SPA no Chromium) + `drive.js` |
