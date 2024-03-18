from setup import *

app = create_app()

if __name__ == '__main__':
	app.run(
		host = 'localhost',
		port = config['server_port'],
		debug = True
	)