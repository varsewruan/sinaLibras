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
import secrets
import urllib.parse
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.security import hash_password
from app.db.mongo import connect_to_mongo, ensure_indexes
from app.models.base import utc_now
from app.models.lesson import Lesson
from app.models.phase import Phase
from app.models.sign import Sign
from app.models.user import StreakState, User

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


def _load_video_manifest() -> dict[str, dict[str, str]]:
    """Map term → {mp4, webm, poster} from scripts/build_sign_videos.py.

    Empty dict when no footage has been transcoded yet: signs keep their SVG
    placeholder and the frontend renders the image path. Most of the catalog
    sits in that state — only terms with real captures appear here.
    """
    settings = get_settings()
    manifest_path = Path(settings.SIGNS_DIR) / "video-manifest.json"
    if not manifest_path.is_file():
        logger.info("seed_video_manifest_missing", path=str(manifest_path))
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
            {"order": 3, "title": "Avós, tios e primos", "xp_reward": 30,
             "signs": ["Avô", "Avó", "Tio", "Tia", "Primo"]},
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


# Demo leaderboard population. Opt-in via --demo-users: never seed these into
# a real deployment. Each gets a random unusable password, so the accounts
# exist for the ranking but nobody can log in as them.
DEMO_USERS = [
    {"name": "Ana Beatriz",  "avatar": "unicorn", "xp": 1840, "streak": 23},
    {"name": "Carlos Mendes", "avatar": "fox",    "xp": 1520, "streak": 14},
    {"name": "Duda Rocha",   "avatar": "owl",     "xp": 1275, "streak": 31},
    {"name": "Rafael Lima",  "avatar": "robot",   "xp": 1040, "streak": 7},
    {"name": "Juliana Alves", "avatar": "cat",    "xp": 890,  "streak": 11},
    {"name": "Pedro Nunes",  "avatar": "hero",    "xp": 720,  "streak": 5},
    {"name": "Marina Costa", "avatar": "frog",    "xp": 610,  "streak": 9},
    {"name": "Tiago Ferraz", "avatar": "ninja",   "xp": 430,  "streak": 3},
    {"name": "Letícia Souza", "avatar": "panda",  "xp": 260,  "streak": 2},
    {"name": "Bruno Tavares", "avatar": "alien",  "xp": 120,  "streak": 1},
]


def _placeholder_url(term: str) -> str:
    """Legacy fallback when no manifest entry exists for a term."""
    safe = urllib.parse.quote(term)
    return f"https://placehold.co/600x400/1E293B/F59E0B?text=Sinal%3A+{safe}"


# ----------------------------- Seeding logic --------------------------------

async def _seed_sign(
    db: AsyncIOMotorDatabase,
    term: str,
    *,
    manifest: dict[str, str],
    videos: dict[str, dict[str, str]],
) -> str:
    """Upsert the sign and keep its media in sync with both manifests."""
    video = videos.get(term) or {}
    assets = {
        "thumbnail_url": manifest.get(term) or _placeholder_url(term),
        # Doubles as the card's caption and the media element's accessible
        # name, so it has to track whether footage actually exists — a filmed
        # sign captioned "placeholder" reads as a bug to the user.
        "text_description": (
            f"Sinal de '{term}' em Libras, demonstrado em vídeo."
            if video else
            f"Sinal de '{term}' — ilustração provisória até o vídeo chegar."
        ),
        # None (not absent) when a term has no footage, so a clip that gets
        # pulled — e.g. a defective capture removed from SOURCE_MAP — actually
        # clears the stale URL instead of leaving a 404 behind.
        "video_url": video.get("mp4"),
        "video_webm_url": video.get("webm"),
        "poster_url": video.get("poster"),
    }

    existing = await db.signs.find_one({"portuguese_term": term})
    if existing:
        # Catch the seed → asset-rebuild → re-seed cycle: update media in
        # place when a manifest URL drifts.
        drifted = {k: v for k, v in assets.items() if existing.get(k) != v}
        if drifted:
            await db.signs.update_one({"_id": existing["_id"]}, {"$set": drifted})
            logger.info("seed_sign_media_updated", term=term, id=existing["_id"],
                        fields=sorted(drifted))
        return existing["_id"]

    sign = Sign(
        portuguese_term=term,
        libras_description=f"Demonstração do sinal '{term}' em Libras.",
        **assets,
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


async def _seed_demo_users(db: AsyncIOMotorDatabase) -> None:
    """Populate the leaderboard with sample players. Idempotent by email."""
    for spec in DEMO_USERS:
        slug = spec["name"].split()[0].lower()
        email = f"{slug}@demo.sinalibras.dev"
        if await db.users.find_one({"email": email}):
            continue

        now = utc_now()
        user = User(
            email=email,
            name=spec["name"],
            # Random secret => the account can never be logged into.
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            avatar=spec["avatar"],
            xp=spec["xp"],
            streak=StreakState(
                current=spec["streak"],
                longest=spec["streak"],
                last_activity_at=now,
            ),
        )
        await db.users.insert_one(user.to_mongo())
        logger.info("seed_demo_user_inserted", name=spec["name"], xp=spec["xp"])


async def _seed_phase(db: AsyncIOMotorDatabase, *, order: int, title: str, description: str) -> str:
    existing = await db.phases.find_one({"order": order})
    if existing:
        return existing["_id"]
    phase = Phase(title=title, description=description, order=order)
    await db.phases.insert_one(phase.to_mongo())
    logger.info("seed_phase_inserted", title=title, order=order)
    return phase.id


async def run(*, reset: bool, demo_users: bool = False) -> None:
    settings = get_settings()
    setup_logging(settings)
    db = await connect_to_mongo(settings)
    await ensure_indexes(db)

    manifest = _load_manifest()
    if manifest:
        logger.info("seed_manifest_loaded", terms=len(manifest))

    videos = _load_video_manifest()
    if videos:
        logger.info("seed_video_manifest_loaded", terms=len(videos))

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
                await _seed_sign(db, term, manifest=manifest, videos=videos)
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

    if demo_users:
        await _seed_demo_users(db)

    logger.info("seed_complete",
                phases=await db.phases.count_documents({}),
                lessons=await db.lessons.count_documents({}),
                signs=await db.signs.count_documents({}),
                users=await db.users.count_documents({}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed SINALibras content catalog")
    parser.add_argument("--reset", action="store_true",
                        help="Drop phases/lessons/signs collections before seeding")
    parser.add_argument("--demo-users", action="store_true",
                        help="Also insert sample players so the ranking has content. "
                             "Never use in production.")
    args = parser.parse_args()
    asyncio.run(run(reset=args.reset, demo_users=args.demo_users))


if __name__ == "__main__":
    main()
