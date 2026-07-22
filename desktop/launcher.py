"""
SINALibras desktop — ponto de entrada do executável.

O app continua sendo o mesmo cliente/servidor de sempre; aqui ele só roda
inteiro na máquina do usuário. Na prática este arquivo faz o que o
docker-compose faz, sem Docker:

  1. sobe um mongod embutido apontando pra uma pasta de dados do usuário;
  2. semeia o catálogo (idempotente, então roda a cada boot sem estragar nada);
  3. sobe o FastAPI servindo API + SPA na MESMA origem (o modo single-host que
     `app.main` já suportava via FRONTEND_BUILD_DIR — nada de novo no backend);
  4. abre uma janela própria (Chromium em modo --app) apontando pra ele.

Chegou a usar uma janela nativa (pywebview/WebView2), removida por crashar
duro — o porquê está em `open_app_window`.

Consequência que vale ter em mente: o banco é local e isolado. Cada pessoa que
instalar tem o próprio ranking, o próprio streak e as próprias conquistas —
ninguém aparece no ranking de ninguém. Isso é inerente ao formato executável,
não um bug.

Portas são escolhidas em tempo de execução (porta 0 = o SO escolhe uma livre),
pra não colidir com um Mongo ou um dev server que a pessoa já tenha rodando.
"""

from __future__ import annotations

import os
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

APP_NAME = "SINALibras"


# --------------------------------------------------------------------------
# Caminhos
# --------------------------------------------------------------------------

def bundle_dir() -> Path:
    """Raiz dos recursos empacotados.

    Congelado pelo PyInstaller, os dados extraídos vivem em sys._MEIPASS. Fora
    dele (rodando do repo) a raiz é a pasta desktop/.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    return Path(meipass) if meipass else Path(__file__).resolve().parent


def data_dir() -> Path:
    """Pasta de dados do usuário — banco, log e segredo do JWT.

    Fica em %LOCALAPPDATA% e não ao lado do .exe: o executável pode estar em
    Program Files, onde um usuário comum não tem permissão de escrita.
    """
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def log_path() -> Path:
    return data_dir() / "sinalibras.log"


_streams_redirected = False


def redirect_streams() -> None:
    """Aponta stdout/stderr pro arquivo de log quando eles não existem.

    Num build windowed (console=False) o PyInstaller deixa sys.stdout e
    sys.stderr como None. Isso não é cosmético: o uvicorn configura logging
    via dictConfig apontando pra `ext://sys.stdout`, e com None a configuração
    explode com "Unable to configure formatter 'default'" — o servidor nem
    chega a subir. Redirecionar cedo conserta isso e ainda faz o log do
    backend aterrissar num arquivo que dá pra ler depois.
    """
    global _streams_redirected
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        stream = log_path().open("a", encoding="utf-8", buffering=1)
    except OSError:
        return
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream
    _streams_redirected = True


def log(message: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {message}"
    # Quando stdout JÁ é o arquivo de log, imprimir e escrever gravaria a
    # mesma linha duas vezes.
    if _streams_redirected:
        try:
            print(line, flush=True)
        except (OSError, ValueError):
            pass
        return
    try:
        if sys.stdout is not None:
            print(line, flush=True)
    except (OSError, ValueError):
        pass
    try:
        with log_path().open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        pass  # log é diagnóstico; nunca deve derrubar o app


# --------------------------------------------------------------------------
# Segredo do JWT
# --------------------------------------------------------------------------

def jwt_secret() -> str:
    """Gera um segredo por instalação e guarda em disco.

    Um segredo fixo no código significaria que qualquer pessoa com o .exe
    poderia forjar o token de qualquer outra instalação. Gerado na primeira
    execução e reusado depois — trocá-lo desloga todo mundo daquela máquina.
    """
    path = data_dir() / "jwt_secret.txt"
    if path.is_file():
        value = path.read_text(encoding="utf-8").strip()
        if len(value) >= 32:
            return value
    value = secrets.token_urlsafe(48)
    path.write_text(value, encoding="utf-8")
    return value


# --------------------------------------------------------------------------
# Mongo
# --------------------------------------------------------------------------

def _no_window() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def kill_orphan_mongod() -> None:
    """Mata um mongod nosso que tenha sobrado de uma execução anterior.

    Se o app morre de um jeito que pula o `finally` (crash do backend gráfico,
    fim de processo pelo gerenciador de tarefas), o mongod continua vivo
    segurando o dbpath. Na abertura seguinte o novo mongod sai com código 100
    (DBPathInUse) e o app **nunca mais abre** — pra quem só clicou no ícone,
    vira "parou de funcionar" pra sempre.

    Guardamos o PID num arquivo e só matamos se o processo daquele PID ainda
    for um mongod: PID é reciclado pelo SO, e matar às cegas poderia derrubar
    um processo alheio.
    """
    pidfile = data_dir() / "mongod.pid"
    if not pidfile.is_file():
        return
    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        pidfile.unlink(missing_ok=True)
        return

    try:
        listing = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True, text=True, creationflags=_no_window(), timeout=15,
        ).stdout.lower()
        if "mongod.exe" in listing:
            log(f"encontrado mongod órfão (pid {pid}); encerrando")
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True, creationflags=_no_window(), timeout=15,
            )
            # Dá um instante pro Windows liberar o lock do dbpath.
            time.sleep(1.5)
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"não deu pra checar o mongod órfão ({exc}); seguindo")
    finally:
        pidfile.unlink(missing_ok=True)


def start_mongod(port: int) -> subprocess.Popen:
    exe = bundle_dir() / "mongodb" / "mongod.exe"
    if not exe.is_file():
        raise RuntimeError(f"mongod não encontrado em {exe}")

    db_path = data_dir() / "db"
    db_path.mkdir(parents=True, exist_ok=True)

    args = [
        str(exe),
        "--dbpath", str(db_path),
        "--port", str(port),
        # Só loopback: o banco não deve ficar exposto na rede da pessoa.
        "--bind_ip", "127.0.0.1",
        # O padrão (snappy) é ótimo pra servidor e irrelevante aqui; o que
        # importa é o tamanho em disco na máquina de alguém.
        "--wiredTigerCacheSizeGB", "0.25",
        "--quiet",
    ]

    # CREATE_NO_WINDOW: sem isso um console preto do mongod pisca junto com o
    # app, o que parece defeito pra quem só clicou no ícone.
    log(f"iniciando mongod na porta {port}")
    process = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_no_window(),
    )
    # Registra o PID pra que a próxima abertura saiba matá-lo se este processo
    # morrer sem passar pelo `finally` (ver kill_orphan_mongod).
    try:
        (data_dir() / "mongod.pid").write_text(str(process.pid), encoding="utf-8")
    except OSError:
        pass
    return process


def wait_for_mongo(port: int, process: subprocess.Popen, timeout: float = 60.0) -> None:
    """Espera a porta aceitar conexão, desistindo se o mongod morrer antes."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"mongod encerrou sozinho (código {process.returncode}). "
                f"Veja o log em {data_dir()}."
            )
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                log("mongod pronto")
                return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError("mongod não respondeu a tempo")


