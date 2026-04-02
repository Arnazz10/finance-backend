import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.record import RecordType
from app.models.user import UserRole
from app.routers.auth import login_for_access_token, register
from app.routers.dashboard import get_category_totals, get_summary, get_trends
from app.routers.records import create_record, delete_record, get_record, list_records, update_record
from app.routers.users import create_user, list_users, update_user_role
from app.schemas.record import RecordCreate, RecordUpdate
from app.schemas.user import UserCreate, UserUpdate


class FinanceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix=".db")
        cls.engine = create_engine(
            f"sqlite:///{cls.db_path}",
            connect_args={"check_same_thread": False},
        )
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls.engine,
        )

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        os.close(cls.db_fd)
        os.unlink(cls.db_path)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestingSessionLocal()

    def tearDown(self):
        self.db.close()

    def register_user(self, *, name: str, email: str, password: str, role: UserRole):
        return register(
            UserCreate(name=name, email=email, password=password, role=role),
            db=self.db,
        )

    def login(self, email: str, password: str):
        return login_for_access_token(
            db=self.db,
            form_data=OAuth2PasswordRequestForm(
                username=email,
                password=password,
                scope="",
                grant_type="password",
                client_id=None,
                client_secret=None,
            ),
        )

    def seed_default_users(self):
        admin = self.register_user(
            name="Admin",
            email="admin@example.com",
            password="password123",
            role=UserRole.ADMIN,
        )
        analyst = self.register_user(
            name="Analyst",
            email="analyst@example.com",
            password="password123",
            role=UserRole.ANALYST,
        )
        viewer = self.register_user(
            name="Viewer",
            email="viewer@example.com",
            password="password123",
            role=UserRole.VIEWER,
        )
        return admin, analyst, viewer

    def test_auth_rbac_crud_and_dashboard(self):
        admin, analyst, viewer = self.seed_default_users()

        admin_token = self.login("admin@example.com", "password123")
        analyst_token = self.login("analyst@example.com", "password123")
        viewer_token = self.login("viewer@example.com", "password123")
        self.assertEqual(admin_token["token_type"], "bearer")
        self.assertEqual(analyst_token["token_type"], "bearer")
        self.assertEqual(viewer_token["token_type"], "bearer")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        records = [
            RecordCreate(
                amount=5000,
                type=RecordType.INCOME,
                category="Salary",
                date=now - timedelta(days=25),
                notes="Monthly salary",
            ),
            RecordCreate(
                amount=1200,
                type=RecordType.EXPENSE,
                category="Rent",
                date=now - timedelta(days=20),
                notes="Apartment rent",
            ),
            RecordCreate(
                amount=300,
                type=RecordType.EXPENSE,
                category="Groceries",
                date=now - timedelta(days=10),
                notes="Weekly shopping",
            ),
            RecordCreate(
                amount=1500,
                type=RecordType.INCOME,
                category="Freelance",
                date=now - timedelta(days=2),
                notes="Side project",
            ),
        ]

        created = [create_record(record=payload, db=self.db, current_user=analyst) for payload in records]
        self.assertEqual(len(created), 4)

        listed = list_records(db=self.db, current_user=analyst)
        self.assertEqual(len(listed), 4)

        filtered = list_records(
            db=self.db,
            current_user=analyst,
            category="Rent",
            type=RecordType.EXPENSE,
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].category, "Rent")

        with self.assertRaises(HTTPException) as bad_range:
            list_records(
                db=self.db,
                current_user=analyst,
                date_from=now,
                date_to=now - timedelta(days=30),
            )
        self.assertEqual(bad_range.exception.status_code, 400)

        fetched = get_record(record_id=created[0].id, db=self.db, current_user=analyst)
        self.assertEqual(fetched.category, "Salary")

        updated = update_record(
            record_id=created[0].id,
            update_data=RecordUpdate(amount=5200, notes="Updated salary"),
            db=self.db,
            current_user=analyst,
        )
        self.assertEqual(updated.amount, 5200)

        summary = get_summary(db=self.db, current_user=viewer)
        self.assertEqual(summary["total_income"], 6700.0)
        self.assertEqual(summary["total_expenses"], 1500.0)
        self.assertEqual(summary["net_balance"], 5200.0)
        self.assertEqual(summary["category_totals"]["Salary"], 5200.0)
        self.assertEqual(summary["category_totals"]["Rent"], -1200.0)
        self.assertEqual(len(summary["recent_transactions"]), 4)

        category_totals = get_category_totals(db=self.db, current_user=viewer)
        self.assertTrue(
            any(item["category"] == "Freelance" and item["total"] == 1500.0 for item in category_totals)
        )

        trends = get_trends(db=self.db, current_user=analyst)
        self.assertGreaterEqual(len(trends), 1)

        delete_record(record_id=created[1].id, db=self.db, current_user=admin)
        with self.assertRaises(HTTPException) as deleted_fetch:
            get_record(record_id=created[1].id, db=self.db, current_user=analyst)
        self.assertEqual(deleted_fetch.exception.status_code, 404)

    def test_admin_user_management_and_inactive_login(self):
        admin, _, viewer = self.seed_default_users()

        created_user = create_user(
            user=UserCreate(
                name="Ops",
                email="ops@example.com",
                password="password123",
                role=UserRole.VIEWER,
            ),
            db=self.db,
            current_user=admin,
        )
        self.assertEqual(created_user.email, "ops@example.com")

        users = list_users(db=self.db, current_user=admin)
        self.assertEqual(len(users), 4)

        updated_viewer = update_user_role(
            user_id=viewer.id,
            update_data=UserUpdate(is_active=False),
            db=self.db,
            current_user=admin,
        )
        self.assertFalse(updated_viewer.is_active)

        with self.assertRaises(HTTPException) as inactive_login:
            self.login("viewer@example.com", "password123")
        self.assertEqual(inactive_login.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
