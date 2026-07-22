"""
Gera o ícone do app (desktop/icon.ico + frontend/public/favicon.ico).

Um "S" branco sobre disco azul da marca, com um anel amarelo — as duas cores
do SINALibras. Feito em código em vez de um .png solto no repo pra que mudar a
paleta seja mexer nos hex daqui e rodar de novo.

Uso:
    python desktop/make_icon.py

Precisa de Pillow (só pra gerar; não é dependência do app).
O .ico carrega vários tamanhos: o Windows escolhe 16px na barra de tarefas e
256px no Explorer, e deixar ele reduzir sozinho a partir de um tamanho único
borra o traço nos pequenos.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AZUL = (74, 151, 255, 255)      # #4a97ff — azul da marca
AMARELO = (255, 198, 26, 255)   # #ffc61a — amarelo da marca
BRANCO = (255, 255, 255, 255)

TAMANHOS = [16, 24, 32, 48, 64, 128, 256]
BASE = 256  # desenha grande e reduz: bordas ficam suaves


def _fonte(tamanho: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for nome in ("segoeuib.ttf", "arialbd.ttf", "seguisb.ttf"):
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    return ImageFont.load_default()


def desenhar() -> Image.Image:
    img = Image.new("RGBA", (BASE, BASE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Anel amarelo + disco azul, chapados. Já tentei uma "sombra interna" aqui:
    # em 256px parecia um disco meio escuro pela metade, e em 16px virava
    # sujeira. Ícone pequeno pede forma sólida, não profundidade.
    d.ellipse([0, 0, BASE - 1, BASE - 1], fill=AMARELO)
    margem = int(BASE * 0.08)
    d.ellipse([margem, margem, BASE - 1 - margem, BASE - 1 - margem], fill=AZUL)

    # "S" centralizado.
    fonte = _fonte(int(BASE * 0.62))
    caixa = d.textbbox((0, 0), "S", font=fonte)
    largura, altura = caixa[2] - caixa[0], caixa[3] - caixa[1]
    d.text(
        ((BASE - largura) / 2 - caixa[0], (BASE - altura) / 2 - caixa[1]),
        "S",
        font=fonte,
        fill=BRANCO,
    )
    return img


def main() -> None:
    raiz = Path(__file__).resolve().parent.parent
    img = desenhar()
    destinos = [
        raiz / "desktop" / "icon.ico",
        raiz / "frontend" / "public" / "favicon.ico",
    ]
    for destino in destinos:
        destino.parent.mkdir(parents=True, exist_ok=True)
        img.save(destino, format="ICO", sizes=[(t, t) for t in TAMANHOS])
        print(f"gravado: {destino}")


if __name__ == "__main__":
    main()
