from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from contextlib import contextmanager
import logging
from models import User, db

logger = logging.getLogger(__name__)


def init_db(app):
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")

            if User.query.count() == 0:
                create_initial_data()

        except SQLAlchemyError as e:
            logger.error(f"Database initialization failed: {e}")
            raise


def create_initial_data():
    try:
        admin = User(username="admin", role="admin")
        admin.set_password("admin123")

        user = User(username="user", role="user")
        user.set_password("user123")

        db.session.add(admin)
        db.session.add(user)

        db.session.commit()
        logger.info("Initial data created successfully")

    except IntegrityError:
        db.session.rollback()
        logger.warning("Initial data already exists")
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to create initial data: {e}")
        raise


@contextmanager
def db_session():
    try:
        yield db.session
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.session.close()


class UserModel:
    @staticmethod
    def authenticate(username, password):
        try:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                return user.to_dict()
            return None
        except SQLAlchemyError as e:
            logger.error(f"Authentication error: {e}")
            return None

    @staticmethod
    def get_user_data(username):
        try:
            user = User.query.filter_by(username=username).first()
            return user.to_dict() if user else None
        except SQLAlchemyError as e:
            logger.error(f"Get user data error: {e}")
            return None

    @staticmethod
    def get_all_users():
        try:
            users = User.query.all()
            return [user.to_dict() for user in users]
        except SQLAlchemyError as e:
            logger.error(f"Get all users error: {e}")
            return []

    @staticmethod
    def create_user(username, password, role="user"):
        try:
            if User.query.filter_by(username=username).first():
                return False, "Username already exists"

            user = User(username=username, role=role)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            return True, "User created successfully"
        except IntegrityError:
            db.session.rollback()
            return False, "Username already exists"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Database error: {str(e)}"
