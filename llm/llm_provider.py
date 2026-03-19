from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm():

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0
    )