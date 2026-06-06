import sqlite3
from contextlib import contextmanager
from pathlib import Path


_DB_PATH = Path("backend/data/chatbot.db")


def init_db(db_path: Path = _DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript("""
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS chatbots (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT,
                tone        TEXT DEFAULT 'professional',
                greeting    TEXT,
                fallback_message TEXT,
                model       TEXT DEFAULT 'gpt-4o-mini',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS documents (
                id          TEXT PRIMARY KEY,
                chatbot_id  TEXT NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
                filename    TEXT NOT NULL,
                file_type   TEXT NOT NULL,
                file_path   TEXT NOT NULL,
                status      TEXT DEFAULT 'pending',
                error       TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                id          TEXT PRIMARY KEY,
                chatbot_id  TEXT NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
                started_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id          TEXT PRIMARY KEY,
                session_id  TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                sources     TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS contact_captures (
                id          TEXT PRIMARY KEY,
                chatbot_id  TEXT NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
                email       TEXT NOT NULL,
                name        TEXT,
                notes       TEXT,
                captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS unknown_questions (
                id          TEXT PRIMARY KEY,
                chatbot_id  TEXT NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
                question    TEXT NOT NULL,
                asked_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()


@contextmanager
def get_connection(db_path: Path | None = None):
    if db_path is None:
        db_path = _DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
