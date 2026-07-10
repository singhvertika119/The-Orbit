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
        # Validate token against Supabase Auth (with retries for transient keep-alive/disconnect issues)
        user_response = None
        last_err = None
        import time
        for attempt in range(3):
            try:
                user_response = supabase.auth.get_user(token)
                if user_response and user_response.user:
                    break
            except Exception as ex:
                last_err = ex
                time.sleep(0.1)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired access token. Details: {str(last_err) if last_err else 'None'}",
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
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
