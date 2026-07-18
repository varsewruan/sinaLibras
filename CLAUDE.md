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

# transcodifica os .mov crus -> webm+mp4+poster (roda NATIVO, precisa de ffmpeg)
cd backend; python -m scripts.build_sign_videos --src "<pasta dos .mov>" --list
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
- **Vídeos de sinais**: 13 dos 37 termos têm filmagem real (`backend/static/signs/video/`, ~2 MB commitado). O resto usa o SVG. Quem decide entre os dois é `frontend/src/components/SignMedia.jsx` — **não colocar `<video>` ou `<img>` de sinal direto numa página**, use esse componente.
- **Avatares**: o allowlist vive no backend (`app/models/user.py::AVATAR_IDS`) e é a autoridade — um id fora dele nunca é persistido (422). O frontend (`frontend/src/lib/avatars.js`) só mapeia id → gradiente + emoji. **Manter as duas listas em sync**; não há assets de imagem. São 18 ids: 10 animais (2026-07-18, da folha de referência), `dummy`, e 7 presets antigos **mantidos de propósito** para não trocar o avatar de quem já escolheu.

## Pegadinhas / decisões fixas

- **O tema é DARK** (navy) desde 2026-07-09, replicando o mockup do usuário. Tudo sai dos CSS vars em `frontend/src/index.css` (`:root`) — trocar os valores lá vira o app inteiro, nenhum className muda. `darkMode: "class"` existe no tailwind mas **não é usado**: nunca setamos `.dark`.
- **Amarelo é a cor secundária** desde 2026-07-18, pareado com o azul como na paleta do Gartic. A regra que decide qual usar: **superfície é azul, prêmio é amarelo.** Estrutura (cards, nav, banners de fase em andamento) fica azul; recompensa e chamada pra ação (estrelas, XP, streak, nó atual do caminho, fase concluída, o único CTA da tela) fica amarelo. `--secondary` no `:root` **é** o amarelo — antes era um segundo navy que nenhum componente usava; o navy sobrou como `--panel`. Tokens: `brand.yellow` / `-light` / `-dark`, `shadow-glow-yellow[-lg]`, variante `yellow3d` do Button.
  - **Amarelo só marca um alvo por tela.** Dois elementos amarelos e ele para de significar "aperte aqui".
