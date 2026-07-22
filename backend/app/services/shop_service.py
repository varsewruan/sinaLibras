"""
Compra e equipamento de itens da loja.

Tudo que decide preço, saldo e posse vive aqui — o cliente manda no máximo um
`item_id`. Preço não vem do request justamente pra ninguém comprar uma coroa
de 1000 XP dizendo que custa 1.

A cobrança incrementa `xp_spent`; `xp` (ranking/nível/conquistas) fica intacto.
Ver o cabeçalho de app/models/shop.py para o porquê.
"""

from __future__ import annotations

from app.models.base import utc_now
from app.models.shop import (
    CATALOG,
    ShopItem,
    ShopItemView,
    ShopView,
    get_item,
    is_owned,
)
from app.models.user import AVATAR_IDS, User
from app.repositories.user_repo import UserRepository


class ShopError(Exception):
    """`code` é contrato de máquina (inglês); `message` é lido por gente."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def balance_of(user: User) -> int:
    # max(0, ...) protege contra um estado impossível (gasto > ganho) virar
    # saldo negativo na tela caso algum dia um dado seja corrigido à mão.
    return max(0, user.xp - user.xp_spent)


class ShopService:
    def __init__(self, *, users: UserRepository) -> None:
        self.users = users

    def catalog_for(self, user: User) -> ShopView:
        items = [
            ShopItemView(
                id=item.id,
                kind=item.kind,
                label=item.label,
                emoji=item.emoji,
                price=item.price,
                owned=is_owned(item, user.owned_items),
                equipped=self._is_equipped(item, user),
            )
            for item in CATALOG
        ]
        return ShopView(
            balance=balance_of(user),
            xp_total=user.xp,
            xp_spent=user.xp_spent,
            items=items,
        )

    async def purchase(self, *, user: User, item_id: str) -> tuple[User, ShopItem]:
        item = get_item(item_id)
        if item is None:
            raise ShopError("item_not_found", "Este item não existe.")

        if is_owned(item, user.owned_items):
            # Idempotência importa: um duplo clique não pode cobrar duas vezes.
            raise ShopError("already_owned", "Você já tem este item.")

        balance = balance_of(user)
        if balance < item.price:
            raise ShopError(
                "insufficient_xp",
                f"Faltam {item.price - balance} XP para comprar {item.label}.",
            )

        updated = await self.users.update_fields(
            user.id,
            {
                "xp_spent": user.xp_spent + item.price,
                "owned_items": [*user.owned_items, item.id],
                "updated_at": utc_now(),
            },
        )
        final = updated or user.model_copy(
            update={
                "xp_spent": user.xp_spent + item.price,
                "owned_items": [*user.owned_items, item.id],
            }
        )
        return final, item

    async def equip(self, *, user: User, item_id: str) -> User:
        """Veste um item já possuído.

        Avatar troca o avatar; acessório troca o acessório. São campos
        separados porque um não substitui o outro — dá pra usar bicho + chapéu.
        """
        item = get_item(item_id)
        if item is None:
            raise ShopError("item_not_found", "Este item não existe.")
        if not is_owned(item, user.owned_items):
            raise ShopError("not_owned", "Compre este item antes de usá-lo.")

        if item.kind == "avatar":
            if item.id not in AVATAR_IDS:
                # Catálogo e allowlist fora de sincronia é bug de programação,
                # não erro do usuário — melhor estourar claro do que gravar um
                # avatar que o modelo vai recusar na próxima leitura.
                raise ShopError("unknown_avatar", "Este avatar não está disponível.")
            fields = {"avatar": item.id}
        else:
            fields = {"accessory": item.id}

        updated = await self.users.update_fields(
            user.id, {**fields, "updated_at": utc_now()}
        )
        return updated or user.model_copy(update=fields)

    async def unequip_accessory(self, *, user: User) -> User:
        updated = await self.users.update_fields(
            user.id, {"accessory": None, "updated_at": utc_now()}
        )
        return updated or user.model_copy(update={"accessory": None})

    @staticmethod
    def _is_equipped(item: ShopItem, user: User) -> bool:
        if item.kind == "avatar":
            return user.avatar == item.id
        return user.accessory == item.id
