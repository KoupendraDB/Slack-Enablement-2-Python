from flask_restful import Resource, request
from datetime import datetime, date
from bson.objectid import ObjectId
from .helpers.masker import unmask_fields, mask_fields

class Users(Resource):
    def __init__(self):
        self.user_masker = {
            '_id': {'unmask': str, 'mask': ObjectId}
        }
        self.user_database = mongo_client[database].user

    def fetch_users(self, request_query):
        query = mask_fields(request_query, self.user_masker)
        print(request_query)
        print(query)
        users = self.user_database.find(query)
        return users if users else []

    def get(self):
        users = self.fetch_users(request.get_json())
        return {
            'success': True,
            'users': [unmask_fields(user, self.user_masker) for user in users]
            }, 200


from app import mongo_client, database
