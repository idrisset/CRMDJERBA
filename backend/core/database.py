from dotenv import load_dotenv
load_dotenv()

import os
import logging
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

mongo_url = os.environ['MONGO_URL']
if 'mongodb+srv' in mongo_url or 'mongodb.net' in mongo_url:
    client = AsyncIOMotorClient(mongo_url, tlsCAFile=certifi.where())
else:
    client = AsyncIOMotorClient(mongo_url)

db = client[os.environ['DB_NAME']]

SOFT_DELETE_FILTER = {"deleted_at": None}
