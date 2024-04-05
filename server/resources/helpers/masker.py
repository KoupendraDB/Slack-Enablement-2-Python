def unmasker(obj, fields_to_convert):
    unmasked = {}
    for k, v in obj.items():
        if (k in fields_to_convert):
            unmasked[k] = fields_to_convert[k]['unmask'](v)
        else:
            unmasked[k] = v
    return unmasked

def masker(obj, fields_to_convert):
    masked = {}
    for k, v in obj.items():
        if (k in fields_to_convert):
            masked[k] = fields_to_convert[k]['mask'](v)
        else:
            masked[k] = v
    return masked

def unmask_fields(obj, fields_to_convert):
    if not obj:
        return obj

    if type(obj) == type([]):
        return [unmasker(doc, fields_to_convert) for doc in obj]
    return unmasker(obj, fields_to_convert)


def mask_fields(obj, fields_to_convert):
    if not obj:
        return obj
    if type(obj) == type([]):
        return [masker(doc, fields_to_convert) for doc in obj]
    return masker(obj, fields_to_convert)