# --------------------------------------------------------------------------
# Backend
# --------------------------------------------------------------------------

def configure_env(*, mongo_port: int) -> None:
    """Preenche as variáveis que `app.core.config.Settings` exige.

    Tem que rodar ANTES de qualquer import de app.*: get_settings() é
    lru_cache, então a primeira leitura é a que vale pro processo inteiro.
    """
    bundle = bundle_dir()
    os.environ.update({
        "MONGO_URL": f"mongodb://127.0.0.1:{mongo_port}",
        "DB_NAME": "sinalibras",
        "JWT_SECRET": jwt_secret(),
        "ENVIRONMENT": "production",
        "LOG_LEVEL": "INFO",
        # Mesma origem: o FastAPI serve o SPA, então não há cross-origin e a
        # lista de CORS fica vazia de propósito.
        "CORS_ORIGINS": "",
        # http://127.0.0.1 não é um contexto seguro pra cookie Secure; marcar
        # Secure aqui faria o navegador descartar o cookie de login.
        "COOKIE_SECURE": "false",
        "COOKIE_SAMESITE": "lax",
        "FRONTEND_BUILD_DIR": str(bundle / "frontend_build"),
        "SIGNS_DIR": str(bundle / "signs"),
        # Os limites padrão (3 cadastros/minuto, 5 logins/minuto) existem pra
        # conter força bruta num servidor público. Aqui não há servidor
        # público: o banco é local, de uma pessoa só, na máquina dela — não há
        # de quem proteger. O que sobrava era só o dano: errar a senha três
        # vezes (ela precisa ter 8+ caracteres) travava a quarta tentativa,
        # a correta, por um minuto inteiro.
        # Mantemos um limite mínimo em vez de desligar: ele ainda segura um
        # loop acidental, e a janela de 3s é curta demais pra alguém notar.
        "RATE_LIMIT_REGISTER": "5/3seconds",
        "RATE_LIMIT_LOGIN": "5/3seconds",
        "RATE_LIMIT_REFRESH": "20/3seconds",
    })


