from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers.opportunities import router as opportunities_router

app = FastAPI(title="Proteins.1 Opportunity Map API")

# Wide open for a hackathon demo - tighten before showing this to anyone outside the room.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(opportunities_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
