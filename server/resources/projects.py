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
        cached_data = self.project_cache_controller.get_cache('user:{}:projects', user_id)
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
        projects = self.fetch_user_projects(user_id)
        return {
            'success': True,
            'projects': [unmask_fields(project, self.project_masker) for project in projects]
        }, 200

from app import mongo_client, database, redis_client
