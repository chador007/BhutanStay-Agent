import redis
import json

r = redis.Redis(
    host='localhost',
    port=6380,
    password='chador2003',
    decode_responses=True
)

def update_sliding_window(session_id, user_msg, ai_res, max_size=10):
    key = f"session:{session_id}:history"
    r.lpush(key, json.dumps({"role": "user", "content": user_msg}))
    r.lpush(key, json.dumps({"role": "assistant", "content": ai_res}))
    r.ltrim(key, 0, max_size - 1)


def get_recent_history(session_id):
    key = f"session:{session_id}:history"
    return [json.loads(m) for m in r.lrange(key, 0, -1)]


def get_working_memory(session_id: str) -> dict:
    key = f"session:{session_id}:working_memory"
    data = r.get(key)
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}
    return {}


def update_working_memory(session_id: str, extracted_data: dict) -> dict:
    if not extracted_data:
        return get_working_memory(session_id)

    key = f"session:{session_id}:working_memory"
    current = get_working_memory(session_id)

    for dot_key, value in extracted_data.items():
        keys = dot_key.split(".")
        if len(keys) == 1:
            current[keys[0]] = value
        else:
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
    key = f"session:{session_id}:working_memory"
    r.delete(key)


def increment_turn_counter(session_id: str) -> int:
    """Increment and return the current turn count."""
    key = f"session:{session_id}:turn_count"
    count = r.incr(key)
    r.expire(key, 86400)
    return count


def get_turn_counter(session_id: str) -> int:
    key = f"session:{session_id}:turn_count"
    val = r.get(key)
    return int(val) if val else 0


def reset_turn_counter(session_id: str):
    key = f"session:{session_id}:turn_count"
    r.set(key, 0)
    r.expire(key, 86400)

def append_to_summary_buffer(session_id: str, role: str, content: str):
    """Add a message to the buffer awaiting summarization."""
    key = f"session:{session_id}:summary_buffer"
    r.rpush(key, json.dumps({"role": role, "content": content}))
    r.expire(key, 86400)


def get_summary_buffer(session_id: str) -> list[dict]:
    key = f"session:{session_id}:summary_buffer"
    raw = r.lrange(key, 0, -1)
    return [json.loads(m) for m in raw]


def clear_summary_buffer(session_id: str):
    key = f"session:{session_id}:summary_buffer"
    r.delete(key)