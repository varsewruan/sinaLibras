"""
SINALibras desktop — ponto de entrada do executável.

O app continua sendo o mesmo cliente/servidor de sempre; aqui ele só roda
inteiro na máquina do usuário. Na prática este arquivo faz o que o
docker-compose faz, sem Docker:

  1. sobe um mongod embutido apontando pra uma pasta de dados do usuário;
  2. semeia o catálogo (idempotente, então roda a cada boot sem estragar nada);
  3. sobe o FastAPI servindo API + SPA na MESMA origem (o modo single-host que
     `app.main` já suportava via FRONTEND_BUILD_DIR — nada de novo no backend);
  4. abre uma janela nativa (WebView2) apontando pra esse servidor local.

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
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

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


def redirect_streams() -> None:
    """Aponta stdout/stderr pro arquivo de log quando eles não existem.

    Num build windowed (console=False) o PyInstaller deixa sys.stdout e
    sys.stderr como None. Isso não é cosmético: o uvicorn configura logging
    via dictConfig apontando pra `ext://sys.stdout`, e com None a configuração
    explode com "Unable to configure formatter 'default'" — o servidor nem
    chega a subir. Redirecionar cedo conserta isso e ainda faz o log do
    backend aterrissar num arquivo que dá pra ler depois.
    """
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


def log(message: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {message}"
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
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    log(f"iniciando mongod na porta {port}")
    return subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


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
    })


def seed_catalog() -> None:
    """Popula fases/lições/sinais. Idempotente, então roda a cada boot.

    Sem isso o app abre vazio: o catálogo não vive no código, vive no banco —
    e o banco nasce vazio na máquina de quem instalou.
    """
    import asyncio

    from scripts.seed import run as seed_run

    log("semeando catálogo")
    asyncio.run(seed_run(reset=False))
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
        mongo_port = free_port()
        mongo = start_mongod(mongo_port)
        wait_for_mongo(mongo_port, mongo)

        configure_env(mongo_port=mongo_port)
        seed_catalog()

        api_port = free_port()
        start_api(api_port)
        wait_for_api(api_port)

        import webview

        log(f"abrindo janela em http://127.0.0.1:{api_port}")
        webview.create_window(
            APP_NAME,
            f"http://127.0.0.1:{api_port}",
            width=1280,
            height=860,
            min_size=(900, 640),
        )
        # Bloqueia até a janela fechar. Precisa ser a thread principal.
        webview.start()
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
