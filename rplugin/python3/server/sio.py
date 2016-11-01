"""Receives vim buffer and sends to socketio-client for preview"""

import os
import sys

import socketio
import eventlet
import eventlet.wsgi
from flask import Flask, render_template, request

# Try redirecting stdout to avoid conflicts with msgpack...
# See: https://github.com/neovim/neovim/issues/2283
sys.stdout = open(os.devnull)


def runserver():
    sio = socketio.Server(async_mode='threading')
    app = Flask(__name__)

    @app.route('/')
    def index():
        """Serve the client-side application."""
        return render_template('index.html')

    @app.route('/render', methods=["PUT"])
    def render():
        """Render the html received from vim"""
        html = request.get_data().decode('utf-8')
        sio.emit('render', html)
        return 'OK'

    @app.route('/quit', methods=["PUT"])
    def quit():
        """Render the html received from vim"""
        sio.emit('quit', 'quit')
        return 'OK'

    """Run little flask+socketio instance to serve previews"""
    # wrap Flask application with engineio's middleware
    app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)

    # deploy as an eventlet WSGI server
    # eventlet.wsgi.server(eventlet.listen(('', 8123)), app)
    app.run(port=8123, threaded=True)


if __name__ == "__main__":
    runserver()
