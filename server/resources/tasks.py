from flask_restful import Resource, request
from datetime import datetime, date
from bson.objectid import ObjectId
from .helpers.middlewares import token_required
from .helpers.masker import unmask_fields

class Tasks(Resource):
    def __init__(self):
        self.task_masker = {
            '_id': {'unmask': str, 'mask': ObjectId},
            'eta_done': {'unmask': date.isoformat, 'mask': datetime.fromisoformat},
            'last_modified_at': {'unmask': datetime.isoformat, 'mask': datetime.fromisoformat},
            'created_at': {'unmask': datetime.isoformat, 'mask': datetime.fromisoformat}
        }
        self.task_database = mongo_client[database].task

    def make_query(self, request_query):
        comparators = ['$eq', '$gt', '$gte', '$lt', '$lte', '$ne', '$in', '$nin', '$regex', '$exists']
        fields = ['_id', 'created_by', 'assignee', 'last_modified_by', 'title', 'status', 'created_at', 'last_modified_at', 'eta_done', 'project']
        query = {}
        request_query_dict = request_query.to_dict()
        for field in fields:
            if request_query_dict.get(field, False):
                query[field] = request_query_dict.get(field)
            for comparator in comparators:
                param = field + '_' + comparator
                value = request_query_dict.get(param)
                if value:
                    if comparator in ['$in', '$nin']:
                        value = value.split(',')
                    if field in self.task_masker:
                        if comparator in ['$in', '$nin']:
                            value = [self.task_masker[field]['mask'](val) for val in value]
                        else:
                            value = self.task_masker[field]['mask'](value)
                    if field not in query:
                        query[field] = {}
                    query[field][comparator] = value
        return query

    def fetch_tasks(self, request_query):
        query = self.make_query(request_query)
        tasks = self.task_database.find(query)
        return tasks if tasks else []

    @token_required
    def get(self, user):
        tasks = self.fetch_tasks(request.args)
        return {
            'success': True,
            'tasks': [unmask_fields(task, self.task_masker) for task in tasks]
            }, 200


from app import mongo_client, database
