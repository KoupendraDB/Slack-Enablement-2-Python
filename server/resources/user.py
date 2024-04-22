from flask import Blueprint, request
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from resources.helpers.cache import RedisCacheController
from resources.helpers.middlewares import token_required
from resources.helpers.token import encode_user
from resources.helpers.masker import unmask_fields
from resources.helpers.masks import user_masker, task_masker
from resources.project import project_masker
from connections.mongo import mongo_client
from connections.redis import redis_client
from app import database, config

user_blueprint = Blueprint('user', __name__, url_prefix='/user')

cache_time = timedelta(minutes = 10)
user_cache_controller = RedisCacheController(redis_client, user_masker, cache_time)
user_database = mongo_client[database].user
project_database = mongo_client[database].project
task_database = mongo_client[database].task

def fetch_user(key_template = None, key = None, query = {}, options = {}):
    if key_template:
        cached_response = user_cache_controller.get_cache(key_template, key)
        if cached_response:
            return cached_response
    user = unmask_fields(user_database.find_one(query, options), user_masker)
    if user and key_template:
        user_cache_controller.set_cache(key_template, key, user)
    return user

def fetch_user_by_username(username, ignore_password = True, cached = True):
    key_template = None
    if cached:
        key_template = 'user:username:{}'
    query, options = {'username': username}, {}
    if ignore_password:
        options['password'] = 0
    return fetch_user(key_template, username, query, options)

def get_access_token(username, password):
    user = fetch_user_by_username(username, False, False)
    if user:
        is_correct_password = False
        if config['enable_password_hashing']:
            is_correct_password = check_password_hash(user['password'], password)
        else:
            is_correct_password = user['password'] == password
        if is_correct_password:
            token = encode_user(str(user['_id']))
            return token, user['role']
    return None, None

@user_blueprint.get('/<string:username>')
def get_user(username):
    user = fetch_user_by_username(username)
    if user:
        return {'success': True, 'user': user}, 200
    return {'success': False}, 404

@user_blueprint.post('/register')
def register_user():
    user_request = request.get_json()
    user = fetch_user_by_username(user_request['username'])
    if user:
        return {'success': False}, 409
    if config['enable_password_hashing']:
        user_request['password'] = generate_password_hash(user_request['password'], 'pbkdf2')
    insert_result = user_database.insert_one(user_request)
    if insert_result and insert_result.inserted_id:
        result = {'success': True, 'user_id': str(insert_result.inserted_id)}, 201
        return result
    return {'success': False}, 400

@user_blueprint.post('/login')
def login():
	body = request.get_json()
	access_token, role = get_access_token(body['username'], body['password'])
	if access_token:
		return {'success': True, 'access_token': access_token, 'role': role}, 200
	return {'success': False}, 404

@user_blueprint.get('/projects')
@token_required
def get_user_projects(user):
    projects = unmask_fields(list(project_database.find(
        {
            '_id': {
                '$in': user['projects']
            }
        }
    )), project_masker)
    return {
        'success': True,
        'projects': projects
    }, 200

@user_blueprint.get('/project/<string:project_id>/tasks')
@token_required
def get_user_project_tasks(project_id, user):
    username = user['username']
    tasks = unmask_fields(list(task_database.find({
        'assignee': username,
        'project': project_id
    })), task_masker)
    return {
        'success': True,
        'tasks': tasks
    }, 200


@user_blueprint.get('/personal/tasks')
@token_required
def get_user_personal_tasks(user):
    username = user['username']
    tasks = unmask_fields(list(task_database.find({
        'assignee': username,
        'project': {
            '$exists': False
        }
    })), task_masker)
    return {
        'success': True,
        'tasks': tasks
    }, 200