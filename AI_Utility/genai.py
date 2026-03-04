from database.DTOs.user_interview_question import UserInterviewDTO
import os
import json
from dotenv import load_dotenv
from google import genai
 
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
        model="gemini-3-flash-preview",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    try:
        json_data = json.loads(response.text)
        return json_data
    except json.JSONDecodeError:
        return {"questions": [response.text]}