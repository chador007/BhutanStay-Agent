import datetime
import os
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_core.messages import (
    HumanMessage, SystemMessage, ToolMessage, AIMessage, BaseMessage, message_to_dict, messages_from_dict
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from fastapi.middleware.cors import CORSMiddleware
from database import get_db

from tools import search_inventory, manage_reservations
from sqlalchemy import text
import asyncpg

load_dotenv()

app = FastAPI(title="BhutanStay AI API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)


session_store: Dict[str, List[BaseMessage]] = {}
# llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
# llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)

llm = ChatOpenAI(model="gpt-4o", temperature=0)

tools = [search_inventory, manage_reservations]
llm_with_tools = llm.bind_tools(tools)

tools_map = {
    "search_inventory": search_inventory,
    "manage_reservations": manage_reservations,
}

def get_system_prompt():
    raw_system_prompt = """
    You are the "BhutStay Assistant," an expert hotel management agent for a luxury hotel chain.
    Your primary goal is to assist users with booking inquiries, reservation management, and room information with efficiency and the warmth of Bhutanese hospitality.
    
    ### 🛠️ YOUR CAPABILITIES
    You have access to specific tools to interact with the hotel database.
    1. ALWAYS use the provided tools to fetch real-time data.
    2. NEVER guess or hallucinate booking details.
    3. If a tool returns "No results," politely inform the user.

    ### 🚨 CRITICAL RULES
    - **Privacy:** Never reveal personal details unless authenticated.
    - **Booking IDs:** A valid code looks like 'BK-2024-xxxxxx'.
    - **Dates:** Always check the current date ({current_date}).
    - **Tone:** Professional, calm, and welcoming.
    """
    return SystemMessage(content=raw_system_prompt.format(
        current_date=datetime.date.today().isoformat()
    ))



def save_history_to_db(session_id: str, message: str, response: str):
    db = get_db()
    with db._engine.connect() as connection:
            connection.execute(
                text("INSERT INTO chat_history (session_id, message, response) VALUES (:s, :m, :r)"),
                {"s": session_id, "m": message, "r": response}
            )
            connection.commit() 

# ─── 4. API Data Models ───
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

def run_agent_step(session_id: str, user_input: str) -> str:
    """
    Retrieves history, runs the LLM loop, executes tools, and saves history.
    """
    
    if session_id not in session_store:
        session_store[session_id] = [get_system_prompt()]
    messages = session_store[session_id]
    messages.append(HumanMessage(content=user_input))

    MAX_STEPS = 5
    step_count = 0

    final_response = ""

    while step_count < MAX_STEPS:
        step_count += 1
        
        # Invoke LLM
        response = llm_with_tools.invoke(messages)
        clean_response = AIMessage(
            content=response.content,
            tool_calls=response.tool_calls, 
            id=response.id                  
        )
    
        print(clean_response)
        messages.append(clean_response)

        print("Message list:")
        print(messages)
    
        # Check if LLM wants to stop (no tool calls)
        if not response.tool_calls:
            final_response = response.content
            break

        # If LLM wants to use tools, execute them
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Find the tool
            selected_tool = tools_map.get(tool_name)
            tool_output = "Error: Tool not found"
            
            if selected_tool:
                try:
                    # Run the tool
                    print(f"🔧 API executing: {tool_name} with {tool_args}")
                    raw_result = selected_tool.invoke(tool_args)
                    tool_output = str(raw_result)
                except Exception as e:
                    tool_output = f"Tool Execution Error: {str(e)}"
            
            # Append Tool Message back to history

            tool_message = ToolMessage(
                tool_call_id=tool_call["id"], 
                content=tool_output,
                name=tool_name)
            
            print("Tool Message:")
            print(tool_message)
            messages.append(tool_message)

    # 3. Update Session Store
    session_store[session_id] = messages

    
    return final_response
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        if not request.session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")

        answer = run_agent_step(request.session_id, request.message)

        # save_history_to_db(request.session_id, request.message, answer)

        return ChatResponse(
            session_id=request.session_id, 
            response=answer
        )
    except Exception as e:
        # Log the error to your terminal so you can see what went wrong
        print(f"Error in chat_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))