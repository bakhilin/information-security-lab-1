import sqlite3
import os
from contextlib import contextmanager

def get_db_path():
    return os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author) REFERENCES users (username)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_users INTEGER DEFAULT 0,
                active_sessions INTEGER DEFAULT 0,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()


def insert_initial_data():
    import bcrypt
    
    with get_db_connection() as conn:
        users_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        
        if users_count == 0:
            users = [
                ('admin', bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()), 'admin'),
                ('user', bcrypt.hashpw('user123'.encode('utf-8'), bcrypt.gensalt()), 'user')
            ]
            
            conn.executemany(
                'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                users
            )
            
            posts = [
                ('First Post', 'This is the first post', 'admin'),
                ('Second Post', 'This is the second post', 'user'),
                ('Third Post', 'This is the third post', 'admin')
            ]
            
            conn.executemany(
                'INSERT INTO posts (title, content, author) VALUES (?, ?, ?)',
                posts
            )
            
            conn.execute(
                'INSERT INTO stats (total_users, active_sessions) VALUES (?, ?)',
                (len(users), 0)
            )
            
            conn.commit()