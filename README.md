# Prepzen API
PrepZen API is a backend service built with FastAPI and MongoDB. It provides endpoints for managing students, domains, interviews, quizzes, and learning paths.

## Tech Stack
Python 3.9+
FastAPI
MongoDB
PyMongo / Motor
BSON

## Setup and Run

Clone the repository:
git clone https://github.com/spandanSwain/prepzen-api.git
cd prepzen-api

Create a virtual environment:
python -m venv venv
source venv/bin/activate    # Linux/Mac
.venv/Scripts/activate      # Windows

Install dependencies:
pip install -r requirements.txt

Configure environment:
Update your MongoDB connection string in configurations/db.py or .env
Ensure collections (users, domain, Interviews, quiz, learning_path) exist in your database

Run the application:
python -m uvicorn main:app --reload

The server will be available at http://127.0.0.1:8000
Swagger UI for testing is available at http://127.0.0.1:8000/docs
Hosted version of the project is available at https://prepzen-api.onrender.com/docs

## .env Setup

Create a `.env` file in the project root and add your keys:

```env
MONGO_URL=mongodb://localhost:27017/prepzen
GEMINI_API_KEY=your-gemini-api-key-here
SECRET_KEY=auth-jwt-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30