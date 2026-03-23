from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

vllm_url = "http://172.19.9.235:5000/v1" 

def get_llm():

    # return ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash-lite",
    #     temperature=0
    # )
    return ChatOpenAI(
        model = "Qwen/Qwen2.5-7B-Instruct",
        openai_api_key="EMPTY",
        base_url=vllm_url,
        temperature=0
    )