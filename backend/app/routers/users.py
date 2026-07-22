"""/users/* endpoints — profile fields owned by the user."""

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.deps import get_current_user, get_user_service
from app.models.user import UpdateAvatarRequest, User, UserPublic
from app.services.shop_service import ShopError
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.patch(
    "/me",
    response_model=UserPublic,
    summary="Update the current user's avatar",
)
async def update_me(
    payload: UpdateAvatarRequest = Body(...),
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserPublic:
    # An unknown preset id is rejected by the DTO validator as a 422 before we
    # get here. A *known* but unpurchased one is a domain error — see
    # UserService.update_avatar.
    try:
        updated = await service.update_avatar(user=user, avatar=payload.avatar)
    except ShopError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": error.code, "message": error.message},
        ) from error
    return UserPublic.from_user(updated)
