import os
from dotenv import load_dotenv
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

load_dotenv()


uri = os.getenv("MONGO_URL")
client = MongoClient(uri, tls=True,
    tlsAllowInvalidCertificates=True, server_api=ServerApi('1'))

db = client.prepzen

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))