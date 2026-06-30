import datetime
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from crewai import Agent, Task, Crew
from app.agents.llm import llm_instant
from app.core.database import supabase

class InvoiceGeneratorOutput(BaseModel):
    invoice_number: str = Field(..., description="The unique invoice number in GIG-YYYY-INIT-NNN format")
    gst_amount: int = Field(..., description="The calculated 18% GST amount in INR")
    total_amount: int = Field(..., description="The total amount in INR (base amount + GST)")
    due_date: str = Field(..., description="The invoice due date in YYYY-MM-DD format")
    invoice_text: str = Field(..., description="A clean, structured plain text invoice layout ready to present to the client")

def get_user_short_id(name: str) -> str:
    """
    Derives initials from a user's name. E.g., 'Vertika Singh' -> 'VS'
    """
    if not name:
        return "XX"
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name.strip()[:2].upper()

def fetch_invoice_number(user_name: str) -> str:
    """
    Queries the database sequence function via RPC to generate the invoice number.
    """
    user_short_id = get_user_short_id(user_name)
    try:
        res = supabase.rpc("generate_invoice_number", {"user_short_id": user_short_id}).execute()
        if res.data:
            return res.data
    except Exception as e:
        print(f"Failed to generate invoice number via database RPC: {str(e)}")
    
    # Fallback to local generation if database function fails
    import random
    year = datetime.datetime.now().year
    rand_seq = random.randint(100, 999)
    return f"GIG-{year}-{user_short_id}-{rand_seq}"

def generate_invoice(
    client_name: str,
    client_email: str,
    project_title: str,
    milestone_title: str,
    amount_inr: int,
    due_days: int,
    user_name: str,
    user_upi: str,
    user_bank_details: str = ""
) -> InvoiceGeneratorOutput:
    """
    Generates a structured GST invoice matching the milestone details using CrewAI.
    Calculations are done in Python and overridden in the output to guarantee 100% accuracy.
    """
    # 1. Pre-calculate values to ensure 100% mathematical precision
    invoice_num = fetch_invoice_number(user_name)
    
    base_price = float(amount_inr)
    gst_val = int(base_price * 0.18)
    total_val = int(base_price + gst_val)
    
    today = datetime.date.today()
    due_dt = today + datetime.timedelta(days=due_days)
    due_date_str = due_dt.strftime("%Y-%m-%d")
    issued_date_str = today.strftime("%Y-%m-%d")

    # 2. Define Generator Agent
    generator_agent = Agent(
        role="Freelance Billing Specialist",
        goal="Format complete, professional, and compliant invoice detail sheets",
        backstory=(
            "You are a meticulous billing specialist who drafts invoices for Indian freelancers. "
            "You format layout details cleanly and ensure every required invoice field (addresses, "
            "bank details, item breakdowns, and totals) is structured and easy to read."
        ),
        llm=llm_instant,
        verbose=False
    )

    # 3. Create Task
    generator_task = Task(
        description=(
            f"Generate a professional structured invoice utilizing these inputs:\n\n"
            f"Invoice Number: {invoice_num}\n"
            f"Issued Date: {issued_date_str}\n"
            f"Due Date: {due_date_str}\n"
            f"Freelancer Name (Sender): {user_name}\n"
            f"UPI ID: {user_upi}\n"
            f"Bank Details: {user_bank_details or 'None'}\n"
            f"Client Name: {client_name}\n"
            f"Client Email: {client_email}\n"
            f"Project Title: {project_title}\n"
            f"Billed Item (Milestone): {milestone_title}\n\n"
            f"Calculated Amounts (DO NOT CHANGE):\n"
            f"- Subtotal (Base Amount): {int(base_price):,} INR\n"
            f"- 18% GST: {gst_val:,} INR\n"
            f"- Grand Total: {total_val:,} INR\n\n"
            f"Your output MUST format this details into a clean plain text invoice layout. "
            f"It must clearly present: Header info, Sender details, Recipient details, item tables, "
            f"subtotal/GST/total breakdowns, and payment directions (UPI/Bank details)."
        ),
        expected_output="A structured JSON object matching the InvoiceGeneratorOutput schema.",
        agent=generator_agent,
        output_pydantic=InvoiceGeneratorOutput
    )

    # 4. Execute Crew
    crew = Crew(
        agents=[generator_agent],
        tasks=[generator_task],
        verbose=False
    )

    result = crew.kickoff()
    
    # Overwrite LLM fields with python calculations to protect against LLM arithmetic hallucination
    pydantic_res = result.pydantic
    pydantic_res.invoice_number = invoice_num
    pydantic_res.gst_amount = gst_val
    pydantic_res.total_amount = total_val
    pydantic_res.due_date = due_date_str
    
    return pydantic_res
