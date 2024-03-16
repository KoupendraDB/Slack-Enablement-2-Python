import redis, os, json

config = {}
with open('../config.json') as config_file:
	config = json.load(config_file)

class RedisManager():
  def __init__(self):
    print('[*] Connecting to Redis...')
    redis_config = config['redis']
    self.redis_client = redis.Redis(
      host = redis_config['server'],
      port = redis_config['port'],
      password = os.environ[redis_config['password_variable']],
      charset = "utf-8",
      decode_responses = True
    )
    self.redis_client.ping()
    print("[+] Successfully connected to Redis!")
