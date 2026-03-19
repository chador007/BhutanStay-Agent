import datetime
from langchain_openai import ChatOpenAI


VLLM_URL = "http://172.19.9.235:5000/v1"


llm = ChatOpenAI(
    model="google/gemma-2-9b-it",
    openai_api_key="EMPTY",
    base_url=VLLM_URL,
    temperature=0,
    model_kwargs={
        "response_format": {"type": "json_object"}
    }
)


RAW_PROMPT = """
Role: You are a structured data extractor.

Task: Analyze this conversation turn and extract ONLY the changes to working memory.

CURRENT WORKING MEMORY STATE:
{memory_state}

CONVERSATION TURN:
{conversation}

YOUR JOB:
Return a JSON object containing ONLY the fields that CHANGED.
Use dot notation for nested updates.

Example 1:
User: Keep it under $200/night
Output:
{
  "search_context.budget.max": 200
}

Example 2:
User: I need a pool
Output:
{
  "search_context.filters": ["pool"]
}

Example 3:
Nothing changed
Output:
{}

Today's date: {current_date}

Return ONLY valid JSON.
"""


def extract_data_with_second_llm(conversation, memory_state="{}"):

    prompt = RAW_PROMPT.format(
        memory_state=memory_state,
        conversation=conversation,
        current_date=datetime.date.today().isoformat()
    )

    response = llm.invoke(prompt)

    return response.content