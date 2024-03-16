from .masker import unmask_fields, mask_fields

class RedisCacheController:
    def __init__(self, redis_client, fields_to_convert = {}, expiration = 0):
        self.redis_client = redis_client
        self.expiration = expiration
        self.fields_to_convert = fields_to_convert
    
    def set_cache(self, key_template, key, value):
        rendered_key = key_template.format(key)
        unmasked_value = unmask_fields(value, self.fields_to_convert)
        self.redis_client.json().set(rendered_key, '$', unmasked_value)
        if self.expiration:
            self.redis_client.expire(rendered_key, self.expiration)

    def get_cache(self, key_template, key):
        rendered_key = key_template.format(key)
        data = self.redis_client.json().get(rendered_key)
        return mask_fields(data, self.fields_to_convert)

    def delete_cache(self, key_template, key):
        rendered_key = key_template.format(key)
        self.redis_client.delete(rendered_key)
