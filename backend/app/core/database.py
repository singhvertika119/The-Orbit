from supabase import create_client, Client
from app.core.config import settings

# Initialize Supabase client
# We use the SERVICE_KEY for database queries, and we will manually enforce
# user-tenant isolation (user_id filtering) in our application logic.
if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in the environment.")

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
