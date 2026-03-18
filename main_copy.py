import datetime
import os
import json

from dotenv import load_dotenv
from langchain_core.messages import (HumanMessage, 
                                     SystemMessage, ToolMessage)
from langchain_openai import ChatOpenAI

from tools import find_bookings, search_inventory, manage_reservations

load_dotenv()

raw_system_prompt = """
You are the "BhutStay Assistant," an expert hotel management agent for a luxury hotel chain..

Your primary goal is to assist users with booking inquiries, reservation management, and room information with efficiency and the warmth of Bhutanese hospitality.

### 🛠️ YOUR CAPABILITIES
You have access to specific tools to interact with the hotel database.
1. ALWAYS use the provided tools to fetch real-time data.
2. NEVER guess or hallucinate booking details, room availability, or prices.
3. If a tool returns "No results," politely inform the user and ask for correct details (like a different booking ID).

### 🚨 CRITICAL RULES
- **Privacy:** Never reveal a guest's personal details (like phone number or full email) unless they have authenticated themselves or provided their Guest ID.
- **Booking IDs:** A valid booking code looks like 'BK-2024-xxxxxx'. If a user provides a wrong format, kindly correct them.
- **Dates:** Always check the current date before making decisions about "upcoming" or "past" bookings.
- **Tone:** Be professional, calm, and welcoming.

### 🧠 REASONING PROCESS
1. Understand the user's intent (e.g., "Find my booking").
2. Check if you have all required parameters (e.g., Do you have the Booking ID?).
3. If parameters are missing, ASK the user for them.
4. Call the appropriate tool.
5. Synthesize the tool output into a natural language response.

Current Date: {current_date}
"""

formatted_system_prompt = raw_system_prompt.format(
    current_date=datetime.date.today().isoformat()
)

llm = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [find_bookings, search_inventory, manage_reservations]
llm_with_tools = llm.bind_tools(tools)

tools_map = {
    "find_bookings": find_bookings,
    "search_inventory": search_inventory,
    "manage_reservations": manage_reservations
}

query = "Find me the booking details with booking code BK-2024-001010. "
print(f"👤 USER: {query}")
messages = [
    SystemMessage(content=formatted_system_prompt),
    HumanMessage(content=query)
]
response = llm_with_tools.invoke(messages)

if response.tool_calls:
    messages.append(response)

    for tool_call in response.tool_calls:
        tool_name = tool_call["name"].lower()
        print(f"🤖 Agent wants to use tool: {tool_name}")
        
        selected_tool = tools_map.get(tool_name)
        
        if selected_tool:
            raw_result = selected_tool.invoke(tool_call["args"])
            tool_output = str(raw_result)
        else:
            tool_output = f"Error: Tool '{tool_name}' is not recognized."

        messages.append(ToolMessage(
            tool_call_id=tool_call["id"], 
            content=tool_output
        ))
    final_response = llm_with_tools.invoke(messages)
    
    print("\n✅ AGENT RESPONSE:")
    print(final_response.content)

else:
    print(f"Agent: {response.content}")