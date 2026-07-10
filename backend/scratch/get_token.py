import os
import sys
import random
from pathlib import Path
from dotenv import load_dotenv

# Resolve the .env path
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# pyrefly: ignore [missing-import]
from supabase import create_client

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in your .env file.")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

# Generate a randomized test user email to completely bypass email conflicts/locks
rand_num = random.randint(1000, 9999)
test_email = f"testuser_{rand_num}@gig.ai"
test_password = "password123"

def get_test_token():
    print(f"Creating confirmed test user: {test_email}...")
    try:
        # 1. Register test user via Admin API (bypasses email confirmation)
        signup_response = supabase.auth.admin.create_user({
            "email": test_email,
            "password": test_password,
            "email_confirm": True
        })
        
        if signup_response.user:
            print("Test user successfully created! Logging in...")
            
            # 2. Log in to retrieve JWT session
            response = supabase.auth.sign_in_with_password({
                "email": test_email,
                "password": test_password
            })
            if response.session:
                print("\n================== JWT ACCESS TOKEN ==================")
                print(response.session.access_token)
                print("======================================================\n")
                print("Copy the token above, go to Swagger UI (http://127.0.0.1:8000/docs),")
                print("click the Authorize button in the top right, and paste it there.")
                return
    except Exception as e:
        print(f"Failed to generate test token: {str(e)}")

if __name__ == "__main__":
    get_test_token()
