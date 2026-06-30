from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import supabase
from app.core.security import get_current_user
from app.models.client import ClientCreate, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])

@router.get("/")
async def list_clients(current_user: dict = Depends(get_current_user)):
    """
    Lists all clients belonging to the authenticated user.
    """
    user_id = current_user["id"]
    try:
        res = supabase.table("clients").select("*").eq("user_id", user_id).order("name", desc=False).execute()
        return res.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Registers a new client under the user's workspace.
    """
    user_id = current_user["id"]
    payload = client_data.model_dump()
    payload["user_id"] = user_id
    try:
        res = supabase.table("clients").insert(payload).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to insert client record into database."
            )
        return res.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create client: {str(e)}"
        )

@router.get("/{client_id}")
async def get_client(
    client_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetches a single client by ID. Verifies tenant ownership.
    """
    user_id = current_user["id"]
    try:
        res = supabase.table("clients").select("*").eq("id", client_id).eq("user_id", user_id).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        return res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

@router.patch("/{client_id}")
async def update_client(
    client_id: str,
    client_data: ClientUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Updates client details. Verifies client belongs to the user.
    """
    user_id = current_user["id"]
    update_payload = {k: v for k, v in client_data.model_dump().items() if v is not None}
    
    try:
        # Verify ownership first
        check = supabase.table("clients").select("id").eq("id", client_id).eq("user_id", user_id).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        res = supabase.table("clients").update(update_payload).eq("id", client_id).eq("user_id", user_id).execute()
        return res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update client: {str(e)}"
        )

@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Deletes a client. Verifies ownership.
    """
    user_id = current_user["id"]
    try:
        # Verify ownership
        check = supabase.table("clients").select("id").eq("id", client_id).eq("user_id", user_id).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        supabase.table("clients").delete().eq("id", client_id).eq("user_id", user_id).execute()
        return {"status": "success", "message": "Client deleted"}
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete client: {str(e)}"
        )
