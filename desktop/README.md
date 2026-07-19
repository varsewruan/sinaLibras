# SINALibras desktop (Windows)

Empacota o app inteiro — SPA, API e banco — num executável que a pessoa baixa,
descompacta e clica. Sem Docker, sem terminal, sem servidor.

## O que o usuário final recebe

Um `SINALibras-setup.exe` — instala, cria atalho no menu iniciar e (opcional) na
área de trabalho. Ao abrir:

- sobe um `mongod` embutido gravando em `%LOCALAPPDATA%\SINALibras\db`;
- semeia o catálogo (fases, lições, sinais) na primeira execução;
- sobe o FastAPI servindo API + SPA na mesma origem, em portas livres;
- abre uma janela própria — Chromium em modo `--app` (Edge/Chrome, já presente
  na máquina), sem barra de endereço nem abas.

Chegou a usar uma janela nativa via WebView2/pywebview; foi abandonada por
crashar duro (0xC0000409). O porquê está em `launcher.open_app_window`.

**O banco é local e isolado.** Cada instalação tem o próprio ranking, streak e
conquistas — duas pessoas com o executável não se veem no ranking. Isso é
inerente ao formato; para ranking compartilhado o caminho é o deploy no Fly.io
(`fly.toml` na raiz do repo).

Desinstalar pelo Painel de Controle **não apaga o progresso** — o banco fica em
`%LOCALAPPDATA%\SINALibras` de propósito, pra que reinstalar não zere quem já
jogou. Apagar de vez = apagar essa pasta à mão.

## Como gerar o executável

Precisa de **Windows**, Python 3.11+ e Node. Rode tudo da raiz do repo.

### 1. Buildar o SPA para mesma origem

`REACT_APP_BACKEND_URL` vazio é o que faz o SPA falar com a própria origem em
vez de `localhost:8000` (ver `frontend/src/lib/env.js`). Buildar com o valor
de dev gera um app que não acha a API dentro do executável.

Pelo container (mais rápido, já tem as deps):

```powershell
docker compose exec -T -e REACT_APP_BACKEND_URL= frontend yarn build
```

Ou nativo, se tiver yarn: `cd frontend; $env:REACT_APP_BACKEND_URL=""; yarn build`

### 2. Baixar o mongod

Só o `mongod.exe` do zip do MongoDB Community 7 (a mesma major do
`mongo:7` usado no compose). Os `.pdb` do zip são símbolos de debug, ~1,5 GB —
não vão para o pacote.

```powershell
$zip = "$env:TEMP\mongodb.zip"
Invoke-WebRequest -UseBasicParsing `
  "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-7.0.14.zip" -OutFile $zip
Expand-Archive $zip "$env:TEMP\mongo" -Force
$env:SINA_MONGOD = "$env:TEMP\mongo\mongodb-win32-x86_64-windows-7.0.14\bin\mongod.exe"
```

### 3. Ambiente Python e build

```powershell
python -m venv .venv-desktop
.\.venv-desktop\Scripts\pip install -r backend\requirements.txt pyinstaller
cd desktop
..\.venv-desktop\Scripts\pyinstaller --noconfirm SINALibras.spec
```

Saída em `desktop\dist\SINALibras\` — a pasta onedir, já funcional.

### 4. Gerar o instalador

Transforma a pasta acima no único arquivo que se manda pra alguém. Precisa do
[Inno Setup 6](https://jrsoftware.org/isdl.php)
(`winget install JRSoftware.InnoSetup`), ainda de dentro de `desktop/`:

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer.iss
```

Saída: `desktop\dist\installer\SINALibras-setup.exe`.

Se preferir mandar a pasta crua, zipar `dist\SINALibras\` também funciona — o
instalador só evita que a pessoa tenha que cavar atrás do `.exe` certo.

## Decisões que valem saber

- **Onedir, não onefile.** Onefile descompacta ~200 MB em `%TEMP%` a cada
  abertura: uns 10s de espera e o mongod acabaria preso numa pasta temporária.
- **Portas escolhidas em runtime** (`porta 0`), pra não colidir com um Mongo ou
  dev server que a pessoa já tenha rodando.
- **Segredo do JWT gerado por instalação** e guardado em
  `%LOCALAPPDATA%\SINALibras\jwt_secret.txt`. Um segredo fixo no código deixaria
  qualquer um com o .exe forjar token de qualquer instalação.
- **`COOKIE_SECURE=false`** porque `http://127.0.0.1` não é contexto seguro;
  com Secure ligado o navegador descarta o cookie e o login nunca "pega".
- **O seed roda a cada boot** — é idempotente, e assim um banco apagado se
  recompõe sozinho.
- **`console=False`**: erros de boot viram MessageBox + log em
  `%LOCALAPPDATA%\SINALibras\sinalibras.log`, senão a falha fica invisível.

## Limitações conhecidas

- **Só Windows x64.** O `mongod.exe` e o build do PyInstaller são específicos
  de plataforma; macOS/Linux exigiriam repetir o processo em cada SO.
- **~36 MB o instalador, ~102 MB instalado** — a maior parte é `mongod.exe`
  (61 MB) e o runtime Python.
- **Sem atualização automática.** Versão nova = mandar o instalador de novo (ele
  sobrescreve a instalação anterior e preserva o progresso).
- **Não assinado.** O SmartScreen do Windows vai avisar na primeira execução
  ("Mais informações" → "Executar assim mesmo"). Assinar exige certificado pago.
- **O Inno Setup instalado via winget é a edição gratuita**, que se anuncia como
  "Non-commercial use only" na compilação. Para distribuição comercial, checar o
  licenciamento em jrsoftware.org.
- **MongoDB é SSPL.** Redistribuir o `mongod.exe` junto pede que a licença
  acompanhe o pacote; para uso pessoal/entre amigos é o caso comum, mas não é
  uma licença permissiva como MIT.
