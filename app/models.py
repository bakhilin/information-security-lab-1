from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Text, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
import bcrypt
from datetime import datetime
import logging

db = SQLAlchemy()
Base = declarative_base()
logger = logging.getLogger(__name__)


class User(db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(120), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Check constraints
    __table_args__ = (
        CheckConstraint(
            "LENGTH(username) >= 3 AND LENGTH(username) <= 50",
            name="check_username_length",
        ),
        CheckConstraint("role IN ('user', 'admin')", name="check_role_values"),
    )

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), self.password_hash.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }