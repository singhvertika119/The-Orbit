from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew
from app.agents.llm import llm_instant

class FollowupWriterOutput(BaseModel):
    subject_line: str = Field(..., description="Subject line for the follow-up reminder email/message")
    message_body: str = Field(..., description="Body text for the follow-up reminder email/message")

def write_followup(
    client_name: str,
    project_title: str,
    total_amount: int,
    days_overdue: int,
    milestone_title: str
) -> FollowupWriterOutput:
    """
    Drafts a payment reminder with a tone calibrated to how many days the invoice is overdue.
    Uses llama-3.1-8b-instant.
    """
    # 1. Calibrate tone based on days overdue
    if days_overdue <= 7:
        tone_guidelines = (
            "Tone: Warm, friendly, and understanding. Assume the payment simply slipped through "
            "their inbox. Keep it polite, brief, and do not mention halting work or using firm language."
        )
    elif days_overdue <= 14:
        tone_guidelines = (
            "Tone: Direct, professional, and clear. State clearly that the invoice is now overdue. "
            "Mention the exact amount and days overdue. Politely request a status update on when "
            "the transfer will be processed."
        )
    else:
        tone_guidelines = (
            "Tone: Firm, formal, and serious. Emphasize that the payment is significantly overdue. "
            "Politely but firmly state that further milestone work on the project may have to be paused "
            "until the outstanding invoice is cleared."
        )

    # 2. Define Follow-up Writer Agent
    writer_agent = Agent(
        role="Freelance Communications Manager",
        goal="Draft calibrated payment follow-ups that secure payments while maintaining client relations",
        backstory=(
            "You are a professional business assistant for freelancers. You draft messages "
            "that help freelancers collect due payments. You follow strict communication rules: "
            "escalating tone proportionally to the days overdue without ever sounding hostile or rude."
        ),
        llm=llm_instant,
        verbose=False
    )

    # 3. Create Task
    writer_task = Task(
        description=(
            f"Draft a payment reminder message using these details:\n\n"
            f"Client Name: {client_name}\n"
            f"Project Title: {project_title}\n"
            f"Milestone: {milestone_title}\n"
            f"Overdue Amount: {total_amount:,} INR\n"
            f"Days Overdue: {days_overdue} days\n\n"
            f"{tone_guidelines}\n\n"
            f"Generate both a subject line and the email body. Make sure to invite them to ask "
            f"if they have any questions or require updated payment details."
        ),
        expected_output="A structured JSON object matching the FollowupWriterOutput schema.",
        agent=writer_agent,
        output_pydantic=FollowupWriterOutput
    )

    # 4. Execute Crew
    crew = Crew(
        agents=[writer_agent],
        tasks=[writer_task],
        verbose=False,
        cache=False
    )

    result = crew.kickoff()
    return result.pydantic
