
from langchain_core.messages import SystemMessage
  
import datetime

#Working memory update
def data_extractor():

    raw_prompt = """

Role: You are a structured data extractor.

Task: Analyze this conversation turn and extract ONLY the changes to working memory.

CURRENT WORKING MEMORY STATE:
{show the full current state as JSON}

CONVERSATION TURN:
User: "I want pet-friendly hotels under $150"
Assistant: "Great! I've updated your search to show pet-friendly options under $150..."

YOUR JOB:
Return a JSON object containing ONLY the fields that CHANGED.
Use dot notation for nested updates.

EXAMPLES:

Example 1 - User sets budget:
Input: "Keep it under $200/night"
Output:
{
  "search_context.budget.max": 200,
  "search_context.budget.currency": "USD"
}

Example 2 - User adds filters:
Input: "I need a pool and free parking"
Output:
{
  "search_context.filters": ["pool", "free-parking"]  // This REPLACES the array
}

Example 3 - User compares hotels:
Input: "Compare the second and fourth hotels"
Output:
{
  "comparison_workspace.hotels_being_compared": ["H456", "H890"],
  "conversation_stage": "comparing"
}

Example 4 - User reveals preference:
Input: "I always avoid hotels near train stations, too noisy"
Output:
{
  "session_preferences.stated": ["Avoids hotels near train stations due to noise"]
}

Example 5 - Nothing changed:
Input: "Thanks!" / "Okay, got it"
Output:
{}

Now extract from the actual conversation turn above.
Return ONLY valid JSON, no markdown, no explanations:

Today's date: {current_date}

"""

    return SystemMessage(
        content=raw_prompt.format(
            current_date=datetime.date.today().isoformat()
        )
    )


