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
from llm.summarizer import summarize_conversation
from memory.vector_store import store_summary, retrieve_relevant_memories
from session.red import (
    r,
    get_working_memory,
    update_working_memory,
    increment_turn_counter,
    append_to_summary_buffer,
    get_summary_buffer,
    clear_summary_buffer,
)
import json

llm = get_llm()

MEMORY_MARKER = "## Current Working Memory"
SEMANTIC_MARKER = "## Relevant Past Context"
SUMMARY_EVERY_N_TURNS = 10

def _sanitize_messages(messages):
    """
    Fix message ordering to satisfy Gemini's strict rules:
    
    1. AIMessage with tool_calls MUST follow HumanMessage or ToolMessage
    2. ToolMessage MUST follow AIMessage with tool_calls (or another ToolMessage)
    3. No orphaned tool sequences
    
    Removes any messages that violate these rules.
    """
    if not messages:
        return messages

    sanitized = []
    i = 0

    while i < len(messages):
        msg = messages[i]

        # ── SystemMessage: always keep ──
        if isinstance(msg, SystemMessage):
            sanitized.append(msg)
            i += 1
            continue

        # ── HumanMessage: always keep ──
        if isinstance(msg, HumanMessage):
            sanitized.append(msg)
            i += 1
            continue

        # ── AIMessage WITH tool_calls ──
        if isinstance(msg, AIMessage) and getattr(msg, 'tool_calls', None):
            # Find the last non-system message
            prev = None
            for p in reversed(sanitized):
                if not isinstance(p, SystemMessage):
                    prev = p
                    break

            if prev is None or isinstance(prev, AIMessage):
                # No valid predecessor → skip this AI + its ToolMessages
                print(f"[sanitize] Dropping orphaned AI tool_call at position {i}")
                i += 1
                while i < len(messages) and isinstance(messages[i], ToolMessage):
                    i += 1
                continue

            # Valid predecessor → keep AI + collect its ToolMessages
            sanitized.append(msg)
            i += 1
            while i < len(messages) and isinstance(messages[i], ToolMessage):
                sanitized.append(messages[i])
                i += 1
            continue

        # ── AIMessage WITHOUT tool_calls ──
        if isinstance(msg, AIMessage):
            sanitized.append(msg)
            i += 1
            continue

        # ── ToolMessage ──
        if isinstance(msg, ToolMessage):
            if sanitized and (
                (isinstance(sanitized[-1], AIMessage) and getattr(sanitized[-1], 'tool_calls', None))
                or isinstance(sanitized[-1], ToolMessage)
            ):
                sanitized.append(msg)
            else:
                print(f"[sanitize] Dropping orphaned ToolMessage at position {i}")
            i += 1
            continue

        # ── Anything else: keep ──
        sanitized.append(msg)
        i += 1

    return sanitized


def _smart_trim(serializable_messages, max_total=11):
    """
    Trim message history while always cutting at a 
    HumanMessage boundary to avoid breaking tool sequences.
    """
    if len(serializable_messages) <= max_total:
        return serializable_messages

    # Always keep system prompt at index 0
    system_msg = serializable_messages[0]
    rest = serializable_messages[1:]
    max_keep = max_total - 1  # space for system prompt

    # Find all HumanMessage positions (valid cut points)
    human_indices = [
        i for i, msg in enumerate(rest)
        if msg.get("type") == "human"
    ]

    # Walk backwards through cut points to find one that fits
    for idx in human_indices:
        candidate = rest[idx:]
        if len(candidate) <= max_keep:
            return [system_msg] + candidate

    # Fallback: take last max_keep, but start at nearest HumanMessage
    fallback = rest[-max_keep:]
    for i, msg in enumerate(fallback):
        if msg.get("type") == "human":
            return [system_msg] + fallback[i:]

    # Last resort
    return [system_msg] + fallback[-max_keep:]


def _build_memory_message(memory: dict):
    if not memory:
        return None
    return SystemMessage(
        content=(
            f"{MEMORY_MARKER}\n"
            "```json\n"
            f"{json.dumps(memory, indent=2)}\n"
            "```\n"
            "Use this context for consistent answers. "
            "Do NOT repeat this JSON to the user."
        )
    )


