from typing import Dict, List
from langchain_core.messages import BaseMessage

session_store: Dict[str, List[BaseMessage]] = {}