from pydantic import BaseModel


class ChatInput(BaseModel):
    message: str
    stress_score: int
    risk_level: str
    avg_sleep: float
    screen_time: float
    activity: str
    aqi: int
    mood: str
    chat_history: str = ""
    summary: str = ""


class EndChatInput(BaseModel):
    chat_history: str
    stress_score: int
    risk_level: str
