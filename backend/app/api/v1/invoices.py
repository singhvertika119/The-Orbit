from fastapi import APIRouter

router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.get("/")
def get_invoices():
    return {"message": "invoices endpoint placeholder"}
