from flask_restful import Resource, request
from datetime import timedelta, datetime
from .helpers.cache import RedisCacheController
from bson.objectid import ObjectId
from .helpers.middlewares import token_required
from .user import User
from .helpers.masker import unmask_fields

class Task(Resource):
    def __init__(self):
        self.cache_time = timedelta(minutes = 30)
        self.cache_masker = {
            '_id': {'unmask': str, 'mask': ObjectId},
            'assignee': {'unmask': str, 'mask': ObjectId},
            'created_by': {'unmask': str, 'mask': ObjectId},
            'last_modified_by': {'unmask': str, 'mask': ObjectId},
            'eta_done': {'unmask': datetime.isoformat, 'mask': datetime.fromisoformat},
            'last_modified_at': {'unmask': datetime.isoformat, 'mask': datetime.fromisoformat},
            'created_at': {'unmask': datetime.isoformat, 'mask': datetime.fromisoformat}
        }
        self.task_cache_controller = RedisCacheController(redis_client, self.cache_masker, self.cache_time)
        self.task_database = mongo_client[database].task
        self.user_resource = User()

    def fetch_task(self, key_template = None, key = None, query = {}, options = {}):
        if key_template:
            cached_response = self.task_cache_controller.get_cache(key_template, key)
            if cached_response:
                return cached_response
        task = self.task_database.find_one(query, options)
        if task and key_template:
            self.task_cache_controller.set_cache(key_template, key, task)
        return task

    def fetch_task_by_id(self, task_id):
        key_template = 'task_id:{}'
        query, options = {'_id': ObjectId(task_id)}, {'_id': 0}
        return self.fetch_task(key_template, task_id, query, options)

    def create_task(self, task_request, creator):
        task = {}
        mandatory_fields = ['assignee', 'title']
        for key in mandatory_fields:
            if key not in task_request:
                return False
        task['last_modified_by'] = task['created_by'] = creator['_id']
        task['last_modified_at'] = task['created_at'] = datetime.now()
        task['title'] = task_request['title']
        task['status'] = task_request['status'] if 'status' in task_request else 'Ready'
        if 'eta_done' in task_request:
            task['eta_done'] = datetime.fromisoformat(task_request['eta_done'])
        assignee = self.user_resource.fetch_user_by_username(task_request['assignee'])
        if assignee:
            task['assignee'] = assignee['_id']
            return task
        return None


    @token_required
    def get(self, task_id, user = None):
        task = None
        if user:
            task = self.fetch_task_by_id(task_id)
        if task:
            return {'success': True, 'task': unmask_fields(task, self.cache_masker)}, 200
        return {'success': False}, 404

    @token_required
    def post(self, user):
        task_request = request.get_json()
        task = self.create_task(task_request, user)
        if task:
            insert_result = self.task_database.insert_one(task)
            if insert_result and insert_result.inserted_id:
                result = {'success': True, 'task_id': str(insert_result.inserted_id)}, 201
                return result
            return {'success': False}, 400
        return {'success': False, 'message': 'Invalid data'}, 400

from app import mongo_client, redis_client, database