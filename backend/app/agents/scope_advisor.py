from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew
from app.agents.llm import llm_versatile

class ScopeAdvisorOutput(BaseModel):
    scope_breakdown: List[str] = Field(..., description="Step-by-step phases or task lists to execute the project deliverables")
    timeline_days: int = Field(..., description="Total estimated time required to complete the project in calendar days")
    price_inr: int = Field(..., description="Suggested project pricing in Indian Rupees (INR)")
    price_rationale: str = Field(..., description="Explanation of why this price and timeline estimation are suggested")
    risk_flags: List[str] = Field(..., description="Risk factors, potential delays, or dependencies (e.g. third-party APIs)")

def advise_scope(
    brief_summary: str,
    deliverables: List[str],
    project_type: str,
    past_projects_context: str = "No past projects available."
) -> ScopeAdvisorOutput:
    """
    Analyzes project deliverables and type to estimate scope, timeline, pricing, and risks using CrewAI.
    """
    # 1. Define Advisor Agent
    advisor_agent = Agent(
        role="Freelance Scope & Pricing Consultant",
        goal="Structure project scopes, estimate deadlines, and suggest competitive market pricing in INR",
        backstory=(
            "You are an experienced Indian IT consultant and freelance strategist. You have managed and priced "
            "hundreds of software projects. You know how to break down deliverables into clear milestones, "
            "estimate duration realistically, and price projects according to complexity and market standards.\n\n"
            "Indian market standards for pricing guidance:\n"
            "- Landing Page / Static Site: 8,000 - 15,000 INR\n"
            "- Web Platform with CMS: 20,000 - 45,000 INR\n"
            "- Full-stack Web App (Auth + DB): 40,000 - 90,000 INR\n"
            "- Mobile Application: 60,000 - 1,50,000 INR"
        ),
        llm=llm_versatile,
        verbose=False
    )

    # 2. Define Scoping Task
    deliverables_str = ", ".join(deliverables) if deliverables else "None specified"
    
    advisor_task = Task(
        description=(
            f"Generate a scope breakdown, timeline, and pricing recommendation for the following project request:\n\n"
            f"Project Type: {project_type}\n"
            f"Deliverables: {deliverables_str}\n"
            f"Brief Summary: {brief_summary}\n\n"
            f"Freelancer's Past Project Experience (calibrated reference data):\n"
            f"---\n"
            f"{past_projects_context}\n"
            f"---\n\n"
            f"Determine:\n"
            f"1. A tasks breakdown matching the deliverables.\n"
            f"2. Timeline in calendar days.\n"
            f"3. suggested price in INR (use the history or default benchmarks above).\n"
            f"4. A rationale explaining this price and duration breakdown.\n"
            f"5. Risks or scope boundaries to prevent scope creep."
        ),
        expected_output="A structured JSON object matching the ScopeAdvisorOutput schema.",
        agent=advisor_agent,
        output_pydantic=ScopeAdvisorOutput
    )

    # 3. Execution in Crew
    crew = Crew(
        agents=[advisor_agent],
        tasks=[advisor_task],
        verbose=False
    )

    result = crew.kickoff()
    return result.pydantic
