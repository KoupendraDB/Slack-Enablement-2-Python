from flask_restful import Resource, request
from datetime import timedelta
from bson.objectid import ObjectId
from .helpers.middlewares import token_required
from .helpers.cache import RedisCacheController
from .helpers.masker import unmask_fields

class Project(Resource):
    def __init__(self):
        self.cache_time = timedelta(minutes = 30)
        self.project_masker = {
            '_id': {'unmask': str, 'mask': ObjectId}
        }
        self.project_database = mongo_client[database].project
        self.project_cache_controller = RedisCacheController(redis_client, self.project_masker, self.cache_time)

    def fetch_project(self, project_id):
        cached_data = self.project_cache_controller.get_cache('project:{}', project_id)
        if cached_data:
            return cached_data
        project = self.project_database.find_one({'_id': ObjectId(project_id)}, {'_id': 0})
        if project:
            self.project_cache_controller.set_cache('project:{}', project_id, project)
        return project

    @token_required
    def get(self, project_id, user):
        project = self.fetch_project(project_id)
        if project:
            return {
                'success': True,
                'project': project
            }, 200
        return {
            'success': False,
        }, 404

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

    @token_required
    def patch(self, project_id, user):
        project_update_request = request.get_json()
        update_result = self.project_database.update_one({'_id': ObjectId(project_id)}, {'$set': project_update_request})
        if update_result and update_result.modified_count:
            self.project_cache_controller.delete_cache('project:{}', project_id)
            return {'success': True}, 200
        return {'success': False}, 400

from app import mongo_client, database, redis_client
