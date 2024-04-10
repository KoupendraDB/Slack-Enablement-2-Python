from flask_restful import Resource, request
from datetime import timedelta
from bson.objectid import ObjectId
from .helpers.middlewares import token_required
from .helpers.cache import RedisCacheController
from .helpers.masker import unmask_fields

class Projects(Resource):
    def __init__(self):
        self.cache_time = timedelta(minutes = 30)
        self.project_masker = {
            '_id': {'unmask': str, 'mask': ObjectId}
        }
        self.project_database = mongo_client[database].project
        self.project_cache_controller = RedisCacheController(redis_client, self.project_masker, self.cache_time)

    def fetch_user_projects(self, user_id):
        cached_data = self.project_cache_controller.get_cache('user:{}:projects', str(user_id))
        if cached_data:
            return cached_data
        projects = self.project_database.find({'$or': [
                {'project_manager': user_id},
                {'developers': {'$elemMatch': {'$eq': user_id}}},
                {'qas': {'$elemMatch': {'$eq': user_id}}}
        ]})
        projects = [project for project in projects]
        self.project_cache_controller.set_cache('user:{}:projects', user_id, projects)
        return projects

    @token_required
    def get(self, user_id, user):
        project = self.fetch_user_projects(user_id)
        return {
            'success': True,
            'projects': [unmask_fields(project, self.project_masker) for project in project]
            }, 200

    @token_required
    def post(self, user):
        project_request = request.get_json()
        insert_result = self.project_database.insert_one(project_request)
        if insert_result and insert_result.inserted_id:
            users = project_request['developers'] + project_request['qas'] + [project_request['project_manager'], project_request['admin']]
            for user_id in users:
                self.project_cache_controller.delete_cache('user:{}:projects', user_id)
            result = {'success': True, 'project_id': str(insert_result.inserted_id)}, 201
            return result
        return {'success': False}, 400
        

from app import mongo_client, database, redis_client
