import json
import uuid
from datetime import datetime
from db.database import get_db_cursor
from memory.embeddings import get_embedding


def store_summary(
    session_id: str,
    summary: str,
    metadata: dict = None
) -> str:
    """
    Store a conversation summary with its embedding
    in PostgreSQL.
    """
    doc_id = str(uuid.uuid4())
    embedding = get_embedding(summary)
    turn_range = metadata.pop("turn_range", None) if metadata else None
    meta_json = json.dumps(metadata) if metadata else "{}"

    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO semantic_memory 
                (id, session_id, summary, embedding, turn_range, metadata)
            VALUES 
                (%s, %s, %s, %s::vector, %s, %s::jsonb)
            """,
            (
                doc_id,
                session_id,
                summary,
                str(embedding),      # pgvector accepts string format
                turn_range,
                meta_json,
            )
        )

    print(f"[vector_store] Stored summary {doc_id} for session {session_id}")
    return doc_id


def retrieve_relevant_memories(
    session_id: str,
    query: str,
    top_k: int = 3
) -> list[str]:
    """
    Find the most relevant past summaries for the 
    given query using cosine similarity.
    """
    query_embedding = get_embedding(query)

    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT 
                summary,
                1 - (embedding <=> %s::vector) AS similarity
            FROM semantic_memory
            WHERE session_id = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (
                str(query_embedding),
                session_id,
                str(query_embedding),
                top_k,
            )
        )

        rows = cur.fetchall()

    # Return just the summary texts
    return [row[0] for row in rows]


def retrieve_memories_with_scores(
    session_id: str,
    query: str,
    top_k: int = 3,
    min_similarity: float = 0.3
) -> list[dict]:
    """
    Retrieve summaries with similarity scores.
    Filters out low-relevance results.
    """
    query_embedding = get_embedding(query)

    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT 
                summary,
                turn_range,
                metadata,
                created_at,
                1 - (embedding <=> %s::vector) AS similarity
            FROM semantic_memory
            WHERE session_id = %s
              AND 1 - (embedding <=> %s::vector) > %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (
                str(query_embedding),
                session_id,
                str(query_embedding),
                min_similarity,
                str(query_embedding),
                top_k,
            )
        )

        rows = cur.fetchall()

    return [
        {
            "summary": row[0],
            "turn_range": row[1],
            "metadata": row[2],
            "created_at": str(row[3]),
            "similarity": round(row[4], 4),
        }
        for row in rows
    ]


def delete_session_memories(session_id: str):
    """Delete all semantic memories for a session."""
    with get_db_cursor() as cur:
        cur.execute(
            "DELETE FROM semantic_memory WHERE session_id = %s",
            (session_id,)
        )
    print(f"[vector_store] Cleared memories for session {session_id}")


def count_session_memories(session_id: str) -> int:
    """Count how many summaries exist for a session."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM semantic_memory WHERE session_id = %s",
            (session_id,)
        )
        return cur.fetchone()[0]