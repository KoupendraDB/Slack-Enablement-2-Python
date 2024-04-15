from flask_restful import Resource, request
from datetime import datetime, date
from bson.objectid import ObjectId
from .helpers.masker import unmask_fields

class Users(Resource):
    def __init__(self):
        self.user_masker = {
            '_id': {'unmask': str, 'mask': ObjectId}
        }
        self.user_database = mongo_client[database].user

    def fetch_users(self, request_query):
        query = {'name': {'$regex': request_query.get('name', '')}}
        if request_query.get('role', None):
            query['role'] = request_query['role']
        users = self.user_database.find(query)
        return users if users else []

    def get(self):
        users = self.fetch_users(request.args.to_dict())
        return {
            'success': True,
            'users': [unmask_fields(user, self.user_masker) for user in users]
            }, 200


from app import mongo_client, database
