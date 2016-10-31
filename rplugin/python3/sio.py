"""Receives vim buffer and sends to socketio-client for preview"""

import socketio
import eventlet
import eventlet.wsgi
from flask import Flask, render_template, request


def runserver():
    sio = socketio.Server(async_mode='eventlet')
    app = Flask(__name__)

    @app.route('/')
    def index():
        """Serve the client-side application."""
        return render_template('index.html')

    @app.route('/render', methods=["PUT"])
    def render():
        """Render the html received from vim"""
        html = request.get_data().decode('utf-8')
        print(html)
        sio.emit('render', html)
        return 'OK'

    @app.route('/quit', methods=["PUT"])
    def quit():
        """Render the html received from vim"""
        sio.emit('quit', 'quit')
        return 'OK'

    """Run little flask+socketio instance to serve previews"""
    # wrap Flask application with engineio's middleware
    app = socketio.Middleware(sio, app)

    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('', 8000)), app)
