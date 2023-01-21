from pydantic import BaseModel

def check_value(cls, value: int) -> int: ...

class TaskRequest(BaseModel):
    request_value: int
    dummy_value: int

class TaskResponse(BaseModel):
    request_value: int
    response_value: int
    is_success: bool
