from flask import Blueprint, request
from bson.objectid import ObjectId
from datetime import timedelta, datetime
from resources.helpers.cache import RedisCacheController
from resources.helpers.middlewares import token_required
from resources.helpers.masker import unmask_fields
from resources.helpers.masks import task_masker
from resources.user import fetch_user_by_username
from connections.mongo import mongo_client
from connections.redis import redis_client
from app import database

task_blueprint = Blueprint('task', __name__, url_prefix='/task')

cache_time = timedelta(minutes = 30)

task_cache_controller = RedisCacheController(redis_client, task_masker, cache_time)
task_database = mongo_client[database].task

def fetch_task(key_template = None, key = None, query = {}, options = {}):
    if key_template:
        cached_response = task_cache_controller.get_cache(key_template, key)
        if cached_response:
            return cached_response
    task = task_database.find_one(query, options)
    if task and key_template:
        task_cache_controller.set_cache(key_template, key, task)
    return task

def fetch_task_by_id(task_id):
    key_template = 'task_id:{}'
    query, options = {'_id': ObjectId(task_id)}, {'_id': 0}
    return fetch_task(key_template, task_id, query, options)

def create_task(task_request, creator):
    task_request['last_modified_by'] = task_request['created_by'] = creator['username']
    task_request['last_modified_at'] = task_request['created_at'] = datetime.now()
    task_request['status'] = task_request['status'] if 'status' in task_request else 'Ready'
    task_request['eta_done'] = datetime.fromisoformat(task_request['eta_done'])
    assignee = fetch_user_by_username(task_request['assignee'])
    if assignee:
        task_request['assignee'] = assignee['username']
        return task_request
    return None

def modify_task(task_request, user):
    task = {}
    fields_to_exclude = ['_id', 'created_by', 'last_modified_by', 'created_at', 'last_modified_at']
    for field in fields_to_exclude:
        if field in task_request:
            return None
    task['last_modified_at'] = datetime.now()
    task['last_modified_by'] = user['username']
    if 'eta_done' in task_request:
        task['eta_done'] = datetime.fromisoformat(task_request['eta_done'])
    if 'assignee' in task_request:
        assignee = fetch_user_by_username(task_request['assignee'])
        if assignee:
            task['assignee'] = assignee['username']
        else:
            return None
    for k, v in task_request.items():
        if k not in ['assignee', 'eta_done']:
            task[k] = v
    return task


@task_blueprint.get('/<string:task_id>')
@token_required
def get_task(task_id, user):
    if user:
        task = fetch_task_by_id(task_id)
        if task:
            return {'success': True, 'task': unmask_fields(task, task_masker)}, 200
    return {'success': False}, 404


@task_blueprint.post('/')
@token_required
def post_task(user):
    task_request = request.get_json()
    task = create_task(task_request, user)
    if task:
        insert_result = task_database.insert_one(task)
        if insert_result and insert_result.inserted_id:
            result = {'success': True, 'task_id': str(insert_result.inserted_id)}, 201
            return result
        return {'success': False}, 400
    return {'success': False, 'message': 'Invalid data'}, 400


@task_blueprint.patch('/<string:task_id>')
@token_required
def update_task(task_id, user):
    task_request = request.get_json()
    modified_task = modify_task(task_request, user)
    if modified_task:
        update_result = task_database.update_one({'_id': ObjectId(task_id)}, {'$set': modified_task})
        if update_result and update_result.modified_count:
            task_cache_controller.delete_cache('task_id:{}', task_id)
            task = fetch_task_by_id(task_id)
            result = {'success': True, 'task': unmask_fields(task, task_masker)}, 200
            return result
        return {'success': False}, 400
    return {'success': False, 'message': 'Invalid data'}, 400


@task_blueprint.delete('/<string:task_id>')
@token_required
def delete_task(task_id, user):
    if user:
        task = fetch_task_by_id(task_id)
        if task and task['created_by'] != user['username']:
            return {'success': False, 'message': 'Only the task creator can delete the task!'}, 401
        delete_result = task_database.delete_one({'_id': ObjectId(task_id)})
        if delete_result and delete_result.deleted_count:
            task_cache_controller.delete_cache('task_id:{}', task_id)
            return {'success': True}, 200
    return {'success': False}, 404
