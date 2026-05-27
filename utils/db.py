import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")


def _get_config():
    return {
        "host":     os.getenv("DB_HOST"),
        "dbname":   os.getenv("DB_NAME", "defaultdb"),
        "user":     os.getenv("DB_USER", "avnadmin"),
        "password": os.getenv("DB_PASSWORD"),
        "port":     int(os.getenv("DB_PORT", 25497)),
        "sslmode":  "require",
    }


@contextmanager
def get_conn():
    conn = psycopg2.connect(**_get_config())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id              TEXT PRIMARY KEY,
                    user_email      TEXT NOT NULL,
                    subject         TEXT,
                    sender_name     TEXT,
                    sender_email    TEXT,
                    received_at     TIMESTAMPTZ,
                    body_preview    TEXT,
                    full_body       TEXT,
                    priority        TEXT,
                    summary         TEXT,
                    processed_at    TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_emails_user_date
                    ON emails(user_email, received_at DESC);

                CREATE INDEX IF NOT EXISTS idx_emails_priority
                    ON emails(priority);
            """)


def upsert_email(data: dict):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO emails
                    (id, user_email, subject, sender_name, sender_email,
                     received_at, body_preview, full_body, priority, summary)
                VALUES
                    (%(id)s, %(user_email)s, %(subject)s, %(sender_name)s, %(sender_email)s,
                     %(received_at)s, %(body_preview)s, %(full_body)s, %(priority)s, %(summary)s)
                ON CONFLICT (id) DO UPDATE SET
                    priority     = EXCLUDED.priority,
                    summary      = EXCLUDED.summary,
                    processed_at = NOW()
            """, data)


def get_cached_emails(user_email: str, start_date: str, end_date: str) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM emails
                WHERE user_email = %s
                  AND received_at >= %s::date
                  AND received_at <  (%s::date + INTERVAL '1 day')
                ORDER BY
                    CASE priority
                        WHEN 'HIGH'   THEN 1
                        WHEN 'MEDIUM' THEN 2
                        WHEN 'LOW'    THEN 3
                        ELSE 4
                    END,
                    received_at DESC
            """, (user_email, start_date, end_date))
            return [dict(r) for r in cur.fetchall()]


def emails_exist_for_range(user_email: str, start_date: str, end_date: str) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM emails
                WHERE user_email = %s
                  AND received_at >= %s::date
                  AND received_at <  (%s::date + INTERVAL '1 day')
                  AND priority IS NOT NULL
            """, (user_email, start_date, end_date))
            count = cur.fetchone()[0]
            return count > 0
