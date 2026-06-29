from fastapi import APIRouter

router = APIRouter(prefix="/digest", tags=["digest"])

@router.get("/")
def get_digest():
    return {"message": "digest endpoint placeholder"}
