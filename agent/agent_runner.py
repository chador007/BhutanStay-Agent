from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage
)

from session.session_store import session_store
from prompts.system_prompt import get_system_prompt
from tools.tools_registry import tools_map, TOOL_DESCRIPTIONS
from utils.helpers import extract_text_content
from llm.llm_provider import get_llm


llm = get_llm()


def run_agent_step(session_id: str, user_input: str):

    if session_id not in session_store:
        session_store[session_id] = [get_system_prompt()]

    messages = session_store[session_id]

    messages.append(HumanMessage(content=user_input))

    MAX_STEPS = 5
    step = 0

    while step < MAX_STEPS:

        step += 1

        response = llm.invoke(messages, tools=TOOL_DESCRIPTIONS)

        content = extract_text_content(response.content)

        ai_message = AIMessage(
            content=content,
            tool_calls=response.tool_calls
        )

        messages.append(ai_message)

        if not response.tool_calls:
            session_store[session_id] = messages
            return content

        for tool_call in response.tool_calls:

            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            tool = tools_map.get(tool_name)

            result = "Tool not found"

            if tool:
                result = tool(**tool_args)

            messages.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                    content=str(result)
                )
            )

    return "Sorry, something went wrong."