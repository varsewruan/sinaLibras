"""
Transcode the raw sign-language captures into web-deliverable video.

The source clips are QuickTime Animation (`qtrle`, `argb`) — lossless RGB with
a real alpha channel, 1920x1080, ~1-1.6s each, around 50 MB per second of
footage. No browser plays that container, so every clip becomes three files:

  <slug>.webm          VP9 with alpha (yuva420p) — Chrome / Firefox / Edge
  <slug>.mp4           H.264, alpha flattened onto the card colour — Safari / iOS
  <slug>-poster.jpg    middle frame, same flattening — <video poster>

Two encodes exist because no single codec gives transparency everywhere:
VP9-alpha is unsupported in Safari, and HEVC-with-alpha (the Safari answer)
needs a macOS encoder we do not have. The frontend lists both in <source>
order, so Safari silently falls back to the flattened MP4.

Run (from backend/):
    python -m scripts.build_sign_videos --src "C:/.../SINAIS/SINAIS"
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
# Source stem (no extension) → catalog terms it provides video for.
#
# Terms MUST match CATALOG_TERMS in build_sign_assets.py character for
# character (including the "?" in "Tudo bem?") — the manifest is keyed by term
# and seed.py looks it up verbatim.
#
# Some clips cover two catalog entries: the source corpus records one gesture
# for "Tio - Tia" and one for "Irmãos". Both terms point at the same encoded
# files rather than duplicating the bytes; the file is named after the first
# term's slug.
SOURCE_MAP: dict[str, list[str]] = {
    "Boa noite_1_1": ["Boa noite"],
    "Boa tarde_1":  ["Boa tarde"],
    "Oi - Olá_1":   ["Olá"],
    "Bom dia_1":    ["Bom dia"],
    "Filho_1":      ["Filho"],
    "Irmãos_1":     ["Irmão", "Irmã"],
    "Mãe_1":        ["Mãe"],
    "Pai_1":        ["Pai"],
    "Primo(a)_1":   ["Primo"],
    "Tio - Tia_1":  ["Tio", "Tia"],
    "Tudo bem_1":   ["Tudo bem?"],
}

# Clips whose source has a rectangular block of destroyed pixels over the
# torso — a botched watermark removal, baked into the RGB and not just the
# alpha mask, so nothing here can recover it. The fix is a clean re-export
# from the original footage.
#
# They ship anyway: a visible blemish beats no demo at all for the greetings,
# which are the first phase a learner sees. Move an entry here into nothing —
# just drop it from SOURCE_MAP — to fall back to the SVG placeholder instead.
DAMAGED: dict[str, list[str]] = {
    "Boa noite_1_1": ["Boa noite"],
    "Boa tarde_1":   ["Boa tarde"],
    "Oi - Olá_1":    ["Olá"],
}

# Some captures have a caption graphic burned into the lower band — the term
# spelled out in Portuguese. Lesson.jsx shows the sign as a quiz prompt, so
# that band is literally the answer printed on screen; it gets cropped away.
#
# Value is how much of the 1920x1080 source to keep, measured from the top.
# Verify a new entry by eye before trusting it: these signs are performed at
# chest height and cropping too far eats the gesture.
CROP_HEIGHT: dict[str, int] = {
    "Bom dia_1": 780,  # "BOM DIA" label fades in over the second half
}

# Playback slowdown, per clip. Most captures run 0.7-1.6s and loop fine at
# native speed; "Tudo bem" is four frames (0.13s) and strobes instead of
# looping. Slowing it is the only lever the footage allows — those four frames
# are nearly identical, so the gesture was never recorded and no amount of
# interpolation would invent it. At 8x the clip reads as a held pose, which is
# honest about what the source contains. A real capture would replace this.
SLOWDOWN: dict[str, float] = {
    "Tudo bem_1": 8.0,
}

SRC_WIDTH = 1920
SRC_HEIGHT = 1080

# ----------------------------- Encoding settings ----------------------------

# Matches --card in frontend/src/index.css (219 52% 19% → #172f4f). The MP4
# has no alpha, so the subject is composited onto the surface it will sit on.
# If the theme's card colour changes, re-run this script.
CARD_COLOR = "0x172f4f"

# 1080p is far more than a card needs and doubles the VP9 encode time.
OUT_WIDTH = 960

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

    for stem, terms in SOURCE_MAP.items():
        source = args.src / f"{stem}.mov"
        slug = slugify(terms[0])
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
    print(f"{len(plan)} clipe(s) → {len(manifest)} termo(s) com vídeo")
    print(f"{total_in / 1024 / 1024:.0f} MB de origem → {total_out / 1024 / 1024:.1f} MB entregues")
    print(f"Manifesto: {manifest_path}")
    shipped_damaged = [s for s in DAMAGED if s in {p[0].stem for p in plan}]
    if shipped_damaged:
        print(f"Com avaria visível na fonte: {len(shipped_damaged)} clipe(s) — ver DAMAGED no topo do script.")


if __name__ == "__main__":
    main()