def seed_catalog() -> None:
    """Popula fases/lições/sinais. Idempotente, então roda a cada boot.

    Sem isso o app abre vazio: o catálogo não vive no código, vive no banco —
    e o banco nasce vazio na máquina de quem instalou.

    O `close_mongo_connection()` no fim NÃO é higiene opcional. `app.db.mongo`
    guarda o client num global e `connect_to_mongo` devolve o existente sem
    reconectar. Como `asyncio.run` fecha o loop que criou, o client ficaria
    amarrado a um loop morto — e o lifespan do uvicorn, rodando no loop dele,
    quebrava em `ensure_indexes` com "Event loop is closed" e o servidor nem
    subia. Fechando aqui, o lifespan reconecta no loop certo.
    """
    import asyncio

    from app.db.mongo import close_mongo_connection
    from scripts.seed import run as seed_run

    async def _seed_then_release() -> None:
        await seed_run(reset=False)
        await close_mongo_connection()

    log("semeando catálogo")
    asyncio.run(_seed_then_release())
    log("catálogo pronto")


def start_api(port: int) -> None:
    import uvicorn

    from app.main import app

    # log_config=None: o uvicorn não deve rodar o dictConfig dele. A app já
    # configura logging por conta própria (app.core.logging.setup_logging, no
    # lifespan), e a config padrão do uvicorn referencia streams que num build
    # windowed podem não existir.
    config = uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="warning", log_config=None
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True, name="uvicorn")
    thread.start()


