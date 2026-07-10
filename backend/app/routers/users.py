"""/users/* endpoints — profile fields owned by the user."""

from fastapi import APIRouter, Body, Depends

from app.deps import get_current_user, get_user_service
from app.models.user import UpdateAvatarRequest, User, UserPublic
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
    # An unknown preset id is rejected by the DTO validator as a 422 before
    # we ever get here, so there's no domain error to translate.
    updated = await service.update_avatar(user=user, avatar=payload.avatar)
    return UserPublic.from_user(updated)
