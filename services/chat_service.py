from agent.agent_runner import run_agent_step
from db.chat_history import save_history_to_db


def handle_chat(session_id, message):

    response = run_agent_step(session_id, message)

    save_history_to_db(
        session_id,
        message,
        response
    )

    return response