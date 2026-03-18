import datetime
import os
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
    AIMessage,
    BaseMessage
)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from database import get_db

from tools_updated import (
    searchProperties,
    compareProperties,
    checkRoomAvailability,
    getPropertyDetails,
    getRoomDetails,
    createBooking,
    cancelBooking,
    getGuestBookings
)

load_dotenv()

app = FastAPI(title="BhutanStay AI API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_store: Dict[str, List[BaseMessage]] = {}

# llm = ChatOpenAI(
#     model="gpt-4o",
#     temperature=0
# )

llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)
# llm = ChatGroq(
#     model="llama-3.3-70b-versatile",
#     temperature=0,
#     api_key=os.getenv("GROQ_API_KEY")
# )

tools = [
    searchProperties,
    compareProperties,
    checkRoomAvailability,
    getPropertyDetails,
    getRoomDetails,
    createBooking,
    cancelBooking,
    getGuestBookings
]


# Tool router dictionary
tools_map = {
    "searchProperties": searchProperties,
    "compareProperties": compareProperties,
    "checkRoomAvailability": checkRoomAvailability,
    "getPropertyDetails": getPropertyDetails,
    "getRoomDetails": getRoomDetails,
    "createBooking": createBooking,
    "cancelBooking": cancelBooking,
    "getGuestBookings": getGuestBookings
}
TOOL_DESCRIPTIONS = [

{
"name": "searchProperties",
"description": "Search for hotels based on location, price, rating and guest count",
"parameters": {
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "property_type": {"type": "string"},
        "minPrice": {"type": "number"},
        "maxPrice": {"type": "number"},
        "adults": {"type": "integer"},
        "children": {"type": "integer"},
        "rating": {"type": "number"}
    },
    "required": ["city"]
}
},

{
"name": "checkRoomAvailability",
"description": "Check if rooms are available for given dates",
"parameters": {
    "type": "object",
    "properties": {
        "property_id": {"type": "string"},
        "checkInDate": {"type": "string", "format": "date"},
        "checkOutDate": {"type": "string", "format": "date"},
        "adults": {"type": "integer"},
        "children": {"type": "integer"}
    },
    "required": ["property_id", "checkInDate", "checkOutDate"]
}
},

{
"name": "getPropertyDetails",
"description": "Get details about a specific hotel",
"parameters": {
    "type": "object",
    "properties": {
        "property_id": {"type": "string"}
    },
    "required": ["property_id"]
}
},

{
"name": "getRoomDetails",
"description": "Get information about a room",
"parameters": {
    "type": "object",
    "properties": {
        "room_id": {"type": "string"}
    },
    "required": ["room_id"]
}
},

{
"name": "createBooking",
"description": "Create a booking for a room",
"parameters": {
    "type": "object",
    "properties": {
        "guest_id": {"type": "string"},
        "property_id": {"type": "string"},
        "room_id": {"type": "string"},
        "check_in_date": {"type": "string", "format": "date"},
        "check_out_date": {"type": "string", "format": "date"},
        "adults": {"type": "integer"},
        "children": {"type": "integer"},
        "payment_method": {"type": "string"}
    },
    "required": [
        "guest_id",
        "property_id",
        "room_id",
        "check_in_date",
        "check_out_date"
    ]
}
},

{
"name": "cancelBooking",
"description": "Cancel a booking",
"parameters": {
    "type": "object",
    "properties": {
        "booking_id": {"type": "string"},
        "reason": {"type": "string"}
    },
    "required": ["booking_id"]
}
},

{
"name": "getGuestBookings",
"description": "Get all bookings for a guest",
"parameters": {
    "type": "object",
    "properties": {
        "guest_id": {"type": "string"}
    },
    "required": ["guest_id"]
}
}

]


