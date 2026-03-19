from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    messages_from_dict,
    messages_to_dict,
)

from prompts.system_prompt import get_system_prompt
from tools.tools_registry import tools_map, TOOL_DESCRIPTIONS
from utils.helpers import extract_text_content
from llm.llm_provider import get_llm
from memory.memory_extractor import extract_data_with_second_llm
from session.red import (
    r,
    get_working_memory,
    update_working_memory,
)
import json

llm = get_llm()

# ─── Marker so we can strip it before saving ───
MEMORY_MARKER = "## Current Working Memory"


def _build_memory_message(memory: dict):
    """
    Build a SystemMessage that injects the current
    working memory into the LLM context.
    Returns None if memory is empty.
    """
    if not memory:
        return None
    return SystemMessage(
        content=(
            f"{MEMORY_MARKER}\n"
            "```json\n"
            f"{json.dumps(memory, indent=2)}\n"
            "```\n"
            "Use this context to give relevant, consistent answers. "
            "Do NOT repeat this JSON to the user."
        )
    )


def _strip_memory_messages(messages):
    """
    Remove injected memory messages before persisting,
    since they are rebuilt fresh every turn.
    """
    return [
        m for m in messages
        if not (
            isinstance(m, SystemMessage)
            and MEMORY_MARKER in (m.content or "")
        )
    ]


def run_agent_step(session_id: str, user_input: str):
    history_key = f"session:{session_id}:history"

    # ── 1. Bootstrap: first request → store system prompt ──
    if not r.exists(history_key):
        system_msg = get_system_prompt()
        if isinstance(system_msg, str):
            system_msg = SystemMessage(content=system_msg)
        r.rpush(history_key, json.dumps(messages_to_dict([system_msg])[0]))

    # ── 2. Load conversation history from Redis ──
    history_raw = r.lrange(history_key, 0, -1)
    messages = messages_from_dict([json.loads(m) for m in history_raw])

    # ── 3. Load working memory & inject after system prompt ──
    current_memory = get_working_memory(session_id)
    mem_msg = _build_memory_message(current_memory)
    if mem_msg:
        messages.insert(1, mem_msg)

    # ── 4. Add user input ──
    messages.append(HumanMessage(content=user_input))

    MAX_STEPS = 5
    step = 0

    while step < MAX_STEPS:
        step += 1
        response = llm.invoke(messages, tools=TOOL_DESCRIPTIONS)
        content = extract_text_content(response.content)

        ai_message = AIMessage(
            content=content,
            tool_calls=response.tool_calls,
        )
        messages.append(ai_message)

        # ── 5. LLM finished (no tool calls) ──
        if not response.tool_calls:

            # ───────────────────────────────────────
            #  A. EXTRACT & UPDATE WORKING MEMORY
            # ───────────────────────────────────────
            try:
                conversation_turn = f"User: {user_input}\nAssistant: {content}"
                memory_state_str = json.dumps(current_memory) if current_memory else "{}"

                updates = extract_data_with_second_llm(
                    conversation=conversation_turn,
                    memory_state=memory_state_str,
                )

                if updates:
                    updated = update_working_memory(session_id, updates)
                    print(f"[working_memory] Updates applied: {json.dumps(updates)}")
                    print(f"[working_memory] Full state: {json.dumps(updated, indent=2)}")
                else:
                    print("[working_memory] No changes detected.")
            except Exception as e:
                # Never let extraction crash the user response
                print(f"[working_memory] Extraction error: {e}")

            # ───────────────────────────────────────
            #  B. PERSIST HISTORY (sliding window)
            # ───────────────────────────────────────
            # Strip the ephemeral memory message before saving
            clean_messages = _strip_memory_messages(messages)
            serializable_messages = messages_to_dict(clean_messages)

            # Keep [system prompt @ 0] + [last 10 messages]
            if len(serializable_messages) > 11:
                system_prompt_msg = serializable_messages[0]
                last_ten = serializable_messages[-10:]
                serializable_messages = [system_prompt_msg] + last_ten

            r.delete(history_key)
            for msg in serializable_messages:
                r.rpush(history_key, json.dumps(msg))
            r.expire(history_key, 86400)

            return content

        # ── 6. Process tool calls ──
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool = tools_map.get(tool_name)
            result = tool(**tool_args) if tool else "Tool not found"

            messages.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                    content=str(result),
                )
            )

    return "Sorry, something went wrong."