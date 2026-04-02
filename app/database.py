from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./finance.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def run_startup_migrations() -> None:
    Base.metadata.create_all(bind=engine)

    # SQLite-friendly additive migration to keep existing local DBs usable.
    expected_columns = {
        "users": {
            "is_active": "BOOLEAN NOT NULL DEFAULT 1",
        },
        "financial_records": {
            "notes": "VARCHAR",
            "is_deleted": "BOOLEAN NOT NULL DEFAULT 0",
        },
    }

    with engine.begin() as connection:
        inspector = inspect(connection)
        for table_name, columns in expected_columns.items():
            if not inspector.has_table(table_name):
                continue

            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for column_name, definition in columns.items():
                if column_name in existing_columns:
                    continue
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ADD COLUMN {column_name} {definition}"
                    )
                )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