def get_system_prompt():

    raw_prompt = """## Role
You are the **BhutStay Assistant**, an intelligent, professional, and warm hotel booking agent designed to provide a seamless travel experience.

## Objectives
1.  **Search Hotels:** Help users find accommodations based on location, budget, or preferences.
2.  **Check Availability:** Verify room status for specific dates.
3.  **View Details:** Provide comprehensive information about amenities and room types.
4.  **Manage Bookings:** Assist users in creating or canceling reservations efficiently.

## Core Rules
1.  **Data Integrity:** Always use provided tools to fetch real-time hotel data. Never hallucinate prices, availability, or property details.
2.  **No Results Policy:** If a tool returns no results, politely inform the user and suggest alternative criteria (e.g., different dates or a nearby location).
3.  **Tone & Voice:** Maintain a professional yet warm and welcoming "hospitality" tone.

## Formatting Standards (Strict)
To ensure clarity and scannability, you must follow these formatting rules for every response:

### 1. Structure & Hierarchy
* Use `##` for main sections and `###` for individual Property Names.
* Use horizontal rules (`---`) to separate different hotel options or distinct sections.

### 2. Information Display
* **Property Header:** Include the Star Rating and Address immediately under the property name.
    * *Example:* **⭐ 4.5 Stars** | 📍 *NewYork, USA*
* **Amenities:** Use bulleted lists for amenities to avoid dense text blocks.
* **Room Pricing:** When multiple room types are available, **always use a Markdown table**.

| Room Type | Price per Night | Capacity |
| :--- | :--- | :--- |
| **Standard** | $150.00 | 2 Guests |
| **Deluxe** | $250.00 | 2 Guests |

### 3. Clear Call-to-Action
Always conclude your response with a focused question or a clear next step to guide the user (e.g., "Would you like me to check the availability for these dates?").

Today's date: {current_date}
"""

    return SystemMessage(
        content=raw_prompt.format(
            current_date=datetime.date.today().isoformat()
        )
    )

def save_history_to_db(session_id: str, message: str, response: str):

    db = get_db()

    with db._engine.connect() as conn:

        conn.execute(
            text("""
            INSERT INTO chat_history(session_id, message, response)
            VALUES(:s, :m, :r)
            """),
            {
                "s": session_id,
                "m": message,
                "r": response
            }
        )

        conn.commit()
def extract_text_content(content) -> str:
    """
    Gemini returns content as a list of dicts like:
      [{'type': 'text', 'text': '...'}]
    OpenAI returns a plain string.
    This normalizes both to a plain string.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)

    return str(content)



class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    session_id: str

def run_agent_step(session_id: str, user_input: str) -> str:

    if session_id not in session_store:
        session_store[session_id] = [get_system_prompt()]

    messages = session_store[session_id]
    messages.append(HumanMessage(content=user_input))

    MAX_STEPS = 5
    step_count = 0
    final_response = ""
    
    # ✅ Track ALL tool calls made (not just the last one)
    tool_call_history = []
    same_tool_count = {}  # Count how many times each tool is called

    while step_count < MAX_STEPS:

        step_count += 1

        response = llm.invoke(messages, tools=TOOL_DESCRIPTIONS)

        normalized_content = extract_text_content(response.content)

        ai_message = AIMessage(
            content=normalized_content,
            tool_calls=response.tool_calls,
            id=response.id
        )

        messages.append(ai_message)

        # ✅ If no tool call → final answer
        if not response.tool_calls:
            final_response = normalized_content
            break

        # ✅ Check for excessive same-tool calls
        current_tool_name = response.tool_calls[0]["name"]
        same_tool_count[current_tool_name] = same_tool_count.get(current_tool_name, 0) + 1
        
        if same_tool_count[current_tool_name] >= 3:
            print(f"⚠️ Tool '{current_tool_name}' called {same_tool_count[current_tool_name]} times, breaking loop")
            break

        # Execute tools
        for tool_call in response.tool_calls:

            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            print(f"🔧 Agent calling tool: {tool_name}")
            print(f"   Arguments: {tool_args}")

            selected_tool = tools_map.get(tool_name)
            tool_output = "Tool not found"

            if selected_tool:
                try:
                    tool_output = selected_tool(**tool_args)
                except Exception as e:
                    tool_output = f"Tool execution error: {str(e)}"
                    print(f"❌ Error: {e}")

            print(f"   Result preview: {str(tool_output)[:200]}")

            tool_message = ToolMessage(
                tool_call_id=tool_call["id"],
                name=tool_name,
                content=str(tool_output)
            )

            messages.append(tool_message)

    # ✅ FALLBACK
    if not final_response:

        print("⚠️ No final response yet — forcing summary call without tools")

        messages.append(
            HumanMessage(
                content="Based on the tool results above, please provide a helpful response to the user. If no results were found, suggest alternatives."
            )
        )

        fallback_response = llm.invoke(messages)
        final_response = extract_text_content(fallback_response.content)
        messages.append(AIMessage(content=final_response))

    session_store[session_id] = messages

    return final_response

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):

    try:

        if not request.session_id:
            raise HTTPException(
                status_code=400,
                detail="Session ID required"
            )

        answer = run_agent_step(
            request.session_id,
            request.message
        )

        save_history_to_db(
            request.session_id,
            request.message,
            answer
        )

        return ChatResponse(
            session_id=request.session_id,
            response=answer
        )

    except Exception as e:

        print("Chat error:", e)

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )