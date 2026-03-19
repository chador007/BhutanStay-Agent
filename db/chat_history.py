from db.database import get_db_cursor 

def save_history_to_db(session_id: str, message: str, response: str):
    """
    Saves a single conversation turn to the permanent PostgreSQL 
    chat_history table.
    """
    print(f"Saving history for session: {session_id}")

    query = """
    INSERT INTO chat_history (session_id, message, response, created_at)
    VALUES (%s, %s, %s, NOW());
    """
    
    try:
        # Use your new pool-based cursor manager
        with get_db_cursor() as cur:
            cur.execute(query, (session_id, message, response))
            # No need for manual commit; the context manager handles it!
            
    except Exception as e:
        print(f"❌ Error saving chat history: {e}")