import redis, os, json

config = {}
with open('../config.json') as config_file:
	config = json.load(config_file)

print('[*] Connecting to Redis...')
redis_config = config['redis']
redis_client = redis.Redis(
  host = redis_config['server'],
  port = redis_config['port'],
  password = os.environ[redis_config['password_variable']],
  charset = "utf-8",
  decode_responses = True
)