"""
Catálogo da loja — avatares e acessórios comprados com XP.

Catálogo mora no código, não no banco, pela mesma razão que o de conquistas
(`app/models/achievement.py`): é conteúdo curado, versionado junto com a UI que
o desenha, e não faz sentido alguém editar em produção sem deploy.

## A regra do saldo

`user.xp` é o XP **ganho na vida inteira** e nunca diminui — é ele que alimenta
ranking, nível e conquistas. Comprar não mexe nele; incrementa `user.xp_spent`.
O saldo gastável é `xp - xp_spent`.

Isso é deliberado: se a compra descontasse de `xp`, comprar um chapéu faria o
jogador cair no ranking, regredir de nível e **perder conquistas já
desbloqueadas** (elas são derivadas do XP a cada request, não armazenadas).
Estudar viraria prejuízo. Decidido em 2026-07-18.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

ItemKind = Literal["avatar", "accessory"]


class ShopItem(BaseModel):
    """Uma peça à venda. `emoji` é o que a UI desenha — não há assets."""

    id: str
    kind: ItemKind
    label: str
    emoji: str
    price: int = Field(..., ge=0)


# --------------------------------------------------------------------------
# Avatares
# --------------------------------------------------------------------------
# Preço 0 = inicial, já disponível pra todo mundo sem compra. Sem pelo menos um
# gratuito, uma conta nova não teria avatar nenhum pra usar.
#
# Os ids TÊM que existir em AVATAR_IDS (app/models/user.py), senão a compra
# passa e o equipamento é rejeitado com 422 — o allowlist é a autoridade.

AVATAR_ITEMS: list[ShopItem] = [
    ShopItem(id="dummy",   kind="avatar", label="Padrão",    emoji="🧑", price=0),
    ShopItem(id="cat",     kind="avatar", label="Gato",      emoji="🐱", price=100),
    ShopItem(id="dog",     kind="avatar", label="Cachorro",  emoji="🐶", price=100),
    ShopItem(id="rabbit",  kind="avatar", label="Coelho",    emoji="🐰", price=150),
    ShopItem(id="frog",    kind="avatar", label="Sapo",      emoji="🐸", price=150),
    ShopItem(id="monkey",  kind="avatar", label="Macaco",    emoji="🐵", price=200),
    ShopItem(id="bear",    kind="avatar", label="Urso",      emoji="🐻", price=250),
    ShopItem(id="fox",     kind="avatar", label="Raposa",    emoji="🦊", price=300),
    ShopItem(id="panda",   kind="avatar", label="Panda",     emoji="🐼", price=350),
    ShopItem(id="tiger",   kind="avatar", label="Tigre",     emoji="🐯", price=400),
    ShopItem(id="lion",    kind="avatar", label="Leão",      emoji="🦁", price=500),
    ShopItem(id="owl",     kind="avatar", label="Coruja",    emoji="🦉", price=250),
    ShopItem(id="robot",   kind="avatar", label="Robô",      emoji="🤖", price=300),
    ShopItem(id="hero",    kind="avatar", label="Herói",     emoji="🦸", price=450),
    ShopItem(id="alien",   kind="avatar", label="Alien",     emoji="👽", price=450),
    ShopItem(id="ninja",   kind="avatar", label="Ninja",     emoji="🥷", price=600),
    ShopItem(id="unicorn", kind="avatar", label="Unicórnio", emoji="🦄", price=800),
    ShopItem(id="star",    kind="avatar", label="Estrela",   emoji="⭐", price=1000),
]

# --------------------------------------------------------------------------
# Acessórios
# --------------------------------------------------------------------------
# Ficam por cima do avatar (ver frontend/src/components/UserAvatar.jsx).
# Só um por vez — é chapéu, não coleção.

ACCESSORY_ITEMS: list[ShopItem] = [
    ShopItem(id="acc-oculos-vermelho", kind="accessory", label="Óculos vermelho",   emoji="🕶️", price=50),
    ShopItem(id="acc-oculos-grau",     kind="accessory", label="Óculos de grau",    emoji="👓", price=50),
    ShopItem(id="acc-bone",            kind="accessory", label="Boné",              emoji="🧢", price=80),
    ShopItem(id="acc-fones",           kind="accessory", label="Fones",             emoji="🎧", price=100),
    ShopItem(id="acc-cachecol",        kind="accessory", label="Cachecol",          emoji="🧣", price=120),
    ShopItem(id="acc-oculos-esqui",    kind="accessory", label="Óculos de esqui",   emoji="🥽", price=150),
    ShopItem(id="acc-laco",            kind="accessory", label="Laço",              emoji="🎀", price=150),
    ShopItem(id="acc-flores",          kind="accessory", label="Coroa de flores",   emoji="🌸", price=200),
    ShopItem(id="acc-festa",           kind="accessory", label="Chapéu de festa",   emoji="🥳", price=200),
    ShopItem(id="acc-cowboy",          kind="accessory", label="Chapéu de cowboy",  emoji="🤠", price=250),
    ShopItem(id="acc-capacete",        kind="accessory", label="Capacete",          emoji="⛑️", price=300),
    ShopItem(id="acc-cartola",         kind="accessory", label="Cartola",           emoji="🎩", price=350),
    ShopItem(id="acc-capelo",          kind="accessory", label="Capelo",            emoji="🎓", price=400),
    ShopItem(id="acc-coracoes",        kind="accessory", label="Corações",          emoji="😍", price=450),
    ShopItem(id="acc-coroa",           kind="accessory", label="Coroa",             emoji="👑", price=1000),
]

CATALOG: list[ShopItem] = [*AVATAR_ITEMS, *ACCESSORY_ITEMS]

_BY_ID: dict[str, ShopItem] = {item.id: item for item in CATALOG}

ACCESSORY_IDS: frozenset[str] = frozenset(item.id for item in ACCESSORY_ITEMS)


def get_item(item_id: str) -> Optional[ShopItem]:
    return _BY_ID.get(item_id)


def free_item_ids() -> frozenset[str]:
    """Itens de preço 0 — valem como 'possuídos' sem nunca terem sido comprados."""
    return frozenset(item.id for item in CATALOG if item.price == 0)


def is_owned(item: ShopItem, owned_items: list[str]) -> bool:
    return item.price == 0 or item.id in owned_items


# --------------------------------------------------------------------------
# DTOs
# --------------------------------------------------------------------------


class ShopItemView(BaseModel):
    """Item + estado para o usuário atual."""

    id: str
    kind: ItemKind
    label: str
    emoji: str
    price: int
    owned: bool
    equipped: bool


class ShopView(BaseModel):
    balance: int
    xp_total: int
    xp_spent: int
    items: list[ShopItemView]


class PurchaseRequest(BaseModel):
    item_id: str = Field(..., max_length=64)
