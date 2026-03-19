import os

from dotenv import load_dotenv

import psycopg2

import psycopg2.pool

from contextlib import contextmanager

load_dotenv()

connection_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    user=os.getenv("DB_USER"),
    password = os.getenv("PASSWORD"),
    host = os.getenv("HOST"),
    port = os.getenv("PORT"),
    database = os.getenv("DBNAME")
)

@contextmanager
def get_db_connection():
    """Get a connection from the pool, auto-return on exit."""
    conn = connection_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        connection_pool.putconn(conn)

@contextmanager
def get_db_cursor():
    """Get a cursor with auto-commit and connection return."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

def init_semantic_memory_table():
    """Create the table and indexes if they don't exist."""
    with get_db_cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS semantic_memory (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id  VARCHAR(255) NOT NULL,
                summary     TEXT NOT NULL,
                embedding   vector(384),
                turn_range  VARCHAR(50),
                metadata    JSONB DEFAULT '{}',
                created_at  TIMESTAMP DEFAULT NOW()
            );
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_semantic_memory_session
                ON semantic_memory (session_id);
        """)

    print("[db] semantic_memory table ready.")
