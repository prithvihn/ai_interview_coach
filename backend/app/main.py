from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import resume, interview, feedback, report, sessions
from app.config import settings

app = FastAPI(
    title="AI Interview Coach API",
    description="Backend API for AI-powered interview coaching",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(resume.router, prefix="/api", tags=["Resume"])
app.include_router(interview.router, prefix="/api", tags=["Interview"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])
app.include_router(report.router, prefix="/api", tags=["Report"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])


@app.get("/")
async def root():
    return {"message": "AI Interview Coach API is running 🚀"}


@app.get("/health")
async def health():
    return {"status": "ok"}
