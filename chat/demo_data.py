from chat import utils
import redis
import math
import json
import random
import time

demo_users = ["Pablo", "Joe", "Mary", "Alex"]
greetings = ["Hello", "Hi", "Yo", "Hola"]
demo_password = "password123"
messages = [
    "Hello!",
    "Hi, How are you? What about our next meeting?",
    "Yeah everything is fine",
    "Next meeting tomorrow 10.00AM",
    "Wow that's great",
]


def math_random():
    return random.uniform(0, 1)


def get_greeting():
    return greetings[math.floor(math_random() * len(greetings))]


def add_message(room_id, from_id, content, timestamp):
    room_key = f"room:{room_id}"
    message = {
        "from": from_id,
        "date": timestamp,
        "message": content,
        "roomId": room_id,
    }
    # Now the other user sends the greeting to the user
    utils.redis_client.zadd(room_key, {json.dumps(message): int(message["date"])})


def create():
    """Create demo data with the default users"""
    # For each name create a user.
    users = []
    for demo_user in demo_users:
        user = utils.create_user(demo_user, demo_password)
        users.append(user)

    rooms = {}

    # Once the demo users were created, for each user send messages to other ones.
    for user in users:
        other_users = filter(lambda x: x["id"] != user["id"], users)

        for other_user in other_users:
            private_room_id = utils.get_private_room_id(
                int(user["id"]), int(other_user["id"])
            )

            if private_room_id not in rooms:
                res = utils.create_private_room(user["id"], other_user["id"])
                room = res[0]
                rooms[private_room_id] = room

            add_message(
                private_room_id,
                other_user["id"],
                get_greeting(),
                time.time() - math_random() * 222,
            )

    def random_user_id():
        return users[math.floor(len(users) * math_random())]["id"]

    for key, message in enumerate(messages):
        add_message(
            "0", random_user_id(), message, time.time() - ((len(messages) - key) * 200),
        )
