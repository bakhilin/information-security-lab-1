import bcrypt
from database import get_db_connection

class UserModel:
    @staticmethod
    def authenticate(username, password):
        with get_db_connection() as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?', 
                (username,)
            ).fetchone()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
                return dict(user)
            return None

    @staticmethod
    def get_user_data(username):
        with get_db_connection() as conn:
            user = conn.execute(
                'SELECT id, username, role, created_at FROM users WHERE username = ?', 
                (username,)
            ).fetchone()
            
            if user:
                return dict(user)
            return None

    @staticmethod
    def get_all_users():
        with get_db_connection() as conn:
            users = conn.execute(
                'SELECT id, username, role, created_at FROM users'
            ).fetchall()
            return [dict(user) for user in users]


class PostModel:
    @staticmethod
    def get_all_posts():
        with get_db_connection() as conn:
            posts = conn.execute(
                'SELECT * FROM posts ORDER BY created_at DESC'
            ).fetchall()
            return [dict(post) for post in posts]

    @staticmethod
    def create_post(title, content, author):
        with get_db_connection() as conn:
            cursor = conn.execute(
                'INSERT INTO posts (title, content, author) VALUES (?, ?, ?)',
                (title, content, author)
            )
            conn.commit()
            return cursor.lastrowid


class StatsModel:
    @staticmethod
    def get_stats():
        with get_db_connection() as conn:
            stats = conn.execute('SELECT * FROM stats ORDER BY id DESC LIMIT 1').fetchone()
            return dict(stats) if stats else None