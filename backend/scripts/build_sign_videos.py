"""
Transcode the raw sign-language captures into web-deliverable video.

The source clips are QuickTime Animation (`qtrle`, `argb`) — lossless RGB with
a real alpha channel, 1920x1080, ~1-3.3s each, around 50 MB per second of
footage. No browser plays that container, so every clip becomes three files:

  <slug>.webm          VP9 with alpha (yuva420p) — Chrome / Firefox / Edge
  <slug>.mp4           H.264, alpha flattened onto the card colour — Safari / iOS
  <slug>-poster.jpg    middle frame, same flattening — <video poster>

Two encodes exist because no single codec gives transparency everywhere:
VP9-alpha is unsupported in Safari, and HEVC-with-alpha (the Safari answer)
needs a macOS encoder we do not have. The frontend lists both in <source>
order, so Safari silently falls back to the flattened MP4.

Run (from backend/), pointing --src at the folder that holds the per-phase
subdirectories (Cumprimentos/, Familia/, Cores/):
    python -m scripts.build_sign_videos --src ".../Sinais (1)"
    python -m scripts.build_sign_videos --src ... --only bom-dia   # one slug
    python -m scripts.build_sign_videos --src ... --list           # dry run

Requires ffmpeg on PATH (or --ffmpeg). Reads the source directory, never
writes to it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.build_sign_assets import slugify

# ----------------------------- Source mapping -------------------------------
# Source clip (path relative to --src, no extension) → catalog terms it fills.
#
# The corpus is organised in per-phase subfolders (Cumprimentos/, Familia/,
# Cores/), so each key carries that subpath: `args.src / f"{key}.mov"`.
#
# Terms MUST match CATALOG_TERMS in build_sign_assets.py character for
# character (including the "?" in "Tudo bem?" and "Como vai?") — the manifest
# is keyed by term and seed.py looks it up verbatim.
#
# This is the 2026-07-22 re-shoot: one clean recording per term, so the map is
# 1:1. The retired first corpus shared a clip across "Tio"/"Tia" and
# "Irmão"/"Irmã"; these give each its own footage. Entries are in catalog
# order so the slug dedup in main() assigns "avo"/"avo-2" to "Avô"/"Avó" the
# same way build_sign_assets.py does for the SVGs.
#
# This map covers every catalog term. "Obrigado" and "Cinza" had no footage
# and were dropped from the catalog on 2026-07-22, so nothing here falls back
# to an SVG. "prima.mov" was shot but the catalog has no "Prima" term (only
# "Primo"), so it is left out.
SOURCE_MAP: dict[str, list[str]] = {
    # Fase 1 — Cumprimentos
    "Cumprimentos/olá":       ["Olá"],
    "Cumprimentos/tchau":     ["Tchau"],
    "Cumprimentos/tudo bem":  ["Tudo bem?"],
    "Cumprimentos/bom dia":   ["Bom dia"],
    "Cumprimentos/boa tarde": ["Boa tarde"],
    "Cumprimentos/boa noite": ["Boa noite"],
    "Cumprimentos/até logo":  ["Até logo"],
    "Cumprimentos/prazer":    ["Prazer"],
    "Cumprimentos/como vai":  ["Como vai?"],
    "Cumprimentos/me chamo":  ["Me chamo"],
    "Cumprimentos/você":      ["Você"],
    # Fase 2 — Família
    "Familia/pai":      ["Pai"],
    "Familia/mãe":      ["Mãe"],
    "Familia/filho":    ["Filho"],
    "Familia/filha":    ["Filha"],
    "Familia/irmão":    ["Irmão"],
    "Familia/irmã":     ["Irmã"],
    "Familia/bebê":     ["Bebê"],
    "Familia/família":  ["Família"],
    "Familia/avô":      ["Avô"],
    "Familia/avó":      ["Avó"],
    "Familia/tio":      ["Tio"],
    "Familia/tia":      ["Tia"],
    "Familia/primo":    ["Primo"],
    # Fase 3 — Cores
    "Cores/vermelho":        ["Vermelho"],
    "Cores/azul":            ["Azul"],
    "Cores/amarelo":         ["Amarelo"],
    "Cores/verde":           ["Verde"],
    "Cores/branco":          ["Branco"],
    "Cores/preto":           ["Preto"],
    "Cores/marrom castanho": ["Marrom"],
    "Cores/rosa":            ["Rosa"],
    "Cores/roxo":            ["Roxo"],
    "Cores/laranja":         ["Laranja"],
    "Cores/dourado":         ["Dourado"],
}

# Per-clip workarounds for source defects, all keyed by `source.stem` (the file
# name with no folder or extension, e.g. "bom dia"):
#   DAMAGED     — clip with a block of destroyed pixels (botched watermark
#                 removal), baked into the RGB; ships anyway, only documental.
#   CROP_HEIGHT — pixels to keep from the top, to cut a caption graphic burned
#                 into the lower band (the term spelled out = the quiz answer).
#   SLOWDOWN    — setpts factor for a clip too short to loop without strobing.
#
# The 2026-07-22 corpus is clean — no burned captions, no destroyed pixels,
# every clip runs ≥1s and loops on its own — so all three are empty. They stay
# as the documented lever for a future clip that regresses; git history shows
# how the retired first corpus used each.
DAMAGED: dict[str, list[str]] = {}
CROP_HEIGHT: dict[str, int] = {}
SLOWDOWN: dict[str, float] = {}

SRC_WIDTH = 1920
SRC_HEIGHT = 1080

# ----------------------------- Encoding settings ----------------------------

# Matches --card in frontend/src/index.css (219 52% 19% → #172f4f). The MP4
# has no alpha, so the subject is composited onto the surface it will sit on.
# If the theme's card colour changes, re-run this script.
CARD_COLOR = "0x172f4f"

# 1080p is far more than a card needs and doubles the VP9 encode time.
OUT_WIDTH = 960

# The captures declare a 1/1323000000 timebase — its denominator is above
# libvpx-vp9's g_timebase limit (1e9), so VP9 refuses to open the encoder on
# the raw stream. Resampling to a fixed frame rate hands every encoder a sane
# 1/FPS timebase; 30 matches the sources' ~30.01 fps and yields CFR web output.
FPS = 30

VIDEO_SUBDIR = "video"
MANIFEST_NAME = "video-manifest.json"


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # ffmpeg puts everything on stderr; surface the tail, not the banner.
        tail = "\n".join(result.stderr.strip().splitlines()[-12:])
        raise RuntimeError(f"ffmpeg failed ({result.returncode}):\n{tail}")


def _source_chain(crop_h: int, slow: float) -> str:
    """Filters applied to the raw capture before every encode, in order."""
    steps = [f"crop={SRC_WIDTH}:{crop_h}:0:0"]
    if slow != 1.0:
        # setpts rewrites timestamps, so the frames simply hold longer. Nothing
        # is interpolated — see SLOWDOWN.
        steps.append(f"setpts={slow}*PTS")
    steps.append(f"scale={OUT_WIDTH}:-2")
    # Last, so a SLOWDOWN setpts above just repeats frames to fill the stretched
    # duration, and so every encode gets the sane timebase FPS documents.
    steps.append(f"fps={FPS}")
    return ",".join(steps)


def encode_webm(ffmpeg: str, src: Path, dest: Path, *, crop_h: int, slow: float) -> None:
    """VP9 with a preserved alpha channel."""
    _run([
        ffmpeg, "-y", "-v", "error",
        "-i", str(src),
        "-map", "0:v:0",              # source carries a stray non-video stream
        "-an",                        # signs are silent; drop audio entirely
        "-vf", _source_chain(crop_h, slow),
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p",       # the "a" is the whole point
        "-crf", "32", "-b:v", "0",
        "-row-mt", "1",
        str(dest),
    ])


def encode_mp4(ffmpeg: str, src: Path, dest: Path, *, crop_h: int, slow: float) -> None:
    """H.264 with the subject flattened onto the card colour."""
    _run([
        ffmpeg, "-y", "-v", "error",
        "-f", "lavfi", "-i", f"color={CARD_COLOR}:{SRC_WIDTH}x{crop_h}",
        "-i", str(src),
        "-filter_complex",
        f"[1:v]{_source_chain(crop_h, slow)}[fg];"
        f"[0:v]scale={OUT_WIDTH}:-2[bg];"
        f"[bg][fg]overlay=shortest=1,format=yuv420p",
        "-an",
        "-c:v", "libx264",
        "-crf", "24",
        "-preset", "slow",
        "-movflags", "+faststart",    # first frame paints before full download
        str(dest),
    ])


def encode_poster(ffmpeg: str, src: Path, dest: Path, *, duration: float, crop_h: int) -> None:
    """Middle frame, flattened — what <video poster> shows before playback."""
    # Seek with `trim`, not `-ss` before `-i`. qtrle stores inter-frame deltas,
    # so an input seek jumps into the middle of a delta chain and yields an
    # empty frame — every poster came out as flat background colour.
    _run([
        ffmpeg, "-y", "-v", "error",
        "-f", "lavfi", "-i", f"color={CARD_COLOR}:{SRC_WIDTH}x{crop_h}",
        "-i", str(src),
        "-filter_complex",
        f"[1:v]trim=start={duration / 2:.3f},setpts=PTS-STARTPTS,"
        f"crop={SRC_WIDTH}:{crop_h}:0:0,scale={OUT_WIDTH}:-2[fg];"
        f"[0:v]scale={OUT_WIDTH}:-2[bg];"
        f"[bg][fg]overlay=shortest=1,format=yuvj420p",
        "-frames:v", "1", "-q:v", "4",
        str(dest),
    ])


def probe_duration(ffprobe: str, src: Path) -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(src)],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 1.0


def main() -> None:
    default_out = Path(__file__).resolve().parent.parent / "static" / "signs"
    parser = argparse.ArgumentParser(description="Transcode sign clips for the web.")
    parser.add_argument("--src", type=Path, required=True,
                        help="Directory holding the raw .mov captures (read-only).")
    parser.add_argument("--out-dir", type=Path, default=default_out,
                        help="Sign asset directory; videos land in <out-dir>/video/.")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="Path to the ffmpeg binary.")
    parser.add_argument("--ffprobe", default="ffprobe", help="Path to the ffprobe binary.")
    parser.add_argument("--only", help="Encode a single slug (debugging).")
    parser.add_argument("--list", action="store_true",
                        help="Show what would be encoded and exit.")
    args = parser.parse_args()

    ffmpeg = shutil.which(args.ffmpeg) or args.ffmpeg
    ffprobe = shutil.which(args.ffprobe) or args.ffprobe

    video_dir: Path = args.out_dir / VIDEO_SUBDIR
    manifest: dict[str, dict[str, str]] = {}
    plan: list[tuple[Path, str, list[str]]] = []

    # Disambiguate slug collisions the same way build_sign_assets.py does:
    # "Avô" and "Avó" both reduce to "avo" after accent stripping, so the
    # second keeps "avo-2". Count over every mapped clip (missing or --only
    # skipped included) so a term's slug never depends on which clips run.
    slug_counts: dict[str, int] = {}
    for stem, terms in SOURCE_MAP.items():
        source = args.src / f"{stem}.mov"
        base = slugify(terms[0])
        slug_counts[base] = slug_counts.get(base, 0) + 1
        slug = base if slug_counts[base] == 1 else f"{base}-{slug_counts[base]}"
        if args.only and slug != args.only:
            continue
        if not source.is_file():
            print(f"  ausente: {source.name} (pulando {', '.join(terms)})", file=sys.stderr)
            continue
        plan.append((source, slug, terms))

    if args.list:
        for source, slug, terms in plan:
            mb = source.stat().st_size / 1024 / 1024
            print(f"  {slug:12} <- {source.name:18} ({mb:6.1f} MB)  ->  {', '.join(terms)}")
        for stem in DAMAGED:
            print(f"  {'^ avariado':12}    {stem + '.mov'}")
        return

    if not plan:
        print("Nada a fazer — verifique --src.", file=sys.stderr)
        raise SystemExit(1)

    video_dir.mkdir(parents=True, exist_ok=True)
    total_in = total_out = 0

    for source, slug, terms in plan:
        crop_h = CROP_HEIGHT.get(source.stem, SRC_HEIGHT)
        slow = SLOWDOWN.get(source.stem, 1.0)
        notes = []
        if crop_h != SRC_HEIGHT:
            notes.append(f"corte {crop_h}px")
        if slow != 1.0:
            notes.append(f"{slow:g}x mais lento")
        note = f"  ({', '.join(notes)})" if notes else ""
        print(f"  {slug} …{note}", flush=True)
        webm = video_dir / f"{slug}.webm"
        mp4 = video_dir / f"{slug}.mp4"
        poster = video_dir / f"{slug}-poster.jpg"

        encode_webm(ffmpeg, source, webm, crop_h=crop_h, slow=slow)
        encode_mp4(ffmpeg, source, mp4, crop_h=crop_h, slow=slow)
        encode_poster(ffmpeg, source, poster, crop_h=crop_h,
                      duration=probe_duration(ffprobe, source))

        total_in += source.stat().st_size
        total_out += webm.stat().st_size + mp4.stat().st_size + poster.stat().st_size

        entry = {
            "webm": f"/signs/{VIDEO_SUBDIR}/{webm.name}",
            "mp4": f"/signs/{VIDEO_SUBDIR}/{mp4.name}",
            "poster": f"/signs/{VIDEO_SUBDIR}/{poster.name}",
        }
        for term in terms:
            manifest[term] = entry

    # Merge with whatever is already on disk so --only does not wipe the rest.
    manifest_path = args.out_dir / MANIFEST_NAME
    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        existing.update(manifest)
        manifest = existing

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print()
    print(f"{len(plan)} clipe(s) -> {len(manifest)} termo(s) com vídeo")
    print(f"{total_in / 1024 / 1024:.0f} MB de origem -> {total_out / 1024 / 1024:.1f} MB entregues")
    print(f"Manifesto: {manifest_path}")
    shipped_damaged = [s for s in DAMAGED if s in {p[0].stem for p in plan}]
    if shipped_damaged:
        print(f"Com avaria visível na fonte: {len(shipped_damaged)} clipe(s) — ver DAMAGED no topo do script.")


if __name__ == "__main__":
    main()
