from flask import Blueprint, request
from resources.helpers.masker import unmask_fields
from resources.helpers.masks import task_masker
from connections.mongo import mongo_client
from app import database

tasks_blueprint = Blueprint('tasks', __name__, url_prefix='/tasks')

task_database = mongo_client[database].task

@tasks_blueprint.get('/')
def search_tasks():
    query = request.get_json()
    tasks = unmask_fields(list(task_database.find(query)), task_masker)
    return {
        'success': True,
        'tasks': [task for task in tasks]
    }, 200
