from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
)


@router.get("/{user}")
def get_admin(user: str):
    r = f"Hello {user}!"
    return r
