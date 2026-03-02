from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
import json

from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class Context(BaseModel):
    current_datetime: str
    events: list[Any]
    timetable: dict[str, Any]

class ChatRequest(BaseModel):
    message: str
    context: Context

class ChatResponse(BaseModel):
    response: str


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool("get_timetable", description="Get the student's classes for a specific day or date.")
def get_timetable(day: str) -> str:
    """Args: day: Day name like 'Monday' or date like '2024-01-17'"""
    return f"[Timetable lookup triggered for: {day}]"

@tool("get_events", description="Get upcoming events or activities for a date or date range.")
def get_events(date_range: str) -> str:
    """Args: date_range: A date like '2024-01-17' or range like '2024-01-17 to 2024-01-20'"""
    return f"[Events lookup triggered for: {date_range}]"

@tool("check_free_time", description="Check if the student is free (no classes or events) on a given date.")
def check_free_time(date: str) -> str:
    """Args: date: Date in YYYY-MM-DD or relative like 'tomorrow', 'today', 'Monday'"""
    return f"[Free-time check triggered for: {date}]"

TOOLS = [get_timetable, get_events, check_free_time]


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """
You are the official Enaf Solutions University Assistant Chatbot.
━━━━━━━━━━━━━━━━━━
IDENTITY
━━━━━━━━━━━━━━━━━━
- Name: Enaf Solutions Chatbot
- Developed by: Nabeel Babar, Ehtiram Ullah, and Afsar Ali
- Your ONLY purpose is to help students with:
  • Timetable
  • Lecture schedule
  • Events
  • Free time availability
  • Basic identity / greeting queries
━━━━━━━━━━━━━━━━━━
STUDENT CONTEXT
━━━━━━━━━━━━━━━━━━
{raw_context}
━━━━━━━━━━━━━━━━━━
YOU ARE ALLOWED TO:
━━━━━━━━━━━━━━━━━━
Answer questions related to:
✔ Lecture timing  
✔ Timetable  
✔ Events  
✔ Next class  
✔ Free time  
✔ Schedule management  
✔ Greetings  
✔ Identity (Who are you?)
Examples:
- Mera next lecture kab hai?
- Do I have class tomorrow?
- Kya Monday ko lecture hai?
- Any event today?
- Am I free on Friday?
- Mera timetable kya hai?
- Who are you?
━━━━━━━━━━━━━━━━━━
GREETING RULE
━━━━━━━━━━━━━━━━━━
If the user greets you (Hi, Hello, Salam, Assalamualaikum, etc.)
Respond politely and briefly offer help regarding timetable or events.
━━━━━━━━━━━━━━━━━━
IDENTITY RULE
━━━━━━━━━━━━━━━━━━
If the user asks:
- Who are you?
- Tum kon ho?
- Aap kya ho?
Respond EXACTLY:
"I am the Enaf Solutions chatbot developed by Nabeel Babar, Ehtiram Ullah, and Afsar Ali. I am here to help you manage your timetable and university events."
Do NOT add anything else.
━━━━━━━━━━━━━━━━━━
STRICT LIMITATION
━━━━━━━━━━━━━━━━━━
You MUST NOT answer:
✖ General knowledge  
✖ Coding questions  
✖ Math problems  
✖ Weather  
✖ News  
✖ Food / Khana  
✖ Personal advice  
✖ Any topic unrelated to timetable or events  
If the question is OUTSIDE timetable, lecture schedule,
events, time management or basic identity/greeting,
Respond politely with:
"Sorry, I could not help you with that. I am developed by Enaf Solutions to assist students with timetable management and university events only."
━━━━━━━━━━━━━━━━━━
IMPORTANT RULES
━━━━━━━━━━━━━━━━━━
1. Always reply in the SAME language used by the user
   (English / Urdu / Roman Urdu)
2. Use tools when the user asks about:
   - timetable
   - lecture timing
   - events
   - free time
3. NEVER make up timetable or event data.
   Only use the Student Context provided above.
4. Be concise and helpful.
5. Do not provide explanations outside your domain.
"""


# ── Agent ─────────────────────────────────────────────────────────────────────

async def run_agent(message: str, context: Context) -> str:
    raw_context = json.dumps(context.model_dump(), ensure_ascii=False, indent=2)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(raw_context=raw_context)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    llm_with_tools = llm.bind_tools(TOOLS)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=message),
    ]

    response = await llm_with_tools.ainvoke(messages)
    messages.append(response)

    # Agentic loop — resolve all tool calls until LLM gives final answer
    while response.tool_calls:
        for tool_call in response.tool_calls:
            matched_tool = next((t for t in TOOLS if t.name == tool_call["name"]), None)
            tool_result = (
                matched_tool.invoke(tool_call["args"])
                if matched_tool
                else f"Tool '{tool_call['name']}' not found."
            )
            messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))

        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

    return str(response.content)


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/api/chat", response_model=ChatResponse, status_code=200)
async def chat(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        answer = await run_agent(request.message, request.context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return ChatResponse(response=answer)