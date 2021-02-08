from chat.app import app, run_app  # noqa


if __name__ == "__main__":
    # monkey patch is "required to force the message queue package to use coroutine friendly functions and classes"
    # check flask-socketio docs https://flask-socketio.readthedocs.io/en/latest/
    import eventlet

    eventlet.monkey_patch()
    run_app()
