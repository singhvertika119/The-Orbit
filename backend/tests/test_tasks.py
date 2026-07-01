from unittest.mock import patch, MagicMock
from app.tasks.invoices import invoice_on_milestone_complete
from app.tasks.followups import daily_overdue_check
from app.tasks.digest import morning_digest
from app.agents.invoice_generator import InvoiceGeneratorOutput
from app.agents.followup_writer import FollowupWriterOutput
from app.agents.digest_writer import DigestWriterOutput

@patch("app.tasks.invoices.supabase")
@patch("app.tasks.invoices.generate_invoice")
def test_invoice_on_milestone_complete_task(mock_generate, mock_db):
    """
    Tests the milestone-complete automatic billing process.
    Aggregates project details, runs invoice generation, saves records,
    and updates milestone mappings.
    """
    mock_milestone = {"id": "mil-1", "project_id": "proj-1", "amount_inr": 20000, "title": "Milestone A"}
    mock_project = {"id": "proj-1", "client_id": "client-1", "title": "Project A"}
    mock_client = {"id": "client-1", "name": "Client A", "email": "client@example.com"}
    mock_user = {"id": "user-1", "name": "Freelancer", "upi_id": "free@upi", "bank_details": "Bank info"}
    
    # Configure DB queries sequence
    mock_db.table().select().eq().eq().execute.side_effect = [
        MagicMock(data=[mock_milestone]),
        MagicMock(data=[mock_project]),
        MagicMock(data=[mock_client])
    ]
    mock_db.table().select().eq().execute.return_value = MagicMock(data=[mock_user])
    
    # Mock billing agent
    mock_generate.return_value = InvoiceGeneratorOutput(
        invoice_number="GIG-2026-FL-001",
        gst_amount=3600,
        total_amount=23600,
        due_date="2026-07-08",
        invoice_text="Invoice details..."
    )
    
    # Mock DB write operations
    mock_db.table().insert().execute.return_value = MagicMock(data=[{"id": "inv-1", "invoice_number": "GIG-2026-FL-001"}])
    mock_db.table().update().eq().eq().execute.return_value = MagicMock(data=[{}])
    
    # Execute task synchronously
    res = invoice_on_milestone_complete.run(milestone_id="mil-1", user_id="user-1")
    
    assert res["status"] == "success"
    assert res["invoice_id"] == "inv-1"
    assert res["invoice_number"] == "GIG-2026-FL-001"

@patch("app.tasks.followups.supabase")
@patch("app.tasks.followups.write_followup")
def test_daily_overdue_check_task(mock_write, mock_db):
    """
    Tests the overdue invoices checker. Queries overdue items,
    runs followup agents, and saves drafts.
    """
    mock_invoice = {
        "id": "inv-1",
        "client_name": "Client A",
        "project_title": "Project A",
        "milestone_title": "Milestone A",
        "total_inr": 23600,
        "due_date": "2026-06-25",
        "followup_drafts": []
    }
    
    # Mock retrieve overdue invoices
    mock_db.table().select().in_().lt().execute.return_value = MagicMock(data=[mock_invoice])
    
    # Mock followup drafter agent
    mock_write.return_value = FollowupWriterOutput(
        subject_line="Overdue Payment Reminder",
        message_body="Hi, your payment is overdue."
    )
    
    mock_db.table().update().eq().execute.return_value = MagicMock(data=[{}])
    
    # Execute task synchronously
    res = daily_overdue_check.run()
    
    assert res["status"] == "success"
    assert res["processed_count"] == 1

@patch("app.tasks.digest.supabase")
@patch("app.tasks.digest.write_digest")
def test_morning_digest_task(mock_write, mock_db):
    """
    Tests daily workspace briefing builder. For each user,
    aggregates stats, runs digest-writer, and stores inside digest_cache.
    """
    # Mock users query
    mock_db.table().select().execute.return_value = MagicMock(data=[{"id": "user-1", "name": "Freelancer"}])
    
    # Mock sequence of db aggregate queries in the user iteration loop
    mock_db.table().select().eq().execute.side_effect = [
        MagicMock(count=2), # Active projects
        MagicMock(data=[]), # Milestones due today
        MagicMock(data=[]), # Overdue milestones
        MagicMock(data=[]), # Overdue invoices
        MagicMock(count=1), # Pending proposals
        MagicMock(data=[]), # Inactive projects
        MagicMock(data=[])  # Cache upsert stub
    ]
    
    mock_write.return_value = DigestWriterOutput(
        digest_text="Hi Freelancer, here is your daily summary."
    )
    
    # Execute task synchronously
    res = morning_digest.run()
    
    assert res["status"] == "success"
    assert res["processed_count"] == 1
