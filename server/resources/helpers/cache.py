class RedisCacheController:
    def __init__(self, redis_client, expiration = 0):
        self.redis_client = redis_client
        self.expiration = expiration

    def set_cache(self, key_template, key, value):
        rendered_key = key_template.format(key)
        self.redis_client.json().set(rendered_key, '$', value)
        if self.expiration:
            self.redis_client.expire(rendered_key, self.expiration)

    def get_cache(self, key_template, key):
        rendered_key = key_template.format(key)
        return self.redis_client.json().get(rendered_key)

    def delete_cache(self, key_template, key):
        rendered_key = key_template.format(key)
        self.redis_client.delete(rendered_key)
