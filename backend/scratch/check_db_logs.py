import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(dotenv_path='backend/.env')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

print(f"SUPABASE_URL: {supabase_url}")

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL or SUPABASE_SERVICE_KEY is missing from .env")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print("\n--- FETCHING RECENT USERS IN public.users ---")
try:
    res_users = supabase.from_('users').select('*').order('created_at', desc=True).limit(5).execute()
    print(res_users.data)
except Exception as e:
    print(f"Failed to fetch users: {e}")

print("\n--- FETCHING RECENT ERRORS IN public.error_logs ---")
try:
    res_errors = supabase.from_('error_logs').select('*').order('created_at', desc=True).limit(5).execute()
    print(res_errors.data)
except Exception as e:
    print(f"Failed to fetch error logs: {e}")
