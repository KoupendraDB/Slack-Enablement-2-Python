from flask import Flask
from flask_restful import Api, request
import json
from connections.mongo import mongo_client
from connections.redis import redis_client

config = {}
with open('../config.json') as config_file:
	config = json.load(config_file)

database = config['mongo']['database_name']

try:
	mongo_client[database].command('ping')
	print("[+] Successfully connected to MongoDB!")
	redis_client.ping()
	print("[+] Successfully connected to Redis!")
except Exception as e:
	print(e)
	exit(1)

app = Flask(__name__)
api = Api(app)

from resources.user import User
api.add_resource(User, '/user', '/user/<string:user_id>', endpoint = 'user')

@app.route('/login', methods = ['POST'])
def login():
    body = request.get_json()
    access_token = User.get_access_token(body['username'], body['password'])
    if access_token:
        return {'success': True, 'access_token': access_token}, 200
    return {'success': False}, 404

if __name__ == '__main__':
	app.run(
		port = config['server_port'],
		debug = True
	)