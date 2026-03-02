import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import List
import json
from dotenv import load_dotenv

load_dotenv()

# ------------------ Pydantic Schema ------------------

class TimetableEntry(BaseModel):
    day: str = Field(...)
    course_code: str = Field(...)
    course_name: str = Field(...)
    faculty: str = Field(...)
    session_type: str = Field(...)
    mode: str = Field(...)
    start_time: str = Field(...)
    end_time: str = Field(...)
    room: str = Field(...)

class Timetable(BaseModel):
    timetable: List[TimetableEntry]


# ------------------ Gemini LLM ------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

# Structured Output Parser
structured_llm = llm.with_structured_output(Timetable)


# ------------------ Prompt ------------------

PROMPT = """
Extract the timetable from the image and return ONLY valid JSON.

Output format:
{
  "timetable": [
    {
      "day": "string",
      "course_code": "string",
      "course_name": "string",
      "faculty": "string",
      "session_type": "string",
      "mode": "string",
      "start_time": "string",
      "end_time": "string",
      "room": "string"
    }
  ]
}

Rules:
- Do not add explanations.
- Do not add markdown.
- Do not add extra fields.
- Return only valid JSON.
"""


# ------------------ Main Function ------------------

def extract_timetable_from_image(image_bytes: bytes):

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    message = HumanMessage(
        content=[
            {"type": "text", "text": PROMPT},
            {
                "type": "image_url",
                "image_url": f"data:image/png;base64,{encoded_image}"
            }
        ]
    )

    response = structured_llm.invoke([message])

    return json.loads(response.json())