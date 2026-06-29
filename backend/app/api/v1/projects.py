from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/")
def get_projects():
    return {"message": "projects endpoint placeholder"}
