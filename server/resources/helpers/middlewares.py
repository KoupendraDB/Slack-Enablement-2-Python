from functools import wraps
from flask_restful import request
from datetime import timedelta
from bson.objectid import ObjectId
from .token import *
from .cache import RedisCacheController
from app import redis_client, mongo_client, database

cache_time = timedelta(hours = 1)

cache_masker = {'_id': {'unmask': str, 'mask': ObjectId}}

token_cache_controller = RedisCacheController(redis_client, cache_masker, cache_time)

user_database = mongo_client[database].user

def fetch_user_by_id(user_id):
    key_template = 'token_user_id:{}'
    cached_response = token_cache_controller.get_cache(key_template, user_id)
    if cached_response:
        return cached_response
    query, options = {'_id': ObjectId(user_id)}, {'password': 0}
    user = user_database.find_one(query, options)
    if user:
        token_cache_controller.set_cache(key_template, user_id, user)
    return user


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'bearer-token' in request.headers:
            token = request.headers['bearer-token']
        if not token:
            return {'message' : 'Token is missing!'}, 401
  
        try:
            data = decode_user(token)
            current_user = fetch_user_by_id(data['user_id'])
        except Exception as e:
            print(e)
            return {'message' : 'Invalid token!'}, 401
        
        kwargs['user'] = current_user
        return  f(*args, **kwargs)

    return decorated
