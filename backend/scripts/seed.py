"""
Seed the catalog with placeholder content (3 phases, 9 lessons, ~36 signs).

Run:
    docker compose run --rm backend python -m scripts.seed
    docker compose run --rm backend python -m scripts.seed --reset

Idempotent: by default it skips entities that already exist (matched by
natural keys: phase.order, lesson.(phase_id, order), sign.portuguese_term).
With --reset, it drops the three collections first.

The image URLs are placeholders from placehold.co — replace with real
Libras videos when the content team plugs in the curriculum.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import urllib.parse
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.mongo import connect_to_mongo, ensure_indexes
from app.models.lesson import Lesson
from app.models.phase import Phase
from app.models.sign import Sign

logger = get_logger(__name__)


def _load_manifest() -> dict[str, str]:
    """Map term → image URL from the asset builder's manifest.

    Empty dict if the bundle hasn't been generated yet — seed then falls
    back to the legacy placehold.co URLs.
    """
    settings = get_settings()
    manifest_path = Path(settings.SIGNS_DIR) / "manifest.json"
    if not manifest_path.is_file():
        logger.warning("seed_manifest_missing", path=str(manifest_path))
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


# ----------------------------- Content definition ---------------------------

CATALOG = [
    {
        "order": 1,
        "title": "Cumprimentos",
        "description": "Os primeiros sinais — diga olá, tchau, bom dia.",
        "lessons": [
            {"order": 1, "title": "Olá e Tchau", "xp_reward": 20,
             "signs": ["Olá", "Tchau", "Tudo bem?", "Obrigado"]},
            {"order": 2, "title": "Bom dia/tarde/noite", "xp_reward": 25,
             "signs": ["Bom dia", "Boa tarde", "Boa noite", "Até logo"]},
            {"order": 3, "title": "Cumprimentos formais", "xp_reward": 30,
             "signs": ["Prazer", "Como vai?", "Me chamo", "Você"]},
        ],
    },
    {
        "order": 2,
        "title": "Família",
        "description": "Apresente quem é importante pra você.",
        "lessons": [
            {"order": 1, "title": "Pais e filhos", "xp_reward": 25,
             "signs": ["Pai", "Mãe", "Filho", "Filha"]},
            {"order": 2, "title": "Irmãos", "xp_reward": 25,
             "signs": ["Irmão", "Irmã", "Bebê", "Família"]},
            {"order": 3, "title": "Avós e tios", "xp_reward": 30,
             "signs": ["Avô", "Avó", "Tio", "Tia"]},
        ],
    },
    {
        "order": 3,
        "title": "Cores",
        "description": "As primeiras cores do vocabulário.",
        "lessons": [
            {"order": 1, "title": "Cores primárias", "xp_reward": 20,
             "signs": ["Vermelho", "Azul", "Amarelo", "Verde"]},
            {"order": 2, "title": "Branco, preto e cinza", "xp_reward": 20,
             "signs": ["Branco", "Preto", "Cinza", "Marrom"]},
            {"order": 3, "title": "Tons vibrantes", "xp_reward": 25,
             "signs": ["Rosa", "Roxo", "Laranja", "Dourado"]},
        ],
    },
]


def _placeholder_url(term: str) -> str:
    """Legacy fallback when no manifest entry exists for a term."""
    safe = urllib.parse.quote(term)
    return f"https://placehold.co/600x400/1E293B/F59E0B?text=Sinal%3A+{safe}"


# ----------------------------- Seeding logic --------------------------------

async def _seed_sign(db: AsyncIOMotorDatabase, term: str, *, manifest: dict[str, str]) -> str:
    """Upsert the sign and keep its thumbnail in sync with the manifest."""
    thumbnail_url = manifest.get(term) or _placeholder_url(term)

    existing = await db.signs.find_one({"portuguese_term": term})
    if existing:
        # Catch the seed → asset-rebuild → re-seed cycle: update the
        # thumbnail in place when the manifest URL drifts.
        if existing.get("thumbnail_url") != thumbnail_url:
            await db.signs.update_one(
                {"_id": existing["_id"]},
                {"$set": {"thumbnail_url": thumbnail_url}},
            )
            logger.info("seed_sign_thumbnail_updated", term=term, id=existing["_id"])
        return existing["_id"]

    sign = Sign(
        portuguese_term=term,
        libras_description=f"Demonstração do sinal '{term}' em Libras.",
        text_description=f"Sinal de '{term}' — substitua pelo vídeo real quando o conteúdo chegar.",
        thumbnail_url=thumbnail_url,
        video_url=None,
    )
    await db.signs.insert_one(sign.to_mongo())
    logger.info("seed_sign_inserted", term=term, id=sign.id)
    return sign.id


async def _seed_lesson(
    db: AsyncIOMotorDatabase,
    *,
    phase_id: str,
    order: int,
    title: str,
    xp_reward: int,
    sign_ids: list[str],
) -> str:
    existing = await db.lessons.find_one({"phase_id": phase_id, "order": order})
    if existing:
        return existing["_id"]
    lesson = Lesson(
        phase_id=phase_id,
        title=title,
        description=f"{title} — pratique até dominar.",
        order=order,
        xp_reward=xp_reward,
        sign_ids=sign_ids,
    )
    await db.lessons.insert_one(lesson.to_mongo())
    logger.info("seed_lesson_inserted", title=title, phase_id=phase_id, order=order)
    return lesson.id


async def _seed_phase(db: AsyncIOMotorDatabase, *, order: int, title: str, description: str) -> str:
    existing = await db.phases.find_one({"order": order})
    if existing:
        return existing["_id"]
    phase = Phase(title=title, description=description, order=order)
    await db.phases.insert_one(phase.to_mongo())
    logger.info("seed_phase_inserted", title=title, order=order)
    return phase.id


async def run(*, reset: bool) -> None:
    settings = get_settings()
    setup_logging(settings)
    db = await connect_to_mongo(settings)
    await ensure_indexes(db)

    manifest = _load_manifest()
    if manifest:
        logger.info("seed_manifest_loaded", terms=len(manifest))

    if reset:
        logger.warning("seed_reset", note="dropping phases / lessons / signs collections")
        await db.phases.drop()
        await db.lessons.drop()
        await db.signs.drop()
        await ensure_indexes(db)  # re-create after drop

    for phase_def in CATALOG:
        phase_id = await _seed_phase(
            db,
            order=phase_def["order"],
            title=phase_def["title"],
            description=phase_def["description"],
        )
        for lesson_def in phase_def["lessons"]:
            sign_ids = [
                await _seed_sign(db, term, manifest=manifest)
                for term in lesson_def["signs"]
            ]
            await _seed_lesson(
                db,
                phase_id=phase_id,
                order=lesson_def["order"],
                title=lesson_def["title"],
                xp_reward=lesson_def["xp_reward"],
                sign_ids=sign_ids,
            )

    logger.info("seed_complete",
                phases=await db.phases.count_documents({}),
                lessons=await db.lessons.count_documents({}),
                signs=await db.signs.count_documents({}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed SINALibras content catalog")
    parser.add_argument("--reset", action="store_true",
                        help="Drop phases/lessons/signs collections before seeding")
    args = parser.parse_args()
    asyncio.run(run(reset=args.reset))


if __name__ == "__main__":
    main()
