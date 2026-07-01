from app.core.celery_app import celery_app
from app.core.database import supabase
from app.agents.invoice_generator import generate_invoice

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def invoice_on_milestone_complete(self, milestone_id: str, user_id: str):
    """
    Background task triggered when a milestone status changes to 'complete'.
    Gathers billing context details, executes the invoice_generator agent,
    inserts the invoice record, and links it back to the milestone.
    """
    try:
        # 1. Fetch Milestone details
        milestone_res = supabase.table("milestones").select("*").eq("id", milestone_id).eq("user_id", user_id).execute()
        if not milestone_res.data:
            raise ValueError(f"Milestone {milestone_id} not found for user {user_id}")
        milestone = milestone_res.data[0]

        # 2. Fetch Project details
        project_res = supabase.table("projects").select("*").eq("id", milestone["project_id"]).eq("user_id", user_id).execute()
        if not project_res.data:
            raise ValueError(f"Associated project {milestone['project_id']} not found for user {user_id}")
        project = project_res.data[0]

        # 3. Fetch Client details
        client_name = "Client"
        client_email = ""
        if project.get("client_id"):
            client_res = supabase.table("clients").select("*").eq("id", project["client_id"]).eq("user_id", user_id).execute()
            if client_res.data:
                client = client_res.data[0]
                client_name = client.get("name") or "Client"
                client_email = client.get("email") or ""

        # 4. Fetch User profile (UPI, bank details)
        user_res = supabase.table("users").select("*").eq("id", user_id).execute()
        user_profile = user_res.data[0] if user_res.data else {}
        user_name = user_profile.get("name") or "Freelancer"
        user_upi = user_profile.get("upi_id") or ""
        user_bank_details = user_profile.get("bank_details") or ""

        # 5. Run invoice_generator agent
        invoice_output = generate_invoice(
            client_name=client_name,
            client_email=client_email,
            project_title=project.get("title") or "Project",
            milestone_title=milestone.get("title") or "Milestone",
            amount_inr=int(float(milestone.get("amount_inr") or 0)),
            due_days=7, # Default payment window of 7 days
            user_name=user_name,
            user_upi=user_upi,
            user_bank_details=user_bank_details
        )

        # 6. Insert new Invoice record (Default payment_status: 'sent')
        invoice_payload = {
            "user_id": user_id,
            "project_id": milestone["project_id"],
            "milestone_id": milestone_id,
            "invoice_number": invoice_output.invoice_number,
            "amount_inr": milestone["amount_inr"],
            "gst_amount": invoice_output.gst_amount,
            "total_inr": invoice_output.total_amount,
            "milestone_title": milestone["title"],
            "project_title": project["title"],
            "client_name": client_name,
            "client_email": client_email,
            "payment_status": "sent",
            "due_date": invoice_output.due_date,
            "invoice_text": invoice_output.invoice_text
        }

        invoice_insert = supabase.table("invoices").insert(invoice_payload).execute()
        if not invoice_insert.data:
            raise RuntimeError("Failed to insert invoice record.")
        new_invoice = invoice_insert.data[0]

        # 7. Link invoice back to milestone
        supabase.table("milestones").update({"invoice_id": new_invoice["id"]}).eq("id", milestone_id).eq("user_id", user_id).execute()

        return {
            "status": "success",
            "invoice_id": new_invoice["id"],
            "invoice_number": new_invoice["invoice_number"]
        }

    except Exception as exc:
        print(f"Error generating invoice for milestone {milestone_id}: {str(exc)}")
        # Trigger Celery retry mechanism
        raise self.retry(exc=exc)
