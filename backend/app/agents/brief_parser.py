from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew
from app.agents.llm import llm_versatile

class BriefParserOutput(BaseModel):
    project_type: str = Field(..., description="Project type (e.g. Web Development, Mobile App, UI/UX Design)")
    deliverables: List[str] = Field(..., description="List of deliverables explicitly mentioned in the brief")
    timeline_signals: str = Field(..., description="Timeline constraints or date mentions explicitly stated")
    budget_signals: str = Field(..., description="Budget hints, constraints, or values explicitly stated")
    ambiguities: List[str] = Field(..., description="Areas lacking clarity or detail (e.g. tech stack, integrations, hosting, scope boundaries)")
    clarifying_questions: List[str] = Field(..., description="Specific questions to ask the client to resolve the ambiguities")

def parse_brief(brief_text: str) -> BriefParserOutput:
    """
    Parses unstructured brief text and extracts a structured JSON model using CrewAI.
    """
    # 1. Define Parser Agent
    parser_agent = Agent(
        role="Senior Client Brief Parser",
        goal="Extract key structured project requirements from messy, unstructured client briefs",
        backstory=(
            "You are a senior freelance solutions architect. You excel at reading raw, informal client "
            "briefs (like chats, emails, notes) and formatting them into neat project specs. "
            "You extract ONLY what is explicitly stated. You never invent details, make assumptions, "
            "or fill in blanks. If details are missing, you flag them as ambiguities and raise clarifying questions."
        ),
        llm=llm_versatile,
        verbose=False
    )

    # 2. Define Parser Task
    parser_task = Task(
        description=(
            f"Thoroughly analyze this raw client brief:\n"
            f"---\n"
            f"{brief_text}\n"
            f"---\n"
            f"Extract the project type, deliverables, timeline constraints, and budget indicators. "
            f"Identify any ambiguities (missing information like framework preference, deployment, "
            f"or scaling needs) and compile a list of precise questions to clarify them with the client."
        ),
        expected_output="A structured JSON object matching the BriefParserOutput schema.",
        agent=parser_agent,
        output_pydantic=BriefParserOutput
    )

    # 3. Chaining sequential execution in Crew
    crew = Crew(
        agents=[parser_agent],
        tasks=[parser_task],
        verbose=False,
        cache=False
    )

    result = crew.kickoff()
    return result.pydantic
