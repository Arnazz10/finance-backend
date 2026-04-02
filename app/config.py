import os


def _load_dotenv(dotenv_path: str = ".env") -> None:
    if not os.path.exists(dotenv_path):
        return

    with open(dotenv_path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./finance.db")
        self.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.seed_demo_data = _as_bool(os.getenv("SEED_DEMO_DATA"), True)
        self.demo_admin_name = os.getenv("DEMO_ADMIN_NAME", "Demo Admin")
        self.demo_admin_email = os.getenv("DEMO_ADMIN_EMAIL", "admin@demo.local")
        self.demo_admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "AdminPass123")
        self.demo_analyst_name = os.getenv("DEMO_ANALYST_NAME", "Demo Analyst")
        self.demo_analyst_email = os.getenv(
            "DEMO_ANALYST_EMAIL", "analyst@demo.local"
        )
        self.demo_analyst_password = os.getenv(
            "DEMO_ANALYST_PASSWORD", "AnalystPass123"
        )
        self.demo_viewer_name = os.getenv("DEMO_VIEWER_NAME", "Demo Viewer")
        self.demo_viewer_email = os.getenv("DEMO_VIEWER_EMAIL", "viewer@demo.local")
        self.demo_viewer_password = os.getenv(
            "DEMO_VIEWER_PASSWORD", "ViewerPass123"
        )


_load_dotenv()
settings = Settings()
