import datetime
from app.core.celery_app import celery_app
from app.core.database import supabase
from app.agents.digest_writer import write_digest

@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def morning_digest(self):
    """
    Cron task running daily. Aggregates workspace data for all users,
    generates morning digest text via CrewAI, and upserts it to digest_cache.
    """
    try:
        # 1. Fetch all users from the public database
        users_res = supabase.table("users").select("id, name").execute()
        users = users_res.data or []
        
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        five_days_ago_str = (datetime.date.today() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
        
        processed_count = 0
        
        for user in users:
            user_id = user["id"]
            user_name = user.get("name") or "Freelancer"
            
            try:
                # A. Count active projects
                active_projects = supabase.table("projects").select("id", count="exact").eq("user_id", user_id).eq("status", "active").execute()
                active_count = active_projects.count or 0

                # B. Query milestones due today
                due_today = supabase.table("milestones").select("title").eq("user_id", user_id).eq("status", "pending").eq("due_date", today_str).execute()
                due_today_list = [m["title"] for m in due_today.data] if due_today.data else []

                # C. Query overdue milestones
                overdue_mils = supabase.table("milestones").select("title, due_date").eq("user_id", user_id).eq("status", "pending").lt("due_date", today_str).execute()
                overdue_mil_list = [f"{m['title']} (due {m['due_date']})" for m in overdue_mils.data] if overdue_mils.data else []

                # D. Query overdue invoices
                overdue_invs = supabase.table("invoices").select("client_name, project_title, total_inr, due_date").eq("user_id", user_id).in_("payment_status", ["sent", "overdue"]).lt("due_date", today_str).execute()
                overdue_invoice_list = []
                if overdue_invs.data:
                    for inv in overdue_invs.data:
                        try:
                            due_date = datetime.datetime.strptime(inv["due_date"], "%Y-%m-%d").date()
                            days_over = (datetime.date.today() - due_date).days
                        except Exception:
                            days_over = 1
                        
                        overdue_invoice_list.append({
                            "client_name": inv.get("client_name") or "Client",
                            "project_title": inv.get("project_title") or "Project",
                            "total_inr": int(float(inv.get("total_inr") or 0)),
                            "days_overdue": days_over
                        })

                # E. Count pending proposals
                pending_props = supabase.table("projects").select("id", count="exact").eq("user_id", user_id).eq("status", "scoping").execute()
                pending_props_count = pending_props.count or 0

                # F. Find inactive projects (updated_at older than 5 days)
                inactive_projects = supabase.table("projects").select("title").eq("user_id", user_id).eq("status", "active").lt("updated_at", five_days_ago_str).execute()
                inactive_list = [p["title"] for p in inactive_projects.data] if inactive_projects.data else []

                # G. Run digest-writer agent
                digest_output = write_digest(
                    user_name=user_name,
                    active_projects_count=active_count,
                    milestones_due_today=due_today_list,
                    overdue_milestones=overdue_mil_list,
                    overdue_invoices=overdue_invoice_list,
                    pending_proposals_count=pending_props_count,
                    inactive_projects=inactive_list
                )

                # H. Upsert cache record
                supabase.table("digest_cache").upsert({
                    "user_id": user_id,
                    "content": digest_output.digest_text
                }).execute()
                
                processed_count += 1
                
            except Exception as user_err:
                # Continue processing other users if one fails
                print(f"Failed to generate morning digest for user {user_id}: {str(user_err)}")

        return {
            "status": "success",
            "processed_count": processed_count
        }

    except Exception as exc:
        print(f"Failed executing morning digest task: {str(exc)}")
        raise self.retry(exc=exc)
