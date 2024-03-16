def unmask_fields(obj, fields_to_convert):
    if not obj:
        return obj
    unmasked = {}
    for k, v in obj.items():
        if (k in fields_to_convert):
            unmasked[k] = fields_to_convert[k]['unmask'](v)
        else:
            unmasked[k] = v
    return unmasked

def mask_fields(obj, fields_to_convert):
    if not obj:
        return obj
    masked = {}
    for k, v in obj.items():
        if (k in fields_to_convert):
            masked[k] = fields_to_convert[k]['mask'](v)
        else:
            masked[k] = v
    return masked