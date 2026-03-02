from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
import datetime

# ----------------------------
# Models
# ----------------------------

class ChatRequest(BaseModel):
    user_query: str
    timetable_data: List[Dict[str, Any]]
    assignment_quiz_data: List[Dict[str, Any]]


class ChatResponse(BaseModel):
    response: str
    source: str  # "timetable", "assignment_quiz", or "general"


# ----------------------------
# LLM
# ----------------------------

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)


# ----------------------------
# Tools
# ----------------------------

@tool
def get_timetable(query: str, timetable_data: List[Dict[str, Any]]) -> str:
    """
    Get the student's class schedule.
    Use this tool when the user asks about:
    - Today's classes or any specific day's classes
    - Next class, upcoming class, or current class
    - Class timings, rooms, or subjects

    Args:
        query: The user's original question.
        timetable_data: List of class entries with fields like day, subject, start_time, end_time, room.
    """
    now = datetime.datetime.now()
    today = now.strftime("%A")

    # Filter today's classes
    todays_classes = [
        cls for cls in timetable_data
        if cls.get("day", "").strip().capitalize() == today
    ]

    if not todays_classes:
        return f"No classes found for today ({today})."

    # Sort by start_time
    def parse_time(t: str):
        for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p"):
            try:
                return datetime.datetime.strptime(t, fmt)
            except ValueError:
                continue
        return datetime.datetime.min

    sorted_classes = sorted(todays_classes, key=lambda x: parse_time(x.get("start_time", "00:00")))

    # Find next upcoming class
    for cls in sorted_classes:
        class_time = parse_time(cls.get("start_time", "00:00"))
        if class_time.replace(year=now.year, month=now.month, day=now.day) > now:
            return (
                f"Your next class is **{cls.get('subject', 'Unknown')}** "
                f"at {cls.get('start_time')} in room {cls.get('room', 'TBD')}."
            )

    # All classes done for the day
    class_list = "\n".join(
        f"- {c.get('subject')} at {c.get('start_time')} (Room: {c.get('room', 'TBD')})"
        for c in sorted_classes
    )
    return f"All classes for today ({today}) are done. Today's schedule was:\n{class_list}"


@tool
def get_quiz_and_assignments(query: str, assignment_quiz_data: List[Dict[str, Any]]) -> str:
    """
    Get upcoming assignments and quizzes.
    Use this tool when the user asks about:
    - Upcoming assignments, quizzes, or tests
    - Due dates or deadlines
    - Pending tasks or submissions

    Args:
        query: The user's original question.
        assignment_quiz_data: List of items with fields like type, title, due_date, subject, description.
    """
    if not assignment_quiz_data:
        return "No upcoming assignments or quizzes found."

    now = datetime.datetime.now().date()

    # Filter only assignments and quizzes
    relevant = [
        item for item in assignment_quiz_data
        if item.get("type", "").lower() in ["assignment", "quiz"]
    ]

    if not relevant:
        return "No assignments or quizzes found in your data."

    # Sort by due_date if available
    def parse_date(d: str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.datetime.strptime(d, fmt).date()
            except (ValueError, TypeError):
                continue
        return datetime.date.max

    sorted_items = sorted(relevant, key=lambda x: parse_date(x.get("due_date", "")))

    lines = []
    for item in sorted_items:
        due = item.get("due_date", "Unknown date")
        title = item.get("title", "Untitled")
        subject = item.get("subject", "")
        item_type = item.get("type", "Task").capitalize()

        due_date = parse_date(due)
        days_left = (due_date - now).days if due_date != datetime.date.max else None

        urgency = ""
        if days_left is not None:
            if days_left < 0:
                urgency = " *(overdue)*"
            elif days_left == 0:
                urgency = " *(due today!)*"
            elif days_left == 1:
                urgency = " *(due tomorrow)*"
            else:
                urgency = f" *({days_left} days left)*"

        subject_str = f" [{subject}]" if subject else ""
        lines.append(f"- **{item_type}**: {title}{subject_str} — Due: {due}{urgency}")

    return "Upcoming assignments and quizzes:\n" + "\n".join(lines)


# ----------------------------
# System Prompt
# ----------------------------

SYSTEM_PROMPT = (
    "NABEEL BABAR, EHTIRAM ULLAH, AFSAR ALI are your creators, that are the founder of ENAF SOLUTIONS."
    "You are a smart and helpful academic assistant for students at UMT (University of Management and Technology). "
    "You have access to the student's timetable and upcoming assignments/quizzes through tools. "
    "When a student asks about their schedule, classes, or next class — use the get_timetable tool. "
    "When a student asks about assignments, quizzes, deadlines, or pending tasks — use the get_quiz_and_assignments tool. "
    "Always pass the full timetable_data or assignment_quiz_data from context into the tool. "
    "Be concise, friendly, and accurate. If information is unavailable, say so clearly."
)


# ----------------------------
# Agent (LangGraph ReAct)
# ----------------------------

agent = create_react_agent(
    model=model,
    tools=[get_timetable, get_quiz_and_assignments],
    prompt=SYSTEM_PROMPT,
)


# ----------------------------
# Router
# ----------------------------

router = APIRouter(prefix="/chat", tags=["Chatbot"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Build message with full context embedded
        user_message = HumanMessage(
            content=(
                f"User query: {request.user_query}\n\n"
                f"Timetable data: {request.timetable_data}\n\n"
                f"Assignment/Quiz data: {request.assignment_quiz_data}"
            )
        )

        # Invoke the ReAct agent
        result = await agent.ainvoke({"messages": [user_message]})

        # Extract final response text
        final_message = result["messages"][-1]
        response_text = final_message.content

        # Determine which tool was used by inspecting message history
        tool_names_used = [
            msg.name
            for msg in result["messages"]
            if hasattr(msg, "name") and msg.name
        ]

        if "get_timetable" in tool_names_used:
            source = "timetable"
        elif "get_quiz_and_assignments" in tool_names_used:
            source = "assignment_quiz"
        else:
            source = "general"

        return ChatResponse(response=response_text, source=source)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))