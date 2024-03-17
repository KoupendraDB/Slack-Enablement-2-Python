from flask_restful import Resource, request
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from .helpers.cache import RedisCacheController
from .helpers.token import encode_user

class User(Resource):
    def __init__(self):
        self.cache_time = timedelta(minutes = 1)
        self.cache_masker = {'_id': {'unmask': str, 'mask': ObjectId}}
        self.user_cache_controller = RedisCacheController(redis_client, self.cache_masker, self.cache_time)
        self.user_database = mongo_client[database].user

    def fetch_user(self, key_template = None, key = None, query = {}, options = {}):
        if key_template:
            cached_response = self.user_cache_controller.get_cache(key_template, key)
            if cached_response:
                return cached_response
        user = self.user_database.find_one(query, options)
        if user and key_template:
            self.user_cache_controller.set_cache(key_template, key, user)
        return user

    def fetch_user_by_id(self, user_id):
        key_template = 'user_id:{}'
        query, options = {'_id': ObjectId(user_id)}, {'_id': 0, 'password': 0}
        return self.fetch_user(key_template, user_id, query, options)

    def fetch_user_by_username(self, username):
        key_template = 'username:{}'
        query, options = {'username': username}, {'password': 0}
        return self.fetch_user(key_template, username, query, options)
    
    @classmethod
    def get_access_token(cls, username, password):
        query = {'username': username}
        user = mongo_client[database].user.find_one(query)
        if user:
            is_correct_password = False
            if config['enable_password_hashing']:
                is_correct_password = check_password_hash(user['password'], password)
            else:
                is_correct_password = user['password'] == password
            if is_correct_password:
                token = encode_user(str(user['_id']))
                return token
        return None


    def get(self, user_id):
        user = self.fetch_user_by_id(user_id)
        if user:
            return {'success': True, 'user': user}, 200
        return {'success': False}, 404

    def post(self):
        user_request = request.get_json()
        user = self.fetch_user_by_username(user_request['username'])
        if user:
            return {'success': False}, 409
        if config['enable_password_hashing']:
            user_request['password'] = generate_password_hash(user_request['password'], 'pbkdf2')
        insert_result = self.user_database.insert_one(user_request)
        if insert_result and insert_result.inserted_id:
            result = {'success': True, 'user_id': str(insert_result.inserted_id)}, 201
            return result
        return {'success': False}, 400

from app import mongo_client, redis_client, database, config