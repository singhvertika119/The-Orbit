from typing import List, Dict
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from crewai import Agent, Task, Crew
from app.agents.llm import llm_versatile

class DigestWriterOutput(BaseModel):
    digest_text: str = Field(..., description="The formatted plain text morning digest briefing. No markdown, no ##, no *.")

def write_digest(
    user_name: str,
    active_projects_count: int,
    milestones_due_today: List[str],
    overdue_milestones: List[str],
    overdue_invoices: List[Dict],
    pending_proposals_count: int,
    inactive_projects: List[str]
) -> DigestWriterOutput:
    """
    Generates a daily morning digest summary based on aggregated metrics.
    Uses llama-3.3-70b-versatile.
    """
    # 1. Define Digest Agent
    digest_agent = Agent(
        role="Freelance Operations Coach who writes in 100% plain text",
        goal="Produce motivational, highly actionable morning briefings in 100% plain text, without any markdown formatting",
        backstory=(
            "You are a workspace assistant designed to help freelancers run their business. "
            "You parse milestones, invoices, and proposals, and generate brief, actionable daily digests. "
            "You highlight immediate actions (like due items or payment reminders) and write in a concise, "
            "clear, plain text tone. You NEVER use markdown formatting like hashes (##), asterisks (*), or bold markers (**). "
            "You use simple newlines and CAPITALIZED SECTION HEADERS for formatting instead."
        ),
        llm=llm_versatile,
        verbose=False
    )

    # 2. Format inputs into string indicators
    due_today_list = "\n".join([f"- {m}" for m in milestones_due_today]) if milestones_due_today else "None due today."
    overdue_mil_list = "\n".join([f"- {m}" for m in overdue_milestones]) if overdue_milestones else "None overdue."
    inactive_proj_list = "\n".join([f"- {p}" for p in inactive_projects]) if inactive_projects else "No inactive projects."
    
    invoices_list = []
    if overdue_invoices:
        for inv in overdue_invoices:
            invoices_list.append(
                f"- Client: {inv.get('client_name')}, Project: {inv.get('project_title')}, "
                f"Amount: {inv.get('total_inr'):,} INR, Overdue: {inv.get('days_overdue')} days"
            )
        invoices_str = "\n".join(invoices_list)
    else:
        invoices_str = "No overdue invoices."

    # 3. Create Task
    digest_task = Task(
        description=(
            f"Write a morning digest for the freelancer with these parameters:\n\n"
            f"Freelancer Name: {user_name}\n"
            f"Active Projects: {active_projects_count}\n"
            f"Pending Proposals: {pending_proposals_count}\n\n"
            f"Milestones Due Today:\n{due_today_list}\n\n"
            f"Overdue Milestones:\n{overdue_mil_list}\n\n"
            f"Overdue Invoices:\n{invoices_str}\n\n"
            f"Projects with no milestone updates in 5+ days:\n{inactive_proj_list}\n\n"
            f"Guidelines:\n"
            f"1. Start with a direct, warm greeting (e.g., 'Good morning, Vertika. Here is your briefing...').\n"
            f"2. Summarize immediate work due today or overdue.\n"
            f"3. Call out high-priority overdue payments and recommend follow-ups.\n"
            f"4. Return plain text only. No markdown formatting, no ##, no *, no **. Use newlines and capitalized headings for separation.\n"
            f"5. Keep it concise, motivational, and business-focused."
        ),
        expected_output="A plain text morning briefing summarizing operations status and action items.",
        agent=digest_agent
    )

    # 4. Execute Crew
    crew = Crew(
        agents=[digest_agent],
        tasks=[digest_task],
        verbose=False,
        cache=False
    )

    result = crew.kickoff()
    raw_text = result.raw
    
    # Programmatically clean any accidental markdown artifacts before caching/returning
    try:
        import re
        # Remove all hash symbols and any formatting stars/italics/backticks
        clean_text = re.sub(r'#+\s*', '', raw_text)
        clean_text = clean_text.replace('**', '').replace('* ', '• ').replace('*', '').replace('`', '').replace('_', '')
        clean_text = clean_text.strip()
    except Exception as e:
        print(f"Failed to post-process digest markdown: {str(e)}")
        clean_text = raw_text

    return DigestWriterOutput(digest_text=clean_text)
