from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.database import supabase

# HTTPBearer security scheme
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    FastAPI dependency to authenticate the user using the Supabase JWT.
    Validates the token against Supabase Auth and fetches the user's profile
    from the public.users database.
    """
    token = credentials.credentials
    try:
        # Validate token against Supabase Auth (synchronous call)
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
            )
        
        user_id = user_response.user.id
        email = user_response.user.email

        # Fetch the user profile from public.users
        res = supabase.table("users").select("*").eq("id", user_id).execute()
        if not res.data:
            # Fallback: if the database row does not exist, insert it now.
            # This ensures robustness even if the Supabase auth trigger fails to run.
            insert_res = supabase.table("users").insert({
                "id": user_id,
                "email": email
            }).execute()
            if not insert_res.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user profile in public database"
                )
            user_profile = insert_res.data[0]
        else:
            user_profile = res.data[0]
            
        return user_profile

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
