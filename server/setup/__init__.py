from flask import Flask
from flask_restful import Api, request
import json
from connections.mongo import MongoManager
from connections.redis import RedisManager

config = {}
with open('../config.json') as config_file:
	config = json.load(config_file)

database = config['mongo']['database_name']

mongo_client = MongoManager().mongo_client
redis_client = RedisManager().redis_client

def create_app():
    app = Flask(__name__)
    api = Api(app)

    from resources.user import User
    api.add_resource(User, '/user', '/user/<string:user_id>', endpoint = 'user')

    from resources.task import Task
    api.add_resource(Task, '/task', '/task/<string:task_id>', endpoint = 'task')

    from resources.projects import Projects
    api.add_resource(Projects, '/projects', '/projects/<string:user_id>', endpoint = 'project')

    from resources.tasks import Tasks
    api.add_resource(Tasks, '/tasks', endpoint = 'tasks')

    @app.route('/login', methods = ['POST'])
    def login():
        body = request.get_json()
        access_token = User.get_access_token(body['username'], body['password'])
        if access_token:
            return {'success': True, 'access_token': access_token}, 200
        return {'success': False}, 404

    return app
