from typing import List
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from crewai import Agent, Task, Crew
from app.agents.llm import llm_versatile

class ProposalDrafterOutput(BaseModel):
    subject_line: str = Field(..., description="Subject line for the proposal email or message (e.g. Project Proposal — Dashboard...)")
    proposal_text: str = Field(..., description="The complete text body of the proposal following the structured format rules.")

def draft_proposal(
    project_title: str,
    client_name: str,
    scope_breakdown: List[str],
    timeline_days: int,
    price_inr: int,
    deliverables: List[str],
    user_name: str,
    user_upi: str = ""
) -> ProposalDrafterOutput:
    """
    Drafts a client-ready proposal with subject line using the proposal-drafter CrewAI agent.
    """
    # 1. Define Proposal Agent
    drafter_agent = Agent(
        role="Senior Freelance Proposal Writer",
        goal="Draft compelling, persuasive, and professional proposals that win clients",
        backstory=(
            "You are a master freelance proposals writer and client relationship strategist. "
            "You specialize in writing clear proposals that frame the client's problem, outline a robust approach, "
            "provide solid milestone deliverables, and make pricing transparent. Your style is professional, "
            "concise, confident, and warm. You structure document details to be clear and readable."
        ),
        llm=llm_versatile,
        verbose=False
    )

    # 2. Format details
    deliverables_list = "\n".join([f"- {d}" for d in deliverables]) if deliverables else "- Software development deliverables"
    scope_list = "\n".join([f"- {s}" for s in scope_breakdown]) if scope_breakdown else "- Project execution phases"
    
    # Calculate 18% GST and total values for prompt guidance
    base_price = float(price_inr)
    gst_amount = int(base_price * 0.18)
    total_price = int(base_price + gst_amount)

    upi_signature = f"\nUPI ID for transfers: {user_upi}" if user_upi else ""

    # 3. Create Proposal Task
    drafter_task = Task(
        description=(
            f"Draft a formal freelance proposal using these parameters:\n\n"
            f"Freelancer Name: {user_name}\n"
            f"Client Name: {client_name}\n"
            f"Project Title: {project_title}\n\n"
            f"Deliverables:\n{deliverables_list}\n\n"
            f"Scope tasks breakdown:\n{scope_list}\n\n"
            f"Timeline: {timeline_days} calendar days\n"
            f"Base pricing investment: {int(base_price):,} INR (excluding GST)\n"
            f"Calculated 18% GST: {gst_amount:,} INR\n"
            f"Total pricing investment (inclusive of 18% GST): {total_price:,} INR\n\n"
            f"Proposal Text MUST strictly follow this structure:\n"
            f"1. Problem Restatement: 2-3 sentences demonstrating a clear understanding of the client's goals.\n"
            f"2. Approach: 3-4 sentences outlining how you will deliver the solution.\n"
            f"3. Deliverables: A clean bulleted list matching the requirements.\n"
            f"4. Timeline: A clear calendar days timeline estimate statement.\n"
            f"5. Investment: Explicitly break down Base Price, 18% GST, and Total Price in INR.\n"
            f"6. Payment Terms: Structure as 40% upfront deposit, 30% on mid-milestone, and 30% upon final completion.\n"
            f"7. Next Steps: A clear and friendly call to action.\n"
            f"8. Signature: Conclude with your name ({user_name}){upi_signature}."
        ),
        expected_output="A structured JSON object with subject_line and proposal_text.",
        agent=drafter_agent,
        output_pydantic=ProposalDrafterOutput
    )

    # 4. Execute Crew
    crew = Crew(
        agents=[drafter_agent],
        tasks=[drafter_task],
        verbose=False,
        cache=False
    )

    result = crew.kickoff()
    return result.pydantic
