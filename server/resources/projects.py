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
            '_id': {'unmask': str, 'mask': ObjectId},
            'users': {'unmask': lambda users: list(map(lambda x: str(x), users)), 'mask': lambda users: list(map(lambda x: ObjectId(x), users))}
        }
        self.project_database = mongo_client[database].project
        self.project_cache_controller = RedisCacheController(redis_client, self.project_masker, self.cache_time)

    def fetch_user_projects(self, user):
        projects = self.project_database.find({'users': {'$elemMatch': {'$eq': user['_id']}}}, {'users': 0})
        return projects if projects else []

    @token_required
    def get(self, user):
        project = self.fetch_user_projects(user)
        return {
            'success': True,
            'projects': [unmask_fields(project, self.project_masker) for project in project]
            }, 200


from app import mongo_client, database, redis_client
