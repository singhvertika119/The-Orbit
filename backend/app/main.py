# pyrefly: ignore [missing-import]
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from slowapi import _rate_limit_exceeded_handler
# pyrefly: ignore [missing-import]
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.limiter import limiter
from app.api.v1 import auth, brief, projects, milestones, invoices, digest, clients

# Initialize Sentry if DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

app = FastAPI(
    title="Gig.ai API",
    description="AI Freelance Command Centre Backend",
    version="1.0"
)

# Connect SlowAPI Limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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
app.include_router(clients.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check():
    """
    Public health check endpoint.
    """
    return {"status": "ok"}
