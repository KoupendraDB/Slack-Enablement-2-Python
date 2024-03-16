import os, certifi, json, urllib
from pymongo.mongo_client import MongoClient


config = {}
with open('../config.json') as config_file:
	config = json.load(config_file)

database = config['mongo']['database_name']
class MongoManager():
	def __init__(self):
		print('[*] Connecting to MongoDB...')
		mongo_config = config['mongo']
		mongo_username = urllib.parse.quote(os.environ[mongo_config['username_variable']])
		mongo_password = urllib.parse.quote(os.environ[mongo_config['password_variable']])
		mongo_uri = mongo_config['server'].format(username = mongo_username, password = mongo_password)
		self.mongo_client = MongoClient(mongo_uri, tlsCAFile = certifi.where())
		self.mongo_client[database].command('ping')
		print("[+] Successfully connected to MongoDB!")
