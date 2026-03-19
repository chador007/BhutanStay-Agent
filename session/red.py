import redis
import json

r = redis.Redis(
    host='localhost',
    port=6380,
    password='chador2003',
    decode_responses=True
)


# ───────────────────────────────────────────
#  SLIDING WINDOW (conversation history)
# ───────────────────────────────────────────

def update_sliding_window(session_id, user_msg, ai_res, max_size=10):
    key = f"session:{session_id}:history"
    r.lpush(key, json.dumps({"role": "user", "content": user_msg}))
    r.lpush(key, json.dumps({"role": "assistant", "content": ai_res}))
    r.ltrim(key, 0, max_size - 1)


def get_recent_history(session_id):
    key = f"session:{session_id}:history"
    return [json.loads(m) for m in r.lrange(key, 0, -1)]


# ───────────────────────────────────────────
#  WORKING MEMORY (structured, per-session)
# ───────────────────────────────────────────

def get_working_memory(session_id: str) -> dict:
    """
    Retrieve the full working memory as a nested dict.
    Stored as a single JSON string in Redis for proper
    support of nested objects, lists, etc.
    """
    key = f"session:{session_id}:working_memory"
    data = r.get(key)
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}
    return {}


def update_working_memory(session_id: str, extracted_data: dict) -> dict:
    """
    Apply dot-notation updates from the extraction LLM
    to the existing working memory.

    Example extracted_data:
        {
            "search_context.budget.max": 200,
            "search_context.filters": ["pool", "spa"],
            "location": "Paro"
        }

    Dot-notation keys are walked/created as nested dicts.
    Plain keys are set at the top level.
    """
    if not extracted_data:
        return get_working_memory(session_id)

    key = f"session:{session_id}:working_memory"
    current = get_working_memory(session_id)

    for dot_key, value in extracted_data.items():
        keys = dot_key.split(".")

        if len(keys) == 1:
            # Simple top-level key like "location"
            current[keys[0]] = value
        else:
            # Nested key like "search_context.budget.max"
            obj = current
            for k in keys[:-1]:
                if k not in obj or not isinstance(obj[k], dict):
                    obj[k] = {}
                obj = obj[k]
            obj[keys[-1]] = value

    r.set(key, json.dumps(current))
    r.expire(key, 7200)
    return current


def reset_working_memory(session_id: str):
    """Clear working memory for a session."""
    key = f"session:{session_id}:working_memory"
    r.delete(key)