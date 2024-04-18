from flask_restful import Resource, request
from bson.objectid import ObjectId
from .helpers.masker import unmask_fields

class Users(Resource):
    def __init__(self):
        self.user_masker = {
            '_id': {'unmask': str, 'mask': ObjectId},
            'projects': {
                'unmask': lambda y: list(map(lambda x: str(x), y)),
                'mask': lambda y: list(map(lambda x: ObjectId(x), y))
            }
        }
        self.user_database = mongo_client[database].user

    def fetch_users(self, request_query):
        users = self.user_database.find(request_query, {'_id': 0, 'password': 0})
        return users if users else []

    def get(self):
        users = self.fetch_users(request.get_json())
        return {
            'success': True,
            'users': [unmask_fields(user, self.user_masker) for user in users]
        }, 200


from app import mongo_client, database
