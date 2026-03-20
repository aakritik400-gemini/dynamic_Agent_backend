from pydantic import BaseModel
from typing import List, Optional

class AgentCreate(BaseModel):
    name: str
    prompt: str
    type: str
    data_file: Optional[str] = None

class HandoffCreate(BaseModel):
    child_agent_ids: List[int]

class AskRequest(BaseModel):
    question: str