import os
from dotenv import load_dotenv
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

load_dotenv()


uri = os.getenv("MONGO_URL")
client = MongoClient(uri, server_api=ServerApi('1'))

db = client.prepzen