"""
Build the asset bundle for the sign catalog.

Pipeline (best-effort):
  1. For each of the 36 catalog terms, query Wikimedia Commons API for a
     potentially relevant Libras image. If a plausible match comes back,
     download it as <slug>.jpg.
  2. Always generate a themed SVG placeholder per term (gradient + emoji +
     term in Nunito) so every sign has at least *something* attractive.
  3. Emit `backend/static/signs/manifest.json` with `{ term: relative-url }`,
     consumed by `scripts/seed.py` at seed time.

Coverage reality: Wikimedia's Libras coverage for these specific words is
near zero. The script tries anyway so we ship the best version we can.

Run:
    python -m scripts.build_sign_assets               # generate everything
    python -m scripts.build_sign_assets --skip-wiki   # placeholders only

The script has zero runtime dependencies beyond the Python stdlib so it
runs in any minimal container.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

# ----------------------------- Catalog (mirrored from seed.py) --------------

CATALOG_TERMS: list[str] = [
    # Phase 1 — Cumprimentos
    "Olá", "Tchau", "Tudo bem?", "Obrigado",
    "Bom dia", "Boa tarde", "Boa noite", "Até logo",
    "Prazer", "Como vai?", "Me chamo", "Você",
    # Phase 2 — Família
    "Pai", "Mãe", "Filho", "Filha",
    "Irmão", "Irmã", "Bebê", "Família",
    "Avô", "Avó", "Tio", "Tia", "Primo",
    # Phase 3 — Cores
    "Vermelho", "Azul", "Amarelo", "Verde",
    "Branco", "Preto", "Cinza", "Marrom",
    "Rosa", "Roxo", "Laranja", "Dourado",
]

# Semantic emoji per term — chosen so the placeholder communicates meaning
# even before Libras content lands.
EMOJI_BY_TERM: dict[str, str] = {
    # Cumprimentos
    "Olá": "👋", "Tchau": "👋", "Tudo bem?": "🤔", "Obrigado": "🙏",
    "Bom dia": "🌅", "Boa tarde": "☀️", "Boa noite": "🌙", "Até logo": "👋",
    "Prazer": "🤝", "Como vai?": "💬", "Me chamo": "💁", "Você": "👉",
    # Família
    "Pai": "👨", "Mãe": "👩", "Filho": "👦", "Filha": "👧",
    "Irmão": "👬", "Irmã": "👭", "Bebê": "👶", "Família": "👨‍👩‍👧‍👦",
    "Avô": "👴", "Avó": "👵", "Tio": "🧔", "Tia": "🧑", "Primo": "🧑‍🤝‍🧑",
    # Cores — emoji is literally the color
    "Vermelho": "🔴", "Azul": "🔵", "Amarelo": "🟡", "Verde": "🟢",
    "Branco": "⚪", "Preto": "⚫", "Cinza": "🌫️", "Marrom": "🟤",
    "Rosa": "💗", "Roxo": "🟣", "Laranja": "🟠", "Dourado": "✨",
}

# Phase-tinted gradients (matches the Blue brand palette).
# Pattern: (stop1, stop2, text_color, eyebrow).
PALETTE_BY_TERM: dict[str, tuple[str, str, str, str]] = {}

# Cumprimentos — navy → primary blue (white text)
for term in CATALOG_TERMS[0:12]:
    PALETTE_BY_TERM[term] = ("#031f55", "#0446b0", "#FFFFFF", "CUMPRIMENTO")

# Cores — each term has its own bg
COLOR_PALETTE: dict[str, tuple[str, str, str]] = {
    "Vermelho":  ("#FCA5A5", "#DC2626", "#FFFFFF"),
    "Azul":      ("#93C5FD", "#1D4ED8", "#FFFFFF"),
    "Amarelo":   ("#FDE68A", "#EAB308", "#1F1611"),
    "Verde":     ("#86EFAC", "#15803D", "#FFFFFF"),
    "Branco":    ("#FFFFFF", "#E5E7EB", "#1F1611"),
    "Preto":     ("#374151", "#0F172A", "#FFFFFF"),
    "Cinza":     ("#D1D5DB", "#6B7280", "#FFFFFF"),
    "Marrom":    ("#D4A574", "#78350F", "#FFFFFF"),
    "Rosa":      ("#FBCFE8", "#DB2777", "#FFFFFF"),
    "Roxo":      ("#DDD6FE", "#7C3AED", "#FFFFFF"),
    "Laranja":   ("#FDBA74", "#EA580C", "#FFFFFF"),
    "Dourado":   ("#FDE68A", "#B45309", "#1F1611"),
}
for term, (a, b, txt) in COLOR_PALETTE.items():
    PALETTE_BY_TERM[term] = (a, b, txt, "COR")

# Família — peach → orange. Derived (everything that is neither a greeting nor
# a colour) instead of a fixed CATALOG_TERMS slice: the family group grows as
# real footage arrives, and a hardcoded slice would silently mis-tint the
# terms that fall off the end.
for term in CATALOG_TERMS[12:]:
    if term not in COLOR_PALETTE:
        PALETTE_BY_TERM[term] = ("#FED7AA", "#EA580C", "#1F1611", "FAMÍLIA")


# ----------------------------- Helpers --------------------------------------

def slugify(term: str) -> str:
    """Stable, filesystem-safe identifier per term."""
    norm = unicodedata.normalize("NFKD", term)
    ascii_only = norm.encode("ascii", "ignore").decode().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return cleaned or "sinal"


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
    )


# ----------------------------- Wikimedia search -----------------------------

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "SINALibras-AssetBuilder/1.0 (https://github.com/sinalibras; learning project)"


def query_wikimedia(term: str, *, timeout: float = 6.0) -> str | None:
    """
    Try to find an image on Commons whose title mentions Libras / sign language
    AND the term. Returns a direct image URL or None.

    The default query catches the alphabet etc., not random word matches.
    """
    queries = [
        f'"libras" "{term}"',
        f'"língua brasileira de sinais" "{term}"',
        f'"brazilian sign language" "{term}"',
    ]
    for q in queries:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": "6",    # File: namespace
            "gsrsearch": q,
            "gsrlimit": "3",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": "600",
        }
        url = f"{WIKIMEDIA_API}?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read())
        except Exception as exc:  # network errors are non-fatal here
            print(f"  wiki err [{term}] {exc}", file=sys.stderr)
            continue

        pages = (data.get("query") or {}).get("pages") or {}
        for page in pages.values():
            info_list = page.get("imageinfo") or []
            if not info_list:
                continue
            info = info_list[0]
            image_url = info.get("thumburl") or info.get("url")
            title = (page.get("title") or "").lower()
            if not image_url:
                continue
            # Reject PDF page-renders (Commons returns lots of 19th-century
            # Portuguese journals when you search a common Portuguese word).
            if ".pdf" in image_url.lower():
                continue
            # Require the file title itself to mention libras / sign language —
            # otherwise we just get random images that happen to share a word.
            if not any(kw in title for kw in ("libras", "signal", "sinai", "sign language", "sign_language")):
                continue
            if any(
                image_url.lower().split("?")[0].endswith(ext)
                for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")
            ):
                return image_url
    return None


def download(url: str, dest: Path, *, timeout: float = 10.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
    except Exception as exc:
        print(f"  download err {url}: {exc}", file=sys.stderr)
        return False
    dest.write_bytes(data)
    return True


# ----------------------------- SVG placeholder ------------------------------

def make_placeholder_svg(term: str) -> str:
    color_a, color_b, text_color, eyebrow = PALETTE_BY_TERM.get(
        term, ("#FCD34D", "#F59E0B", "#1F1611", "SINAL")
    )
    emoji = EMOJI_BY_TERM.get(term, "✨")
    safe_term = xml_escape(term)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" '
        'preserveAspectRatio="xMidYMid meet" role="img" '
        f'aria-label="Sinal: {safe_term}">'
        '<defs>'
        '<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{color_a}"/>'
        f'<stop offset="100%" stop-color="{color_b}"/>'
        '</linearGradient>'
        '</defs>'
        '<rect width="600" height="400" rx="20" fill="url(#g)"/>'
        # Eyebrow label
        f'<text x="300" y="60" text-anchor="middle" '
        'font-family="Nunito, system-ui, sans-serif" font-weight="900" '
        f'font-size="14" fill="{text_color}" opacity="0.7" '
        f'letter-spacing="4">{eyebrow}</text>'
        # Big emoji
        f'<text x="300" y="220" text-anchor="middle" '
        'font-family="Apple Color Emoji, Segoe UI Emoji, Noto Color Emoji, '
        'EmojiOne Color, Twemoji Mozilla, sans-serif" '
        f'font-size="140" dominant-baseline="middle">{emoji}</text>'
        # Term
        f'<text x="300" y="320" text-anchor="middle" '
        'font-family="Nunito, system-ui, sans-serif" font-weight="900" '
        f'font-size="48" fill="{text_color}">{safe_term}</text>'
        # Footer brand
        f'<text x="300" y="365" text-anchor="middle" '
        'font-family="Nunito, system-ui, sans-serif" font-weight="700" '
        f'font-size="13" fill="{text_color}" opacity="0.55" '
        'letter-spacing="3">SINALIBRAS</text>'
        '</svg>'
    )


# ----------------------------- Main -----------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Build asset bundle for signs.")
    parser.add_argument("--skip-wiki", action="store_true",
                        help="Skip Wikimedia queries; only generate placeholders.")
    parser.add_argument(
        "--out-dir", type=Path,
        default=Path(__file__).resolve().parent.parent / "static" / "signs",
        help="Where to write assets + manifest.json.",
    )
    args = parser.parse_args()

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, str] = {}
    wiki_hits = 0
    placeholder_count = 0

    # Disambiguate slug collisions (e.g. Avô/Avó both reduce to "avo" after
    # accent stripping). First write keeps the bare slug; subsequent ones
    # get -2, -3, ... suffixes.
    slug_counts: dict[str, int] = {}

    for term in CATALOG_TERMS:
        base_slug = slugify(term)
        slug_counts[base_slug] = slug_counts.get(base_slug, 0) + 1
        slug = base_slug if slug_counts[base_slug] == 1 else f"{base_slug}-{slug_counts[base_slug]}"
        rel_url: str | None = None

        # 1. Try Wikimedia (best-effort).
        if not args.skip_wiki:
            wiki_url = query_wikimedia(term)
            if wiki_url:
                # Use the original Wikimedia URL directly — no need to host
                # ourselves, and they have a CDN.
                rel_url = wiki_url
                wiki_hits += 1
                print(f"  wiki hit [{term}] {wiki_url}")

        # 2. Always emit a placeholder file so the disk has a fallback even
        #    when the wiki URL goes down or changes.
        placeholder_path = out_dir / f"{slug}.svg"
        placeholder_path.write_text(make_placeholder_svg(term), encoding="utf-8")
        placeholder_count += 1

        # 3. If wiki didn't find anything, point to our placeholder.
        if rel_url is None:
            rel_url = f"/signs/{slug}.svg"

        manifest[term] = rel_url

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Wrote {placeholder_count} placeholder SVG(s) to {out_dir}")
    print(f"Wikimedia hits: {wiki_hits}/{len(CATALOG_TERMS)}")
    print(f"Manifest: {out_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