def _build_semantic_message(memories: list[str]):
    if not memories:
        return None
    combined = "\n\n---\n\n".join(memories)
    return SystemMessage(
        content=(
            f"{SEMANTIC_MARKER}\n"
            "These are summaries of earlier parts of this conversation:\n\n"
            f"{combined}\n\n"
            "Use this context if relevant to the current question."
        )
    )


def _strip_injected_messages(messages):
    """Remove ephemeral injected messages before saving."""
    return [
        m for m in messages
        if not (
            isinstance(m, SystemMessage)
            and (
                MEMORY_MARKER in (m.content or "")
                or SEMANTIC_MARKER in (m.content or "")
            )
        )
    ]


def _maybe_summarize(session_id: str, turn_count: int):
    if turn_count % SUMMARY_EVERY_N_TURNS != 0:
        return

    buffer = get_summary_buffer(session_id)
    if not buffer:
        return

    conversation_text = "\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}"
        for msg in buffer
    )

    try:
        summary = summarize_conversation(conversation_text)
        store_summary(
            session_id=session_id,
            summary=summary,
            metadata={
                "turn_range": f"{turn_count - SUMMARY_EVERY_N_TURNS + 1}-{turn_count}"
            }
        )
        print(f"[semantic_memory] Summary stored for turns ending at {turn_count}")
        clear_summary_buffer(session_id)
    except Exception as e:
        print(f"[semantic_memory] Summarization failed: {e}")



def run_agent_step(session_id: str, user_input: str):
    history_key = f"session:{session_id}:history"

    # ── 1. Bootstrap ──
    if not r.exists(history_key):
        system_msg = get_system_prompt()
        if isinstance(system_msg, str):
            system_msg = SystemMessage(content=system_msg)
        r.rpush(history_key, json.dumps(messages_to_dict([system_msg])[0]))

    # ── 2. Load conversation history ──
    history_raw = r.lrange(history_key, 0, -1)
    messages = messages_from_dict([json.loads(m) for m in history_raw])

    # ── 3. Inject WORKING MEMORY (Layer 2) ──
    current_memory = get_working_memory(session_id)
    mem_msg = _build_memory_message(current_memory)
    inject_index = 1
    if mem_msg:
        messages.insert(inject_index, mem_msg)
        inject_index += 1

    # ── 4. Retrieve & inject SEMANTIC MEMORY (Layer 3) ──
    try:
        past_summaries = retrieve_relevant_memories(
            session_id=session_id,
            query=user_input,
            top_k=3
        )
        sem_msg = _build_semantic_message(past_summaries)
        if sem_msg:
            messages.insert(inject_index, sem_msg)
    except Exception as e:
        print(f"[semantic_memory] Retrieval failed: {e}")

    # ── 5. Append user input ──
    messages.append(HumanMessage(content=user_input))

    # ══════════════════════════════════════════
    #  SANITIZE before sending to Gemini
    # ══════════════════════════════════════════
    messages = _sanitize_messages(messages)

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

        # ── 6. LLM finished ──
        if not response.tool_calls:

            # ─── A. UPDATE WORKING MEMORY ───
            try:
                conversation_turn = f"User: {user_input}\nAssistant: {content}"
                memory_state_str = json.dumps(current_memory) if current_memory else "{}"

                updates = extract_data_with_second_llm(
                    conversation=conversation_turn,
                    memory_state=memory_state_str,
                )
                if updates:
                    update_working_memory(session_id, updates)
                    print(f"[working_memory] Updates: {json.dumps(updates)}")
            except Exception as e:
                print(f"[working_memory] Error: {e}")

            # ─── B. TRACK TURNS FOR SUMMARIZATION ───
            append_to_summary_buffer(session_id, "user", user_input)
            append_to_summary_buffer(session_id, "assistant", content)
            turn_count = increment_turn_counter(session_id)

            # ─── C. MAYBE SUMMARIZE → VECTOR DB ───
            _maybe_summarize(session_id, turn_count)

            # ─── D. PERSIST SLIDING WINDOW ───
            clean_messages = _strip_injected_messages(messages)
            serializable_messages = messages_to_dict(clean_messages)

            # ════════════════════════════════════
            #  SMART TRIM (cut at clean boundary)
            # ════════════════════════════════════
            serializable_messages = _smart_trim(serializable_messages, max_total=11)

            r.delete(history_key)
            for msg in serializable_messages:
                r.rpush(history_key, json.dumps(msg))
            r.expire(history_key, 86400)

            return content

        # ── 7. Process tool calls ──
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