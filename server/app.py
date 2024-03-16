from setup import *

app = create_app()

if __name__ == '__main__':
	app.run(
		port = config['server_port'],
		debug = True
	)