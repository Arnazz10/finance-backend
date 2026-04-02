from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import run_startup_migrations
from .routers import auth, users, records, dashboard
from .models import user, record


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_startup_migrations()
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
