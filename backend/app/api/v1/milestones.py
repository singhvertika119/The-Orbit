from fastapi import APIRouter

router = APIRouter(prefix="/milestones", tags=["milestones"])

@router.get("/")
def get_milestones():
    return {"message": "milestones endpoint placeholder"}
