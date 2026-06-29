from crewai import LLM
from app.core.config import settings

if not settings.GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in the environment variables.")

# Versatile model for complex tasks (brief parsing, scoping, proposal drafting, digest writing)
llm_versatile = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=settings.GROQ_API_KEY,
    temperature=0.3
)

# Instant model for structured, lightweight tasks (invoice generation, follow-up reminders)
llm_instant = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=settings.GROQ_API_KEY,
    temperature=0.2
)