def wait_for_api(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                log("api pronta")
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("a API não subiu a tempo")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    mongo = None
    redirect_streams()
    try:
        kill_orphan_mongod()
        mongo_port = free_port()
        mongo = start_mongod(mongo_port)
        wait_for_mongo(mongo_port, mongo)

        configure_env(mongo_port=mongo_port)
        seed_catalog()

        api_port = free_port()
        start_api(api_port)
        wait_for_api(api_port)

        open_app_window(f"http://127.0.0.1:{api_port}")
        return 0

    except Exception as exc:  # noqa: BLE001 — última linha de defesa da GUI
        log(f"ERRO: {exc}")
        _show_error(str(exc))
        return 1

    finally:
        if mongo and mongo.poll() is None:
            log("encerrando mongod")
            mongo.terminate()
            try:
                mongo.wait(timeout=15)
            except subprocess.TimeoutExpired:
                # Um mongod pendurado tranca o dbpath e impede o próximo boot.
                mongo.kill()
        try:
            (data_dir() / "mongod.pid").unlink(missing_ok=True)
        except OSError:
            pass


# Abaixo disso, uma janela que "fechou" quase certamente não foi fechada pelo
# usuário — o Chromium entregou a URL a outro processo e saiu (ver
# open_app_window). Nesse caso NÃO derrubamos o backend.
MIN_WINDOW_SECONDS = 5.0


# Navegadores baseados em Chromium, em ordem de preferência. Edge vem primeiro
# por estar sempre presente no Windows 10/11.
_BROWSERS = [
    r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
]


def _find_chromium() -> Optional[Path]:
    for raw in _BROWSERS:
        candidate = Path(os.path.expandvars(raw))
        if candidate.is_file():
            return candidate
    return None


def _cleanup_old_profiles(keep: Path) -> None:
    """Apaga os perfis de janela de execuções anteriores.

    Como usamos um `--user-data-dir` novo a cada abertura (ver
    open_app_window), os antigos só ocupam espaço. Best-effort: um perfil ainda
    travado por um Chromium vivo não deleta, e tudo bem — cai fora no próximo
    boot. O glob `janela*` também limpa o `janela` único das versões antigas.
    """
    try:
        entries = list(keep.parent.glob("janela*"))
    except OSError:
        return
    for entry in entries:
        if entry == keep or not entry.is_dir():
            continue
        shutil.rmtree(entry, ignore_errors=True)


def open_app_window(url: str) -> None:
    """Abre o app numa janela própria e espera ela fechar.

    ## Por que um perfil NOVO a cada abertura

    O modo `--app` do Chromium abre uma janela SEM barra de endereço, sem abas,
    com entrada própria na barra de tarefas e ícone do site. Visualmente é um
    aplicativo, e não custa nada em tamanho: o motor já está na máquina. O
    truque só se sustenta se ESTE processo do navegador ficar vivo enquanto a
    janela existe — é o `window.wait()` lá embaixo que segura o launcher no ar;
    quando ele volta, o `main()` cai no `finally` e derruba o mongod.

    O perigo é o Chromium ENTREGAR a URL a um processo já existente e sair na
    hora. Ele faz isso quando acha outro processo usando o mesmo
    `--user-data-dir` (o "singleton" do perfil). O Edge agrava: com o startup
    boost ligado ele mantém um processo em segundo plano mesmo sem janelas. Aí
    o `msedge.exe` que abrimos entrega a URL e encerra em <1s, o `wait()` volta
    na hora e o launcher mata o backend com a janela ainda na tela — o usuário
    digita o login e cai num backend morto ("falha ao entrar" depois de ~1min
    de retry). Aconteceu de verdade (ver sinalibras.log: janela "fechada" no
    mesmo segundo em que abriu).

    A defesa é um `--user-data-dir` ÚNICO por abertura: sem processo pré-
    existente para aquele perfil, o Chromium é obrigado a criar um processo
    novo, que vive enquanto a janela viver. Não se perde nada: a porta muda a
    cada boot, então o cookie de login (preso à origem 127.0.0.1:porta) já não
    sobrevivia entre sessões — o perfil sempre foi descartável.

    Tentei antes uma janela nativa com pywebview/WebView2. Ela **crasha duro**
    (0xC0000409 dentro de `webview.start()`, no 3.13 e no 3.14), e crash
    nativo não vira exceção Python — o processo sumia sem log, deixando o
    mongod órfão. Como não consigo verificar que funciona, não vai junto.
    """
    exe = _find_chromium()
    # Perfil único por PID: garante um processo novo (sem entrega ao velho).
    profile = data_dir() / f"janela-{os.getpid()}"
    profile.mkdir(parents=True, exist_ok=True)
    _cleanup_old_profiles(keep=profile)

    if exe is None:
        # Nenhum Chromium: cai pro navegador padrão. Vira uma aba comum, mas
        # é melhor do que não abrir nada.
        import webbrowser

        log("nenhum Chromium encontrado; abrindo no navegador padrão")
        webbrowser.open(url)
        log("mantendo o app no ar (feche pelo gerenciador de tarefas)")
        while True:
            time.sleep(3600)

    log(f"abrindo janela do app com {exe.name}")
    started = time.monotonic()
    window = subprocess.Popen(
        [
            str(exe),
            f"--app={url}",
            f"--user-data-dir={profile}",
            "--window-size=1280,900",
            "--no-first-run",
            "--no-default-browser-check",
            # Sem isso o Edge pode abrir a aba de boas-vindas por cima do app.
            "--disable-features=msEdgeWelcomePage,Translate",
        ],
        creationflags=_no_window(),
    )
    # Bloqueia até a pessoa fechar a janela; aí o main() cai no `finally` e
    # derruba o mongod junto.
    window.wait()

    # Rede de segurança: se o navegador saiu cedo demais, ele quase certamente
    # ENTREGOU a janela a outro processo (ver docstring) em vez de ter sido
    # fechado pelo usuário. Derrubar o backend agora mataria uma janela viva —
    # e não dá pra reatar naquele processo alheio. Então seguramos o app no ar
    # em vez de matá-lo. O perfil único torna isso raríssimo, mas o estrago de
    # errar é justamente o bug que estamos consertando.
    if time.monotonic() - started < MIN_WINDOW_SECONDS:
        log(
            "janela encerrou em <5s (provável entrega a outro Chromium); "
            "mantendo o app no ar para não matar uma janela viva"
        )
        while True:
            time.sleep(3600)

    log("janela fechada")


def _show_error(message: str) -> None:
    """Sem console no modo janela, uma falha silenciosa parece 'não abre'."""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            None,
            f"{message}\n\nDetalhes em:\n{data_dir() / 'sinalibras.log'}",
            f"{APP_NAME} — erro ao iniciar",
            0x10,  # MB_ICONERROR
        )
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    sys.exit(main())
