import os
import sys

from flask import Flask
from flask_cors import CORS
from flask_session import Session
from flask_socketio import SocketIO

from chat import utils
from chat.config import get_config
from chat.socketio_signals import io_connect, io_disconnect, io_join_room, io_on_message

sess = Session()
app = Flask(__name__, static_url_path="", static_folder="../client/build")
app.config.from_object(get_config())
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


def run_app():
    # Create redis connection etc.
    # Here we initialize our database, create demo data (if it's necessary)
    # TODO: maybe we need to do it for gunicorn run also?
    utils.init_redis()
    sess.init_app(app)

    # moved to this method bc it only applies to app.py direct launch
    # Get port from the command-line arguments or environment variables
    arg = sys.argv[1:]
    # TODO: js client is hardcoded to proxy all to 8000 port, maybe change it?
    port = int(os.environ.get("PORT", 5000))
    if len(arg) > 0:
        try:
            port = int(arg[0])
        except ValueError:
            pass

    # we need socketio.run() instead of app.run() bc we need to use the eventlet server
    socketio.run(app, port=port, debug=True, use_reloader=True)


# this was rewritten from decorators so we can move this methods to another file
socketio.on_event("connect", io_connect)
socketio.on_event("disconnect", io_disconnect)
socketio.on_event("room.join", io_join_room)
socketio.on_event("message", io_on_message)

# routes moved to another file and we need to import it lately
# bc they are using app from this file
from chat import routes  # noqa

application = app
