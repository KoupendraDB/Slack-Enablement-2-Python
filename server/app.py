from flask import Flask
from flask_restful import Api
import json

config = {}
with open('../config.json') as config_file:
	config = json.load(config_file)

database = config['mongo']['database_name']

app = Flask(__name__)
api = Api(app)

if __name__ == '__main__':
	from resources.project import project_blueprint
	app.register_blueprint(project_blueprint)

	from resources.user import user_blueprint
	app.register_blueprint(user_blueprint)

	from resources.users import users_blueprint
	app.register_blueprint(users_blueprint)

	from resources.task import task_blueprint
	app.register_blueprint(task_blueprint)

	from resources.tasks import tasks_blueprint
	app.register_blueprint(tasks_blueprint)

	app.run(
		host = '0.0.0.0',
		port = config['server_port'],
		debug = True
	)