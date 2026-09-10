from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.database import init_db
from app.routers.collection import router as collection_router

app = FastAPI(title="Proteins.1 EU Platform-Competitor Collector")

# Wide open for a hackathon demo - tighten before showing this to anyone outside the room.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(collection_router)


@app.on_event("startup")
def on_startup():
    init_db()


_FRONTEND = Path(__file__).resolve().parent.parent / "reports" / "frontend.html"


@app.get("/", include_in_schema=False)
def frontend():
    """The single frontend page (Overview + Data tabs). Regenerate with
    `python reports/build_frontend_page.py`."""
    if _FRONTEND.exists():
        return FileResponse(_FRONTEND, media_type="text/html")
    return JSONResponse(
        {"detail": "frontend not built - run: python reports/build_frontend_page.py"},
        status_code=503,
    )


@app.get("/health")
def health():
    return {"status": "ok"}
