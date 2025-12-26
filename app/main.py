"""Main FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.database import create_db_and_tables
from app.routers import router

# Create FastAPI app
app = FastAPI(
    title="TastyTrade Transaction Analyzer",
    description="Upload, classify, and analyze TastyTrade CSV transactions",
    version="1.0.0"
)

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Setup static files (if needed)
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(router)


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with upload form."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request):
    """Transactions list page."""
    return templates.TemplateResponse(
        "transactions.html",
        {"request": request}
    )


@app.get("/spreads", response_class=HTMLResponse)
async def spreads_page(request: Request):
    """Spreads list page."""
    return templates.TemplateResponse(
        "spreads.html",
        {"request": request}
    )


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Analytics and summary page."""
    return templates.TemplateResponse(
        "analytics.html",
        {"request": request}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
