from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, brief, projects, milestones, invoices, digest

app = FastAPI(
    title="Gig.ai API",
    description="AI Freelance Command Centre Backend",
    version="1.0"
)

# Configure CORS origins
origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(brief.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(milestones.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")
app.include_router(digest.router, prefix="/api/v1")

@app.get("/health", tags=["health"])
def health_check():
    """
    Public health check endpoint.
    """
    return {"status": "ok"}
