from bson import ObjectId
from datetime import date, datetime

project_masker = {
    '_id': {'unmask': str, 'mask': ObjectId}
}

task_masker = {
    '_id': {'unmask': str, 'mask': ObjectId},
    'eta_done': {'unmask': date.isoformat, 'mask': datetime.fromisoformat},
    'last_modified_at': {'unmask': datetime.isoformat, 'mask': datetime.fromisoformat},
    'created_at': {'unmask': datetime.isoformat, 'mask': datetime.fromisoformat}
}

user_masker = {
    '_id': {'unmask': str, 'mask': ObjectId},
    'projects': {
        'unmask': lambda y: list(map(lambda x: str(x), y)),
        'mask': lambda y: list(map(lambda x: ObjectId(x), y))
    }
}