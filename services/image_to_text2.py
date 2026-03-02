import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import List
import json

# ------------------ Pydantic Schema ------------------

class TimetableEntry(BaseModel):
    day: str
    course_code: str
    course_name: str
    faculty: str
    session_type: str
    mode: str
    start_time: str
    end_time: str
    room: str

class Timetable(BaseModel):
    timetable: List[TimetableEntry]


# ------------------ Gemini LLM ------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

structured_llm = llm.with_structured_output(Timetable)


# ------------------ Prompt ------------------

PROMPT = """
Multiple timetable images are provided.

Combine all timetable data from ALL images into one unified JSON.

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
- Combine timetable data from all images.
- Do not repeat duplicate entries.
- Do not add explanations.
- Do not add markdown.
- Do not add extra fields.
- Return only valid JSON.
"""


# ------------------ Multi Image Function ------------------

def extract_timetable_from_multiple_images(image_bytes_list: List[bytes]):

    image_contents = []

    for img in image_bytes_list:
        encoded = base64.b64encode(img).decode("utf-8")
        image_contents.append({
            "type": "image_url",
            "image_url": f"data:image/png;base64,{encoded}"
        })

    message = HumanMessage(
        content=[
            {"type": "text", "text": PROMPT},
            *image_contents
        ]
    )

    response = structured_llm.invoke([message])

    return json.loads(response.json())