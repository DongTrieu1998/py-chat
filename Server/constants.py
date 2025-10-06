from enum import Enum


class MessageType(Enum):
    JSON_RPC = "json_rpc"
    PLAIN_TEXT = "plain_text"


class RpcServerConfig:
    DEFAULT_HOST = '127.0.0.1'
    DEFAULT_PORT = 65432
    MAX_CONNECTIONS = 10
    BUFFER_SIZE = 1024
    SOCKET_TIMEOUT = 30.0


class ChatServerConfig:
    DEFAULT_USERNAME_PREFIX = "User_"
    MAX_USERNAME_LENGTH = 50
    MAX_MESSAGE_LENGTH = 1000


class ClientConfig:
    DEFAULT_HOST = '127.0.0.1'
    DEFAULT_PORT = 65432
    BUFFER_SIZE = 1024
    SOCKET_TIMEOUT = 30.0
    MAX_USERNAME_LENGTH = 50


class LoggingConfig:
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LEVEL = 'INFO'


class ErrorCodes:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


class Messages:
    class Server:
        SERVER_STARTED = "RPC Server started on {host}:{port}"
        CLIENT_CONNECTED = "New client connected from {address}"
        CLIENT_DISCONNECTED = "Client {address} disconnected"
        SESSION_STARTED = "RPC session started with {address}"
        CLEANUP_COMPLETED = "RPC Server cleanup completed"

    class Chat:
        USER_JOINED = "{username} has joined the chat!"
        USER_LEFT = "{username} has left the chat!"
        WELCOME_MESSAGE = "Welcome to the chat, {username}!"

    class Client:
        CONNECTED = "{username} connected to server at {host}:{port}"
        LOCAL_ADDRESS = "Local address: {address}"
        BINDING = "Binding client to local address {address}"
        DISCONNECTED = "{username} disconnected from server"

    class Commands:
        HELP = """
Chat Commands:
  - Type message to send
  - /users - Get online users
  - /quit - Exit chat
"""


class ValidationRules:
    @staticmethod
    def is_valid_username(username: str) -> bool:
        return bool(username.strip()) and len(username) <= ChatServerConfig.MAX_USERNAME_LENGTH

    @staticmethod
    def is_valid_message(message: str) -> bool:
        return bool(message.strip()) and len(message) <= ChatServerConfig.MAX_MESSAGE_LENGTH

    @staticmethod
    def sanitize_username(username: str) -> str:
        username = username.strip()
        if len(username) > ChatServerConfig.MAX_USERNAME_LENGTH:
            username = username[:ChatServerConfig.MAX_USERNAME_LENGTH]
        return username or f"{ChatServerConfig.DEFAULT_USERNAME_PREFIX}{id(username)}"
