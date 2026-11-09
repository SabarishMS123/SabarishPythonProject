"""
Database service - PostgreSQL connection and schema management.
Handles users, chat sessions, messages, and pinned chats.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv
from datetime import datetime
from datetime import timedelta
import hashlib
import secrets

load_dotenv()


class Database:
    def __init__(self):
        self.config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "dbname": os.getenv("DB_NAME", "ai_assistant_db"),
            "user": os.getenv("DB_USER", "aiapp"),
            "password": os.getenv("DB_PASSWORD", "aiapppass"),
        }

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def init_schema(self):
        """Create all required tables if they don't exist."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Users table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(150) NOT NULL,
                        is_verified BOOLEAN DEFAULT FALSE,
                        verification_code VARCHAR(10),
                        verification_expires TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Chat sessions (one per AI type conversation)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        ai_type VARCHAR(50) NOT NULL,
                        title VARCHAR(255) DEFAULT 'New Chat',
                        is_pinned BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Messages
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
                        role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Indexes for performance
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sessions_user 
                    ON chat_sessions(user_id);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_session 
                    ON messages(session_id);
                """)
                print("✅ Database schema initialized successfully.")

    # ─── User operations ───────────────────────────────────────────────

    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100000
        )
        return f"{salt}${hash_obj.hex()}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt, hash_hex = stored_hash.split("$")
            hash_obj = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt.encode(), 100000
            )
            return hash_obj.hex() == hash_hex
        except Exception:
            return False

    def create_user(self, email: str, password: str, full_name: str, code: str) -> int | None:
        """Create unverified user. Returns user_id or None if email exists."""
        password_hash = self.hash_password(password)
        expires = datetime.utcnow().replace(microsecond=0)
        # expire in 15 minutes
        
        expires = datetime.utcnow() + timedelta(minutes=15)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """
                        INSERT INTO users (email, password_hash, full_name, verification_code, verification_expires)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id;
                        """,
                        (email.lower().strip(), password_hash, full_name.strip(), code, expires),
                    )
                    user_id = cur.fetchone()[0]
                    return user_id
                except psycopg2.IntegrityError:
                    return None  # email already exists

    def verify_user(self, email: str, code: str) -> bool:
        """Verify the email code and mark user as verified."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, verification_code, verification_expires, is_verified
                    FROM users WHERE email = %s;
                    """,
                    (email.lower().strip(),),
                )
                row = cur.fetchone()
                if not row:
                    return False
                if row["is_verified"]:
                    return True
                if row["verification_code"] != code:
                    return False
                if row["verification_expires"] < datetime.utcnow():
                    return False

                cur.execute(
                    """
                    UPDATE users
                    SET is_verified = TRUE, verification_code = NULL, verification_expires = NULL
                    WHERE id = %s;
                    """,
                    (row["id"],),
                )
                return True

    def get_user_by_email(self, email: str) -> dict | None:
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM users WHERE email = %s;",
                    (email.lower().strip(),),
                )
                return cur.fetchone()

    def authenticate(self, email: str, password: str) -> dict | None:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not user["is_verified"]:
            return None
        if self.verify_password(password, user["password_hash"]):
            return dict(user)
        return None

    # ─── Chat session operations ────────────────────────────────────────

    def create_session(self, user_id: int, ai_type: str, title: str = "New Chat") -> int:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_sessions (user_id, ai_type, title)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (user_id, ai_type, title),
                )
                return cur.fetchone()[0]

    def get_sessions(self, user_id: int, ai_type: str | None = None) -> list:
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if ai_type:
                    cur.execute(
                        """
                        SELECT * FROM chat_sessions
                        WHERE user_id = %s AND ai_type = %s
                        ORDER BY is_pinned DESC, updated_at DESC;
                        """,
                        (user_id, ai_type),
                    )
                else:
                    cur.execute(
                        """
                        SELECT * FROM chat_sessions
                        WHERE user_id = %s
                        ORDER BY is_pinned DESC, updated_at DESC;
                        """,
                        (user_id,),
                    )
                return [dict(r) for r in cur.fetchall()]

    def update_session_title(self, session_id: int, title: str):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat_sessions
                    SET title = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                    """,
                    (title[:255], session_id),
                )

    def pin_session(self, session_id: int, pinned: bool = True):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat_sessions
                    SET is_pinned = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                    """,
                    (pinned, session_id),
                )

    def delete_session(self, session_id: int):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chat_sessions WHERE id = %s;", (session_id,))

    def touch_session(self, session_id: int):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat_sessions
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                    """,
                    (session_id,),
                )

    # ─── Message operations ────────────────────────────────────────────

    def add_message(self, session_id: int, role: str, content: str) -> int:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (session_id, role, content)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (session_id, role, content),
                )
                msg_id = cur.fetchone()[0]
                # also touch the session
                cur.execute(
                    """
                    UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                    """,
                    (session_id,),
                )
                return msg_id

    def get_messages(self, session_id: int) -> list:
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM messages
                    WHERE session_id = %s
                    ORDER BY created_at ASC;
                    """,
                    (session_id,),
                )
                return [dict(r) for r in cur.fetchall()]


# Singleton instance
db = Database()
