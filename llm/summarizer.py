from langchain_openai import ChatOpenAI

VLLM_URL = "http://172.19.9.235:5000/v1"

summary_llm = ChatOpenAI(
    model="google/gemma-2-9b-it",
    openai_api_key="EMPTY",
    base_url=VLLM_URL,
    temperature=0,
)

SUMMARY_PROMPT = """
Summarize this conversation chunk concisely.
Focus on:
- What the user wanted
- What was searched/recommended
- Decisions made
- Preferences expressed
- Any unresolved questions

CONVERSATION:
{conversation}

Write a concise summary in 3-5 sentences:
"""


def summarize_conversation(messages_text: str) -> str:
    prompt = SUMMARY_PROMPT.format(conversation=messages_text)
    response = summary_llm.invoke(prompt)
    return response.content.strip()