from flask import Blueprint, request
from resources.helpers.masker import unmask_fields
from resources.helpers.masks import user_masker
from connections.mongo import mongo_client
from app import database

users_blueprint = Blueprint('users', __name__, url_prefix='/users')

project_database = mongo_client[database].project
user_database = mongo_client[database].user

@users_blueprint.get('/available/<string:role>')
def get_available_users(role):
    querystring = request.args.to_dict()
    name = querystring.get('name', '')
    max_projects = querystring.get('max_projects', 1)
    users = unmask_fields(list(user_database.find(
        {
            'role': role,
            'name': {
                '$regex': name
            },
            'projects': {
                '$lt': {
                    '$size': max_projects
                }
            }
        }
    )), user_masker)
    return {
        'success': True,
        'users': users
    }, 200