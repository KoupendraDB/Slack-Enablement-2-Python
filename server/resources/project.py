from flask import Blueprint, request
from datetime import timedelta
from bson.objectid import ObjectId
from resources.helpers.middlewares import token_required
from resources.helpers.cache import RedisCacheController
from resources.helpers.masker import unmask_fields
from resources.helpers.masks import project_masker, user_masker
from connections.mongo import mongo_client
from connections.redis import redis_client
from app import database
import os, base64

project_blueprint = Blueprint('project', __name__, url_prefix='/project')

cache_time = timedelta(minutes = 30)

project_database = mongo_client[database].project
user_database = mongo_client[database].user
project_cache_controller = RedisCacheController(redis_client, project_masker, cache_time)

def fetch_project(key_template = None, key = None, query = {}, options = {}):
    if key_template:
        cached_response = project_cache_controller.get_cache(key_template, key)
        if cached_response:
            return cached_response
    project = project_database.find_one(query, options)
    if project and key_template:
        project_cache_controller.set_cache(key_template, key, project)
    return project

def fetch_project_by_id(project_id):
    key_template = 'project:id:{}'
    query = {'_id': ObjectId(project_id)}
    return fetch_project(key_template, project_id, query)

def fetch_project_by_channel_id(channel_id):
    key_template = 'project:channel_id:{}'
    query = {'channel_id': channel_id}
    return fetch_project(key_template, channel_id, query)

def generate_invitation_code():
    token=os.urandom(8)
    return base64.b64encode(token).decode('ascii')


@project_blueprint.get('/<string:project_id>')
@token_required
def get_project(project_id, user):
    project = fetch_project_by_id(project_id)
    if project:
        return {
            'success': True,
            'project': unmask_fields(project, project_masker)
        }, 200
    return {
        'success': False,
    }, 404


@project_blueprint.post('/')
@token_required
def post_project(user):
    project_request = request.get_json()
    project_details = project_request.get('details')
    insert_result = project_database.insert_one(project_details)
    if insert_result and insert_result.inserted_id:
        user_database.update_many(
            {
                'username': {
                    '$in': project_request.get('members', [])
                }
            },
            {
                '$addToSet': {
                    'projects': insert_result.inserted_id
                }
            }
        )
        result = {'success': True, 'project_id': str(insert_result.inserted_id)}, 201
        return result
    return {'success': False}, 400


@project_blueprint.get('/channel/<string:channel_id>')
def get_project_by_channel_id(channel_id):
    project = fetch_project_by_channel_id(channel_id)
    if project:
        return {
            'success': True,
            'project': unmask_fields(project, project_masker)
        }, 200
    return {
        'success': False,
    }, 404


@project_blueprint.post('/accept-invite/<string:invitation_code>')
@token_required
def accept_project_invite(invitation_code, user):
    username = user['username']
    project = project_database.find_one({
        f'invitations.{username}': {
            '$exists': True,
            '$eq': invitation_code
        }
    })

    if not project:
        return {'success': False, 'message': 'Invalid code!'}, 404

    updated_user = unmask_fields(user_database.find_one_and_update(
        {
            '_id': user['_id']
        },
        {
            '$addToSet': {
                'projects': project['_id']
            }
        }
    ), user_masker)

    updated_project = unmask_fields(project_database.find_one_and_update(
        {
            '_id': project['_id']
        },
        {
            '$unset': {
                f'invitations.{username}': 1
            }
        }
    ), project_masker)
    
    if updated_project:
        project_cache_controller.delete_cache('project:id:{}', updated_project['_id'])
        project_cache_controller.delete_cache('project:channel_id:{}', updated_project['channel_id'])
        project_cache_controller.delete_cache('user:username:{}', username)
        project_cache_controller.delete_cache('token_user_id:{}', updated_user['_id'])
        return {'success': True, 'project': updated_project}, 200
    return {'success': False, 'message': 'Unknown error!'}, 400


@project_blueprint.post('/<string:project_id>/create-invite')
@token_required
def create_project_invite(project_id, user):
    invitees = request.get_json().get('invitees')
    project = fetch_project_by_id(project_id)

    if not project:
        return {'success': False, 'message': 'Project does not exist!'}, 404
    
    invitation_codes = {}
    for invitee in invitees:
        if project.get('invitations', {}).get(invitee):
            return {
                'success': False,
                'message': 'Invitation already sent!'
            }, 409
        invitation_codes[f'invitations.{invitee}'] = generate_invitation_code()
    
    updated_project = unmask_fields(project_database.find_one_and_update(
        {
            '_id': project['_id']
        },
        {
            '$set': invitation_codes
        }
    ), project_masker)
    
    if updated_project:
        project_cache_controller.delete_cache('project:id:{}', updated_project['_id'])
        project_cache_controller.delete_cache('project:channel_id:{}', updated_project['channel_id'])
        return {
            'success': True,
            'invitation_codes': invitation_codes
        }, 200

    return {'success': False, 'message': 'Unknown error!'}, 400


@project_blueprint.post('/<string:project_id>/roll-off-members')
@token_required
def roll_off_member(project_id, user):
    members = request.get_json().get('members', [])
    user_database.update_many(
        {
            'username': {
                '$in': members
            }
        },
        {
            '$pull': {
                'projects': ObjectId(project_id)
            }
        }
    )
    users = list(user_database.find(
        {
            'username': {
                '$in': members
            }
        }
    ))
    for user in users:
        project_cache_controller.delete_cache('user:username:{}', user['username'])
        project_cache_controller.delete_cache('token_user_id:{}', str(user['_id']))
    return {'success': True}, 200


@project_blueprint.get('/<string:project_id>/members')
def get_project_members(project_id):
    users = unmask_fields(list(user_database.find(
        {
            'projects': {
                '$elemMatch': {'$in': [ObjectId(project_id)]}
            }
        },
        {
            '_id': 0,
            'password': 0
        }
    )), user_masker)

    return {
        'success': True,
        'members': users
    }, 200