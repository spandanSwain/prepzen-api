import os
import json
from google import genai
from dotenv import load_dotenv
from database.Interviews.models import InterviewComplete
from database.DTOs.user_interview_question import UserInterviewDTO
from database.DTOs.evaluation_metrics import EvaluationMetrics

# Load the variables from .env into the system environment
load_dotenv()
 
# Fetch the key using os.getenv
api_key = os.getenv("GEMINI_API_KEY")
 
# Initialize the client
client = genai.Client(api_key=api_key)

def getDataFromGemini(user: UserInterviewDTO):
    # Use a system-style instruction to enforce JSON formatting
    prompt = (f"""Act as a Senior {user.domain} Interviewer for a {user.proficiency} level candidate.
        Generate exactly {user.numQuestions} interview questions on the topic: {user.topic}.
        Context: The candidate ({user.username}) has a current performance level of {user.performanceLevel}.
        Rules:
        1. Return the response ONLY as a JSON object with a key 'questions' containing an array of strings.
        2. Do not include any introductory or concluding text.
        The questions are going to be read by a voice assistant so do not use "/" or "*" or any other special characters which might break the voice assistant.
        Return the questions formatted like this:
        ["Question 1", "Question 2", "Question 3"]
        """
    )
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    try:
        json_data = json.loads(response.text)
        return json_data
    except json.JSONDecodeError:
        return {"questions": [response.text]}
    


def evaluateUserBasedOnTranscribe(data: InterviewComplete):
    system_instruction = "You are a professional interviewer analyzing a mock interview. Evaluate the candidate strictly based on the provided transcript."
    
    prompt = f"""
    Analyze the following interview transcript:
    {data.transcribe}

    Task:
    Provide a score (0-100) for each category and a critical evaluation. 
    Do not be lenient; point out mistakes or gaps in knowledge clearly.

    Evaluation Criteria:
    - communication_skills: (0-100)
    - technical_knowledge: (0-100)
    - problem_solving: (0-100)
    - cultural_role_fit: (0-100)
    - confidence_clarity: (0-100)
    
    New Required Formatting:
    1. detailed_feedback: This must be exactly ONE of these three strings: "Good", "Average", or "Bad" based on the overall performance.
    2. areas_for_improvement: This must be a JSON array (list) of strings containing specific, actionable critiques.

    Return the response ONLY as a JSON object.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", # or "gemini-2.5-flash"
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": EvaluationMetrics 
            }
        )
        
        # Parse the string response into a Python dictionary
        evaluation_json = json.loads(response.text)
        return evaluation_json

    except Exception as e:
        return {
            "error": "Failed to generate evaluation",
            "details": str(e)
        }