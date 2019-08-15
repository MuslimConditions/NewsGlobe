import cherrypy
from paste.translogger import TransLogger

from server import app


def run_server():
    # Enable WSGI access logging via Paste
    app_logged = TransLogger(app)

    # Mount the WSGI callable object (app) on the root directory
    cherrypy.tree.graft(app_logged, '/')

    # Set the configuration of th web web_app
    cherrypy.config.update({
        'engine.autoreload_on': True,
        'log.screen': True,
        'web_app.socket_port': 80,
        'web_app.socket_host': '0.0.0.0'
    })

    # Start the CherryPy WSGI web web_app
    cherrypy.engine.start()
    cherrypy.engine.block()


if __name__ == "__main__":
    run_server()
