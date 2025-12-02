from pymongo import MongoClient
import os

_global_client = None
_global_db = None

def init_db():
    global _global_client, _global_db
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME")

    if not mongo_uri or not db_name:
        raise RuntimeError("Missing MONGO_URI or DB_NAME environment variables")

    _global_client = MongoClient(mongo_uri)
    _global_db = _global_client[db_name]

def close_db():
    global _global_client
    if _global_client:
        _global_client.close()
        _global_client = None

def get_collection(collection_name: str):
    if _global_db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _global_db[collection_name]

class DBHandler:
    def __init__(self, collection_name: str):
        global _global_db
        if _global_db is None:
            init_db()
        self.collection = _global_db[collection_name]

    def insert_document(self, document: dict) -> str:
        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    def find_document(self, query: dict) -> dict:
        return self.collection.find_one(query)
    
    def find_documents(self, query: dict) -> list:
        return list(self.collection.find(query))

    def update_document(self, query: dict, update_values: dict) -> int:
        result = self.collection.update_one(query, {'$set': update_values})
        return result.modified_count

    def delete_document(self, query: dict) -> int:
        result = self.collection.delete_one(query)
        return result.deleted_count
