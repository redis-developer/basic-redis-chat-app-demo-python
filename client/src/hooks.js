// @ts-check
import { useEffect, useRef, useState } from "react";
import { getEventSource, getMe, login, logOut } from "./api";
import io from "socket.io-client";
import { parseRoomName } from "./utils";

/**
 * @param {import('./state').UserEntry} newUser
 */
const updateUser = (newUser, dispatch, infoMessage) => {
  dispatch({ type: "set user", payload: newUser });
  if (infoMessage !== undefined) {
    dispatch({
      type: "append message",
      payload: {
        id: "0",
        message: {
          /** Date isn't shown in the info message, so we only need a unique value */
          date: Math.random() * 10000,
          from: "info",
          message: infoMessage,
        },
      },
    });
  }
};

const onShowRoom = (room, username, dispatch) => dispatch({
  type: "add room",
  payload: {
    id: room.id,
    name: parseRoomName(room.names, username),
  },
});

const onMessage = (message, dispatch) => {
  /** Set user online */
  dispatch({
    type: "make user online",
    payload: message.from,
  });
  dispatch({
    type: "append message",
    payload: { id: message.roomId === undefined ? "0" : message.roomId, message },
  });
};

/** @returns {[SocketIOClient.Socket, boolean]} */
const useSocket = (user, dispatch) => {
  const [connected, setConnected] = useState(false);
  /** @type {React.MutableRefObject<SocketIOClient.Socket>} */
  const socketRef = useRef(null);
  const eventSourceRef = useRef(null);
  const socket = socketRef.current;

  /** First of all it's necessary to handle the socket io connection */
  useEffect(() => {
    if (user === null) {
      if (socket !== null) {
        socket.disconnect();
      }
      setConnected(false);
      if (eventSourceRef.current !== null) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    } else {

      if (eventSourceRef.current === null) {
        eventSourceRef.current = getEventSource();
        /** Handle non socket.io messages */
        eventSourceRef.current.onmessage = function (e) {
          const { type, data } = JSON.parse(e.data);
          switch (type) {
            case "user.connected": updateUser(data, dispatch, `${data.username} connected`);
              break;
            case "user.disconnected": updateUser(data, dispatch, `${data.username} left`);
              break;
            case "show.room": onShowRoom(data, user.username, dispatch);
              break;
            case 'message': onMessage(data, dispatch);
              break;
            default:
              break;
          }
        };
      }

      if (socket !== null) {
        socket.connect();
      } else {
        socketRef.current = io();
      }
      setConnected(true);
    }
  }, [user, socket, dispatch]);

  /**
   * Once we are sure the socket io object is initialized
   * Add event listeners.
   */
  useEffect(() => {
    if (connected && user) {
      socket.on("user.connected", (newUser) => updateUser(newUser, dispatch, `${newUser.username} connected`));
      socket.on("user.disconnected", (newUser) => updateUser(newUser, dispatch, `${newUser.username} left`));
      socket.on("show.room", (room) => {
        onShowRoom(room, user.username, dispatch);
      });
      socket.on("message", (message) => {
        onMessage(message, dispatch);
      });
    } else {
      /** If there was a log out, we need to clear existing listeners on an active socket connection */
      if (socket) {
        socket.off("user.connected");
        socket.off("user.disconnected");
        socket.off("user.room");
        socket.off("message");
      }
    }
  }, [connected, user, dispatch, socket]);

  return [socket, connected];
};

/** User management hook. */
const useUser = (onUserLoaded = (user) => { }, dispatch) => {
  const [loading, setLoading] = useState(true);
  /** @type {[import('./state.js').UserEntry | null, React.Dispatch<import('./state.js').UserEntry>]} */
  const [user, setUser] = useState(null);
  /** Callback used in log in form. */
  const onLogIn = (
    username = "",
    password = "",
    onError = (val = null) => { },
    onLoading = (loading = false) => { }
  ) => {
    onError(null);
    onLoading(true);
    login(username, password)
      .then((x) => {
        setUser(x);
      })
      .catch((e) => onError(e.message))
      .finally(() => onLoading(false));
  };

  /** Log out form */
  const onLogOut = async () => {
    logOut().then(() => {
      setUser(null);
      /** This will clear the store, to completely re-initialize an app on the next login. */
      dispatch({ type: "clear" });
      setLoading(true);
    });
  };

  /** Runs once when the component is mounted to check if there's user stored in cookies */
  useEffect(() => {
    if (!loading) {
      return;
    }
    getMe().then((user) => {
      setUser(user);
      setLoading(false);
      onUserLoaded(user);
    });
  }, [onUserLoaded, loading]);

  return { user, onLogIn, onLogOut, loading };
};

export {
  updateUser,
  useSocket,
  useUser
};