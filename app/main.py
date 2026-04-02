from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import settings
from .database import SessionLocal, run_startup_migrations
from .models.user import User, UserRole
from .routers import auth, users, records, dashboard
from .models import user, record
from .utils.security import get_password_hash


def seed_demo_users() -> None:
    if not settings.seed_demo_data:
        return

    demo_users = [
        {
            "name": settings.demo_admin_name,
            "email": settings.demo_admin_email,
            "password": settings.demo_admin_password,
            "role": UserRole.ADMIN,
        },
        {
            "name": settings.demo_analyst_name,
            "email": settings.demo_analyst_email,
            "password": settings.demo_analyst_password,
            "role": UserRole.ANALYST,
        },
        {
            "name": settings.demo_viewer_name,
            "email": settings.demo_viewer_email,
            "password": settings.demo_viewer_password,
            "role": UserRole.VIEWER,
        },
    ]

    db = SessionLocal()
    try:
        for demo_user in demo_users:
            existing_user = db.query(User).filter(User.email == demo_user["email"]).first()
            if existing_user:
                continue
            db.add(
                User(
                    name=demo_user["name"],
                    email=demo_user["email"],
                    hashed_password=get_password_hash(demo_user["password"]),
                    role=demo_user["role"],
                    is_active=True,
                )
            )
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_startup_migrations()
    seed_demo_users()
    yield

app = FastAPI(
    title="Zorvyn Finance Dashboard API",
    description="Backend for a finance dashboard with RBAC, JWT auth, record management, and analytics.",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Zorvyn Finance API",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
