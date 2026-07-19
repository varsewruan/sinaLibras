"""/shop/* — catálogo, compra e equipamento de itens."""

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.deps import get_current_user, get_shop_service
from app.models.shop import PurchaseRequest, ShopView
from app.models.user import User, UserPublic
from app.services.shop_service import ShopError, ShopService

router = APIRouter(prefix="/shop", tags=["shop"])

# Erro de domínio → status HTTP. Igual ao mapa em routers/auth.py.
_STATUS = {
    "item_not_found": status.HTTP_404_NOT_FOUND,
    "already_owned": status.HTTP_409_CONFLICT,
    "insufficient_xp": status.HTTP_402_PAYMENT_REQUIRED,
    "not_owned": status.HTTP_403_FORBIDDEN,
    "unknown_avatar": status.HTTP_422_UNPROCESSABLE_ENTITY,
}


def _http(error: ShopError) -> HTTPException:
    return HTTPException(
        status_code=_STATUS.get(error.code, status.HTTP_400_BAD_REQUEST),
        detail={"code": error.code, "message": error.message},
    )


@router.get("/items", response_model=ShopView, summary="Catálogo com o estado do usuário")
async def list_items(
    user: User = Depends(get_current_user),
    service: ShopService = Depends(get_shop_service),
) -> ShopView:
    return service.catalog_for(user)


@router.post("/purchase", response_model=UserPublic, summary="Comprar um item com XP")
async def purchase(
    payload: PurchaseRequest = Body(...),
    user: User = Depends(get_current_user),
    service: ShopService = Depends(get_shop_service),
) -> UserPublic:
    try:
        updated, _item = await service.purchase(user=user, item_id=payload.item_id)
    except ShopError as error:
        raise _http(error) from error
    return UserPublic.from_user(updated)


@router.post("/equip", response_model=UserPublic, summary="Vestir um item já comprado")
async def equip(
    payload: PurchaseRequest = Body(...),
    user: User = Depends(get_current_user),
    service: ShopService = Depends(get_shop_service),
) -> UserPublic:
    try:
        updated = await service.equip(user=user, item_id=payload.item_id)
    except ShopError as error:
        raise _http(error) from error
    return UserPublic.from_user(updated)


@router.post("/unequip", response_model=UserPublic, summary="Tirar o acessório")
async def unequip(
    user: User = Depends(get_current_user),
    service: ShopService = Depends(get_shop_service),
) -> UserPublic:
    return UserPublic.from_user(await service.unequip_accessory(user=user))
