from pydantic import BaseModel


class ChatMessageInput(BaseModel):
    message: str
    stress_score: int
    risk_level: str
    sleepHours: float
    screenTime: float
    stepCount: int
    aqi: int
    mood: str
    chat_history: str = ""


class StartChatInput(BaseModel):
    message: str
    stress_score: int
    risk_level: str
    sleepHours: float
    screenTime: float
    stepCount: int
    aqi: int
    mood: str
    chat_history: str = ""
    summary: str = ""


class EndChatInput(BaseModel):
    chat_history: str
    stress_score: int
    risk_level: str
