from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.database import init_db
from backend.api.institutions import router as institutions_router
from backend.api.projects import router as projects_router

app = FastAPI(title="EPA System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(institutions_router, prefix="/api/institutions", tags=["Institutions"])
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.on_event("startup")
def startup_event():
    init_db()