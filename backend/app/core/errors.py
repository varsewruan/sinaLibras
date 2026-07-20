"""
Portuguese rendering of the two errors our own code never gets to phrase:
pydantic's 422s and slowapi's 429.

Everything else in the API raises its own `{code, message}` detail, already
written in Portuguese. These two are generated inside libraries, so without
a handler the user is shown English ("Field required", "Rate limit
exceeded: 3 per 1 minute").

This handler rewrites only the `msg` of each error. The response shape is
deliberately unchanged — status 422 with `detail` as a list of
`{type, loc, msg}` — because the SPA branches on exactly that shape
(`Array.isArray(detail) ? detail[0].msg : detail.message` in Register.jsx)
and the backend tests assert the status. Translating is a presentation
change; it must not become a contract change.

Note that pydantic gives BOTH e-mail failures and our own `raise ValueError`
validators `type == "value_error"`. They're told apart by the "Value error, "
prefix pydantic puts on the latter — see `_value_error_message`.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

# Field names as they appear mid-sentence, with the definite article so the
# generated messages read naturally ("Informe a senha." / "A senha deve...").
_FIELD_LABELS: dict[str, str] = {
    "email": "o e-mail",
    "name": "o nome",
    "password": "a senha",
    "avatar": "o avatar",
    "score": "a pontuação",
    "lesson_id": "a lição",
}

_PYDANTIC_VALUE_ERROR_PREFIX = "Value error, "


def _field_label(loc: tuple[Any, ...]) -> str | None:
    """Last string element of `loc` is the field name; `loc` starts with 'body'."""
    for part in reversed(loc):
        if isinstance(part, str) and part != "body":
            return _FIELD_LABELS.get(part)
    return None


def _plural_chars(n: int) -> str:
    return "1 caractere" if n == 1 else f"{n} caracteres"


def _value_error_message(msg: str) -> str:
    """
    `value_error` covers two very different things.

    Our own validators raise ValueError with an already-Portuguese sentence,
    which pydantic re-emits prefixed with "Value error, " — strip it and the
    message is ready. Anything else is the library's own (in practice the
    e-mail validator), which we replace wholesale.
    """
    if msg.startswith(_PYDANTIC_VALUE_ERROR_PREFIX):
        return msg[len(_PYDANTIC_VALUE_ERROR_PREFIX):]
    if msg.startswith("value is not a valid email address"):
        return "E-mail inválido."
    return "Valor inválido."


def translate_validation_error(error: dict[str, Any]) -> str:
    """One pydantic error dict → one Portuguese sentence."""
    err_type = error.get("type", "")
    ctx = error.get("ctx") or {}
    label = _field_label(tuple(error.get("loc", ())))

    if err_type == "missing":
        return f"Informe {label}." if label else "Campo obrigatório."

    if err_type == "string_too_short":
        n = ctx.get("min_length")
        if label and n is not None:
            return f"{label.capitalize()} deve ter pelo menos {_plural_chars(n)}."
        return "Valor curto demais."

    if err_type == "string_too_long":
        n = ctx.get("max_length")
        if label and n is not None:
            return f"{label.capitalize()} deve ter no máximo {_plural_chars(n)}."
        return "Valor longo demais."

    if err_type in {"greater_than_equal", "less_than_equal"}:
        limit = ctx.get("ge", ctx.get("le"))
        rel = "no mínimo" if err_type == "greater_than_equal" else "no máximo"
        if label and limit is not None:
            return f"{label.capitalize()} deve ser {rel} {limit}."
        return "Valor fora do intervalo permitido."

    if err_type == "value_error":
        return _value_error_message(error.get("msg", ""))

    # Unknown type: a generic Portuguese sentence still beats leaking the
    # library's English at the user.
    return f"{label.capitalize()} é inválido." if label else "Valor inválido."


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """
    429s in the same `{code, message}` shape as every other error we raise.

    slowapi's built-in handler answers `{"error": "Rate limit exceeded: 3 per
    1 minute"}` — no `detail` key, and in English. The SPA reads
    `data.detail.message` (Login/Register.jsx), finds nothing, and falls back
    to a generic "Falha ao criar conta.", so the one thing the user needed to
    know — that it's temporary and waiting fixes it — was the one thing that
    never reached the screen.

    The wait isn't named in the message on purpose: the window is configurable
    per environment (seconds in the desktop build, a minute on the web), so a
    hardcoded "um minuto" would be a lie in half the deploys.
    """
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": {
                "code": "rate_limited",
                "message": "Muitas tentativas seguidas. Espere um pouco e tente de novo.",
            }
        },
    )
    # Keeps slowapi's X-RateLimit-*/Retry-After headers, which the default
    # handler adds and clients may rely on.
    return request.app.state.limiter._inject_headers(
        response, request.state.view_rate_limit
    )


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    translated = [
        {**error, "msg": translate_validation_error(error)} for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        # jsonable_encoder because pydantic puts non-serialisable objects in
        # `ctx` (the original exception instance, for value_error).
        content={"detail": jsonable_encoder(translated)},
    )
