import sys
import os

# Add the current directory to sys.path to make sure we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def seed_demo_users():
    db: Session = SessionLocal()
    try:
        demo_users = [
            {
                "email": "admin@doxa.demo",
                "password": "Admin123!",
                "role": UserRole.ADMIN,
            },
            {
                "email": "agent@doxa.demo",
                "password": "Agent123!",
                "role": UserRole.AGENT,
            },
            {
                "email": "client@doxa.demo",
                "password": "Client123!",
                "role": UserRole.CLIENT,
            },
        ]

        print("Starting demo user seeding...")

        for user_data in demo_users:
            user = db.query(User).filter(User.email == user_data["email"]).first()
            if not user:
                print(f"Creating user: {user_data['email']}")
                new_user = User(
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    is_active=True,
                )
                db.add(new_user)
            else:
                print(f"User already exists: {user_data['email']}")

        db.commit()
        print("Demo user seeding completed.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_users()
