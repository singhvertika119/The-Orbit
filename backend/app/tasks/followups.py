import datetime
from app.core.celery_app import celery_app
from app.core.database import supabase
from app.agents.followup_writer import write_followup

@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def daily_overdue_check(self):
    """
    Cron task running daily. Finds all unpaid invoices past their due dates,
    generates tone-calibrated reminder drafts, and writes them to followup_drafts.
    """
    try:
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        
        # 1. Fetch all invoices with 'sent' or 'overdue' status past their due date
        overdue_res = supabase.table("invoices")\
            .select("*")\
            .in_("payment_status", ["sent", "overdue"])\
            .lt("due_date", today_str)\
            .execute()
            
        overdue_invoices = overdue_res.data or []
        processed_count = 0
        
        for invoice in overdue_invoices:
            invoice_id = invoice["id"]
            due_date_str = invoice["due_date"]
            
            # Calculate overdue duration
            try:
                due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
                days_overdue = (datetime.date.today() - due_date).days
            except Exception:
                days_overdue = 1

            # 2. Invoke followup_writer agent
            followup_result = write_followup(
                client_name=invoice.get("client_name") or "Client",
                project_title=invoice.get("project_title") or "Project",
                total_amount=int(float(invoice.get("total_inr") or 0)),
                days_overdue=days_overdue,
                milestone_title=invoice.get("milestone_title") or "Milestone"
            )

            # 3. Create follow-up draft item
            new_draft = {
                "subject_line": followup_result.subject_line,
                "message_body": followup_result.message_body,
                "days_overdue": days_overdue,
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

            # 4. Read existing drafts and append new item
            existing_drafts = invoice.get("followup_drafts")
            if not isinstance(existing_drafts, list):
                existing_drafts = []
            
            existing_drafts.append(new_draft)

            # 5. Update invoice record (transition payment_status to 'overdue')
            supabase.table("invoices").update({
                "payment_status": "overdue",
                "followup_drafts": existing_drafts
            }).eq("id", invoice_id).execute()
            
            processed_count += 1

        return {
            "status": "success",
            "processed_count": processed_count
        }

    except Exception as exc:
        print(f"Error executing daily overdue check task: {str(exc)}")
        raise self.retry(exc=exc)