- **Não existe sidebar** (removida em 2026-07-18): a Home concentra todos os pontos de entrada, e uma segunda barra fixa dizia a mesma coisa duas vezes. **Cuidado ao mexer no Header**: com a sidebar fora, a marca do Header é o *único* caminho de volta pro início no desktop (o `BottomNav` é `lg:hidden`). Escondê-la deixa o usuário preso na página em que clicou. O streak também migrou pra lá — era o único conteúdo exclusivo da sidebar.
- **A Home é um grid de 6 tiles, sem botão JOGAR** (mockup de 2026-07-18). Loja e Vídeo Aulas são tiles "Em breve" (sem backend). O CTA que retoma a próxima lição é o `cta-comecar`, na página **Aprender** — quem mexer na Home precisa lembrar que `drive.js` da skill `run-app` navega por esses testids.
- **`HubTile` (Home) e `FeatureCard` (Aprender) são separados de propósito** — um é ícone grande centralizado sem descrição, o outro é card alinhado à esquerda com descrição. Unificar exigiria uma prop que reescreve o corpo inteiro.
- **As estrelas do caminho são a nota real, e não custaram backend nenhum.** `progress_service.complete_lesson` já guardava a **melhor** nota por lição, e `LessonSummary.score` já vinha em `/learning/phases`. `frontend/src/lib/stars.js` só traduz: >=90 → 3, >=70 → 2, passou (>=60, o `PASS_THRESHOLD`) → 1. Como é a melhor nota, estrela **nunca regride** — e rejogar melhora a estrela sem dar XP de novo. **Só lição concluída desenha estrelas**; fileira vazia diria "você tirou zero" em vez de "você ainda não veio aqui".
- **Conquistas são derivadas, não armazenadas**: `achievement_service` avalia o catálogo contra xp/streak-mais-longo/lições-concluídas a cada request. Não existe registro de "desbloqueou em X". Se precisar da data, criar coleção de unlocks — não dá pra recuperar retroativamente.
- **Streak das conquistas usa `streak.longest`**, não `current` — senão a medalha some no dia em que o usuário perde a sequência.
- **Ranking usa "competition ranking"**: empatados em XP dividem o mesmo rank (1,2,2,4). Isso é obrigatório — o rank de quem está *fora* da página é derivado de `count_with_more_xp`, e um `enumerate()` posicional faria o mesmo usuário ver números diferentes conforme o `limit`. Ver `_competition_ranks` + `test_own_rank_does_not_depend_on_limit`.
- **O bloqueio das lições no caminho é só UI.** `/lesson/:id` continua acessível direto; o conteúdo é público, não há o que proteger no servidor.
- **Dois encodes por vídeo, de propósito.** `build_sign_videos.py` gera `<slug>.webm` (VP9 com alpha vivo) e `<slug>.mp4` (H.264 com o fundo achatado). Nenhum codec dá transparência em todo lugar: Safari não decodifica VP9-alpha, e HEVC-com-alpha exige encoder de macOS. A ordem dos `<source>` no `SignMedia` é carregada — WebM primeiro, ou o Chrome se contenta com o MP4 chapado.
  - **O MP4 tem `--card` (#172f4f) queimado no fundo.** Mudou a cor do card no `index.css`? Rode o script de novo, senão os vídeos ficam com retalho de cor errada no Safari.
  - **ffmpeg não é dependência do repo** — é ferramenta de máquina de quem gera os assets. Os `.mov` originais (~560 MB) ficam fora do git.
- **A fonte dos vídeos tem defeitos, e o script os contorna um a um.** Três dicionários no topo de `build_sign_videos.py`, todos por clipe:
  - `DAMAGED` — 3 clipes com um retângulo de pixels destruídos no tronco (remoção de marca d'água malfeita). **Publicados assim mesmo**, decidido em 2026-07-18: o gesto está legível e a alternativa era a fase de cumprimentos inteira sem vídeo. Irrecuperável por código — o RGB embaixo também é preto. Só reexport do original conserta. É só documental; tirar do `SOURCE_MAP` é o que faz voltar pro SVG.
  - `CROP_HEIGHT` — corta a legenda queimada do "Bom dia". **Legenda queimada em lição é a resposta do quiz impressa na tela**; clipe novo com texto tem que ser cortado ou deixado de fora.
  - `SLOWDOWN` — o "Tudo bem" veio truncado em 4 quadros (0,13s) e piscava em vez de repetir. A 8x lê como pose parada. Não há movimento a recuperar, os 4 quadros são quase idênticos.
- **`SOURCE_MAP` mapeia arquivo → termos, não 1:1.** "Tio - Tia" e "Irmãos" cobrem dois termos cada, apontando pro mesmo arquivo em vez de duplicar bytes.
- **Erro de API: `code` em inglês, `message` em português.** O `code` é contrato de máquina — o SPA e os testes fazem switch nele, então **nunca traduzir**. O `message` é o que aparece na tela, então é português. Vale para todo `detail={"code": ..., "message": ...}`.
  - Os **422 do pydantic** são o caso especial: o texto vem da biblioteca ("Field required", "String should have at least 8 characters"), não do nosso código. `backend/app/core/errors.py` reescreve só o `msg` de cada erro, **mantendo status e formato** (`detail` como lista de `{type, loc, msg}`) — o front faz `Array.isArray(detail) ? detail[0].msg : detail.message`, então traduzir não pode virar mudança de contrato.
  - Cuidado: e-mail inválido e `raise ValueError` nos nossos validadores têm **o mesmo `type: "value_error"`**. Diferencia-se pelo prefixo `"Value error, "` que o pydantic põe no segundo. Campo novo com mensagem própria? Adicione o rótulo em `_FIELD_LABELS`, senão cai no genérico.
  - O texto do `TokenError` (`"invalid_token: Signature has expired"`) **não é mais repassado** ao cliente — era diagnóstico, não frase pra usuário, e vazava detalhe de token. O `code` continua distinguindo os casos.
- **`AuthLayout` é livre de react-router de propósito.** `Login.test.jsx` renderiza `<Login/>` com o `react-router-dom` mockado só com `Link`/`useNavigate`/`useLocation` e **sem Router na árvore**. Importar qualquer outra coisa do router dentro do layout quebra o teste — por isso o `<Link>` do rodapé é passado pela página via prop `footer`.
- **O `Toaster` é `theme="dark"` fixo**, não vem do `next-themes`. Não existe `ThemeProvider` no app, então `useTheme()` caía em `"system"` e seguia o SO: quem usa Windows no claro via toast branco por cima do app navy. O tema aqui não é escolha do usuário. (`next-themes` ficou no `package.json` sem nenhum uso.)
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
| Visual das telas deslogadas | `frontend/src/components/AuthLayout.jsx` (usado por `pages/Login.jsx` e `pages/Register.jsx`) |
| XP / streak / lições concluídas | `backend/app/services/progress_service.py`, `frontend/src/lib/hooks/useLearning.js` |
| Layout / shell / nav | `frontend/src/components/AppShell.jsx`, `Header.jsx`, `BottomNav.jsx`, `lib/nav-items.js` |
| Tema / cores / glow | `frontend/src/index.css` (`:root`), `frontend/tailwind.config.js` |
| Avatar do usuário | `backend/app/models/user.py` (`AVATAR_IDS`), `routers/users.py`, `frontend/src/lib/avatars.js`, `components/UserAvatar.jsx` |
| Ranking | `backend/app/services/ranking_service.py`, `frontend/src/pages/Ranking.jsx` |
| Conquistas | `backend/app/models/achievement.py` (catálogo), `services/achievement_service.py`, `frontend/src/pages/Achievements.jsx` |
| Caminho de fases (estilo Duolingo) | `frontend/src/pages/Lessons.jsx`, `components/LessonNode.jsx`, `components/PhaseBanner.jsx`, `components/PathConnector.jsx`, `components/PathMarker.jsx` |
| Estrelas por lição | `frontend/src/lib/stars.js`, `components/LessonStars.jsx` |
| Hub da Home / marca | `frontend/src/pages/Home.jsx`, `components/HubTile.jsx`, `components/Wordmark.jsx` |
| Nível / gemas a partir do XP | `frontend/src/lib/level.js` |
| Sinais / dicionário | `backend/app/repositories/sign_repo.py`, `frontend/src/pages/Dictionary.jsx`, `frontend/src/lib/hooks/useSearchSigns.js` |
| Vídeo de sinal (transcodificar / exibir) | `backend/scripts/build_sign_videos.py`, `frontend/src/components/SignMedia.jsx`, `backend/app/models/learning.py` (`SignView`) |
| Configuração / env | `backend/app/core/config.py`, `backend/.env.example`, `frontend/src/lib/env.js`, `frontend/.env.example` |
| Rodar / verificar o app end-to-end | `.claude/skills/run-app/SKILL.md` (docker + seed + dirige o SPA no Chromium) + `drive.js` |
