import json

from flask import session
from flask_socketio import emit, join_room

from chat import utils


def publish(name, message, broadcast=False, room=None):
    """If the messages' origin is the same sever, use socket.io for sending, otherwise: pub/sub"""
    if room:
        emit(name, message, room=room, broadcast=True)
    else:
        emit(name, message, broadcast=broadcast)
    # Here is an additional publish for the redis pub/sub
    outgoing = {"serverId": utils.SERVER_ID, "type": name, "data": message}
    utils.redis_client.publish("MESSAGES", json.dumps(outgoing))


def io_connect():
    """Handle socket.io connection, check if the session is attached"""
    # it's better to use get method for dict-like objects, it provides helpful setting of default value
    user = session.get("user", None)
    if not user:
        return

    user_id = user.get("id", None)
    utils.redis_client.sadd("online_users", user_id)

    msg = dict(user)
    msg["online"] = True

    publish("user.connected", msg, broadcast=True)


def io_disconnect():
    user = session.get("user", None)
    if user:
        utils.redis_client.srem("online_users", user["id"])
        msg = dict(user)
        msg["online"] = False
        publish("user.disconnected", msg, broadcast=True)


def io_join_room(id_room):
    join_room(id_room)


def io_on_message(message):
    """Handle incoming message, make sure it's send to the correct room."""

    def escape(htmlstring):
        """Clean up html from the incoming string"""
        escapes = {'"': "&quot;", "'": "&#39;", "<": "&lt;", ">": "&gt;"}
        # This is done first to prevent escaping other escapes.
        htmlstring = htmlstring.replace("&", "&amp;")
        for seq, esc in escapes.items():
            htmlstring = htmlstring.replace(seq, esc)
        return htmlstring

    # Make sure nothing illegal is sent here.
    message["message"] = escape(message["message"])
    # The user might be set as offline if he tried to access the chat from another tab, pinging by message
    # resets the user online status
    utils.redis_client.sadd("online_users", message["from"])
    # We've got a new message. Store it in db, then send back to the room. */
    message_string = json.dumps(message)
    room_id = message["roomId"]
    room_key = f"room:{room_id}"

    is_private = not bool(utils.redis_client.exists(f"{room_key}:name"))
    room_has_messages = bool(utils.redis_client.exists(room_key))

    if is_private and not room_has_messages:
        ids = room_id.split(":")
        msg = {
            "id": room_id,
            "names": [
                utils.hmget(f"user:{ids[0]}", "username"),
                utils.hmget(f"user:{ids[1]}", "username"),
            ],
        }
        publish("show.room", msg, broadcast=True)
    utils.redis_client.zadd(room_key, {message_string: int(message["date"])})

    if is_private:
        publish("message", message, room=room_id)
    else:
        publish("message", message, broadcast=True)
