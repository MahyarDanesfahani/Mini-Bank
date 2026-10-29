from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import inspect, text

from app import models  # noqa: F401
from app.config import settings, validate_production_settings
from app.database import Base, engine
from app.routers import auth, funds


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_production_settings()
    Base.metadata.create_all(bind=engine)
    # create_all does not add fields to an existing users table.
    columns = {column["name"] for column in inspect(engine).get_columns("users")}
    additions = {
        "national_code": "VARCHAR(10)", "birth_date": "DATE", "gender": "VARCHAR(20)",
        "address": "TEXT", "postal_code": "VARCHAR(10)", "occupation": "VARCHAR(120)",
    }
    fund_columns = {column["name"] for column in inspect(engine).get_columns("funds")}
    fund_additions = {"max_members": "INTEGER NOT NULL DEFAULT 10", "current_members": "INTEGER NOT NULL DEFAULT 1"}
    membership_columns = {column["name"] for column in inspect(engine).get_columns("memberships")}
    with engine.begin() as connection:
        for name, sql_type in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {sql_type}"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_national_code ON users (national_code)"))
        for name, sql_type in fund_additions.items():
            if name not in fund_columns:
                connection.execute(text(f"ALTER TABLE funds ADD COLUMN {name} {sql_type}"))
        if "ended_at" not in membership_columns:
            connection.execute(text("ALTER TABLE memberships ADD COLUMN ended_at DATETIME"))
        connection.execute(text("UPDATE funds SET current_members = (SELECT COUNT(*) FROM memberships WHERE memberships.fund_id = funds.id AND memberships.status = 'active')"))
        connection.execute(text("UPDATE funds SET max_members = current_members WHERE max_members < current_members"))
    yield


app = FastAPI(
    title=settings.app_name,
    description="API مدیریت صندوق قرض‌الحسنه گروهی",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(funds.router, prefix=settings.api_prefix)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/service-worker.js", include_in_schema=False)
def service_worker():
    return FileResponse(STATIC_DIR / "service-worker.js", media_type="application/javascript", headers={"Service-Worker-Allowed": "/"})


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/setup-owner", include_in_schema=False)
def setup_owner_page():
    return FileResponse(STATIC_DIR / "setup-owner.html")


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
