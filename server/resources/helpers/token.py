import jwt, os, json
from datetime import timedelta, datetime


config = {}
with open('../config.json') as config_file:
	config = json.load(config_file)

secret_key = os.environ[config['app_secret_key_variable']]

def decode_user(token):
    return jwt.decode(jwt = token, key = secret_key, algorithms = 'HS256')

def encode_user(user_id):
    return jwt.encode({
        'user_id': user_id,
        'exp' : datetime.now() + timedelta(minutes = 60)
    }, secret_key, algorithm = "HS256")