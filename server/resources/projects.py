from flask_restful import Resource, request
from datetime import timedelta
from bson.objectid import ObjectId
from .helpers.middlewares import token_required
from .helpers.masker import unmask_fields

class Projects(Resource):
    def __init__(self):
        self.cache_time = timedelta(minutes = 30)
        self.project_masker = {
            '_id': {'unmask': str, 'mask': ObjectId}
        }
        self.project_database = mongo_client[database].project

    def fetch_user_projects(self, query = {}, options = {}):
        projects = self.project_database.find(query, options)
        projects = [project for project in projects]
        return projects

    @token_required
    def get(self, user):
        body = request.get_json()
        projects = self.fetch_user_projects(body.get('query', {}), body.get('options', {}))
        return {
            'success': True,
            'projects': [unmask_fields(project, self.project_masker) for project in projects]
        }, 200

from app import mongo_client, database
