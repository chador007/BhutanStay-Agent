from sqlalchemy import text
from .database import get_db

def save_history_to_db(session_id, message, response):

    db = get_db()

    with db._engine.connect() as conn:

        conn.execute(
            text("""
            INSERT INTO chat_history(session_id, message, response)
            VALUES(:s,:m,:r)
            """),
            {
                "s": session_id,
                "m": message,
                "r": response
            }
        )

        conn.commit()