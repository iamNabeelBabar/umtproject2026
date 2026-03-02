# from langchain_openai import ChatOpenAI
# from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from typing import Any, Dict, List

# import datetime
# import json

# from langchain.tools import tool
# from langchain.agents import create_agent




# #get current time and date
# current_time = datetime.datetime.now().isoformat()
# current_date = datetime.datetime.now().date().isoformat()


# #define model
# model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)



# #define ChatResponse
# class ChatResponse(BaseModel):
#     resources: str
#     timetable_data: List[Dict]
#     assignment_quiz_data: List[Dict]
    
    

# #define tools 

# @tool
# def get_timetable(query, timetable_data) -> str:
#     """
#     Get the student's classes for a specific day or date.
    
#     **Args:**
#     query: The user's original question or request that triggered this tool.
#     timetable_data: The relevant timetable information extracted from the user's context, which may include class names, times, and locations.
    
#     """
    
#     return f"[Timetable lookup triggered for: {timetable_data}] for query: {query}"


# @tool
# def get_quiz_and_assignments(query, assignment_quiz_data) -> str:
#     """
#     Get upcoming events or activities for a date or date range.
    
#     **Args:**
#     query: The user's original question or request that triggered this tool.
#     assignment_quiz_data: The relevant assignment and quiz information extracted from the user's context, which may include due dates, titles, and descriptions.
    
#     """
    
#     return f"[Events lookup triggered for: {assignment_quiz_data}] for query: {query}"



# agent = create_agent(
#     tools=[get_timetable, get_quiz_and_assignments],
#     llm=model,
#     system_message="You are a helpful assistant for students at UMT. You have access to the student's timetable and upcoming assignments/quizzes. Use the tools provided to answer the student's questions about their schedule and tasks. Always provide clear and concise responses based on the information available."
# )

  

# router = APIRouter(prefix="/chat", tags=["Chatbot"])



# #get the timetable , assignments and quizzes from the context and pass it to the agent to answer the user's query
