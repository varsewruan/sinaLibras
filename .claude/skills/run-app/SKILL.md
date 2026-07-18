---
name: run-app
description: Sobe o stack do SINALibras (docker compose + seed) e dirige o SPA num Chromium headless para confirmar que uma mudança funciona de verdade. Use quando pedirem para rodar, subir, iniciar o app, verificar na interface, tirar screenshot das páginas, ou validar uma branch de ponta a ponta.
---

# Rodar o SINALibras

Verificado em 2026-07-10 (Windows 11, PowerShell, Docker Desktop).

Sequência inteira, do zero até screenshots das páginas. Não pule o seed:
sem ele o catálogo vem vazio e o Ranking não tem o que mostrar.

## 1. Subir

```powershell
docker compose build
docker compose up -d
docker compose ps --format "table {{.Service}}\t{{.Status}}"
```

Espere `backend` e `mongo` ficarem `(healthy)`. O `frontend` não tem
healthcheck — confirme pelo log:

```powershell
docker compose logs frontend --tail 5   # espere "webpack compiled successfully"
```

**Primeiro boot do frontend é lento** (roda `yarn install` dentro do
container). Nos seguintes é instantâneo, graças ao volume nomeado
`frontend-node-modules`.

## 2. Seed

```powershell
docker compose exec -T backend python -m scripts.seed --demo-users
```

Esperado: `lessons=9 phases=3 signs=36 users=18`.

- **`-T` é obrigatório.** Sem ele, `docker compose exec` tenta alocar TTY e
  trava quando chamado de fora de um terminal interativo.
- `--demo-users` é opt-in e **nunca roda em produção**. Cria ~10 jogadores
  fake com senha aleatória, idempotentes por e-mail (`*@demo.sinalibras.dev`).

## 3. Smoke da API

Backend em `http://localhost:8000/api`. Duas armadilhas do ambiente Windows:

- **`curl.exe` no PowerShell come as aspas duplas** de `-d '{"a":"b"}'`. O
  backend responde `json_invalid` e parece bug dele. Passe o corpo por
  arquivo: `--data "@payload.json"`.
- **O validador de e-mail rejeita TLDs reservados** (`.test`, `.invalid`,
  `.localhost`, `.example`) com 422. Use um domínio real, ex. `@sinalibras.dev`.

```powershell
$sp = "<scratchpad>"
'{"name":"Smoke","email":"smoke-run@sinalibras.dev","password":"senha-forte-123456"}' |
  Set-Content -Encoding utf8 "$sp\register.json"

curl.exe -s -c "$sp\cookies.txt" -H "Content-Type: application/json" `
  --data "@$sp\register.json" http://localhost:8000/api/auth/register
curl.exe -s -b "$sp\cookies.txt" http://localhost:8000/api/achievements/me
curl.exe -s -b "$sp\cookies.txt" "http://localhost:8000/api/ranking?limit=3"
```

`/api/ranking` é público; `/api/achievements/me` e `/api/progress/me/summary`
exigem o cookie. Note o `/me` — `GET /api/achievements` sem sufixo é 404.

## 4. Dirigir a interface

O webpack compilar só prova que o bundle fecha. Um erro de runtime no React
ainda dá tela branca, então **abra o navegador de verdade**.

Playwright não é dependência do repo. Instale fora dele:

```powershell
$sp = "<scratchpad>"
Set-Location $sp
npm init -y; npm install playwright
npx --yes playwright install chromium
```

Rode o driver que acompanha esta skill (faz login pela UI, varre as rotas,
tira screenshot de cada uma, reporta erros de console e confere que os
pontos de entrada da Home navegam):

```powershell
$env:NODE_PATH = "$sp\node_modules"   # o script mora no repo, os módulos no scratchpad
node .claude\skills\run-app\drive.js
```

Screenshots saem no diretório atual como `shot-<rota>.png`. **Olhe as
imagens** — um frame em branco é falha de renderização, e o texto sozinho
não denuncia layout quebrado.

### Seletores: use os `data-testid`, não o texto

Os títulos dos cards são maiúsculos por CSS (`text-transform`). `innerText`
devolve `"RANKING"`, mas o DOM tem `"Ranking"` — `getByText("RANKING")`
nunca casa. E `a[href="/profile"]` resolve primeiro no BottomNav, que fica
**oculto no desktop**, então `.first().click()` estoura timeout.

| testid | onde | leva a |
|---|---|---|
| `login-email` / `login-password` / `login-submit` / `login-error` | `pages/Login.jsx` | — |
| `hub-aprender` | tile da Home | `/learn` |
| `hub-fases` | tile da Home | `/lessons` |
| `hub-objetivos` | tile da Home | `/achievements` |
| `hub-ranking` | tile da Home | `/ranking` |
| `hub-loja` / `hub-videoaulas` | tiles "Em breve" da Home | nada (só toast) |
| `cta-comecar` | botão da página Aprender | `/lesson/:id` (próxima lição, id dinâmico) |
| `header-profile` | avatar do topo | `/profile` |

Todas as rotas exceto `/login` e `/register` são `<Protected>` — logue antes.

No **desktop a sidebar só tem Início + Aprender**, de propósito
(`lib/nav-items.js`). Ranking / Conquistas / Perfil só são alcançáveis pelos
tiles da Home e pelo avatar, o que torna esses cliques o único caminho vivo —
vale testá-los sempre.

A Home é um **grid de 6 tiles, sem botão JOGAR** (mockup de 2026-07-18). O CTA
que retoma a próxima lição é o `cta-comecar`, na página Aprender.

## 5. Testes

```powershell
docker compose exec -T backend python -m pytest -v
```

52 testes, ~13s, todos verdes em 2026-07-10. O `PendingDeprecationWarning`
do Starlette (`import python_multipart`) vem da lib, não do código do projeto.

## Limpeza

```powershell
docker compose down -v   # derruba e apaga o volume do mongo (leva o usuário de smoke junto)
```

Sem o `-v` o `smoke-run@sinalibras.dev` continua no banco. Ele é inofensivo,
mas aparece no ranking com 0 XP e desempata na última posição.

## Coisas que parecem bug e não são

- `avatar: "dummy"` num usuário novo é o default documentado. `AVATAR_IDS`
  (`app/models/user.py`) e `AVATARS` (`frontend/src/lib/avatars.js`) têm os
  mesmos 18 ids (10 animais + `dummy` + 7 presets antigos).
- Nó do caminho sem fileira de estrelas não é bug: só lição **concluída**
  desenha estrelas. A nota vem de `LessonSummary.score` (melhor nota já
  tirada) — ver `frontend/src/lib/stars.js`.
- Empatados em XP dividem o mesmo rank (1, 2, 2, 4). É "competition ranking",
  exigido por `test_own_rank_does_not_depend_on_limit`. Cinco usuários com
  0 XP aparecendo todos como rank 15 está **certo**.
