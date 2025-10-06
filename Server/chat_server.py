import socket
import logging
from typing import Tuple, Dict, Any, List
from rpc_server import RpcServer
from constants import ChatServerConfig, Messages, ValidationRules


class ChatServer:
    def __init__(self, rpc_server: RpcServer):
        self.rpc_server = rpc_server
        self.user_names: Dict[Tuple[str, int], str] = {}
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._register_handlers()

    def _register_handlers(self):
        self.rpc_server.register_handler('join_chat', self._handle_join_chat)
        self.rpc_server.register_handler('leave_chat', self._handle_leave_chat)
        self.rpc_server.register_handler('send_message', self._handle_send_message)
        self.rpc_server.register_handler('get_users', self._handle_get_users)

    def _validate_message(self, message: str) -> bool:
        return ValidationRules.is_valid_message(message)

    def _get_username(self, client_address: Tuple[str, int]) -> str:
        return self.user_names.get(client_address, f"{ChatServerConfig.DEFAULT_USERNAME_PREFIX}{client_address[1]}")

    def _format_chat_message(self, username: str, message: str) -> str:
        return f"{username}: {message.strip()}"

    def _handle_join_chat(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        username = self._validate_and_get_username(params, client_address)

        if not username:
            return {
                'status': 'error',
                'message': 'Invalid username'
            }

        self.user_names[client_address] = username
        self._broadcast_join_message(username, client_socket)
        self._send_welcome_message(username, client_socket)

        self.logger.info(f"{username} ({client_address}) joined the chat")

        return {
            'status': 'success',
            'message': f'Joined chat as {username}',
            'users': list(self.user_names.values())
        }

    def _validate_and_get_username(self, params: Dict[str, Any], client_address: Tuple[str, int]) -> str:
        username = params.get('username', f"{ChatServerConfig.DEFAULT_USERNAME_PREFIX}{client_address[1]}")
        username = ValidationRules.sanitize_username(username)

        if username in self.user_names.values():
            username = f"{username}_{client_address[1]}"

        return username

    def _broadcast_join_message(self, username: str, client_socket: socket.socket) -> None:
        join_data = {
            'type': 'system',
            'message': f"{username} has joined the chat!",
            'username': 'SYSTEM'
        }
        self.rpc_server.broadcast_json_message(join_data, client_socket)

    def _send_welcome_message(self, username: str, client_socket: socket.socket) -> None:
        welcome_data = {
            'type': 'system',
            'message': f"Welcome to the chat, {username}!",
            'username': 'SYSTEM'
        }
        self.rpc_server.send_json_to_client(client_socket, welcome_data)

    def _handle_leave_chat(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        username = self._get_username(client_address)
        self._remove_user(client_address)
        self._broadcast_leave_message(username, client_socket)

        self.logger.info(f"{username} ({client_address}) left the chat")

        return {
            'status': 'success',
            'message': f'{username} left the chat'
        }

    def _remove_user(self, client_address: Tuple[str, int]) -> None:
        if client_address in self.user_names:
            del self.user_names[client_address]

    def _broadcast_leave_message(self, username: str, client_socket: socket.socket) -> None:
        leave_data = {
            'type': 'system',
            'message': f"{username} has left the chat!",
            'username': 'SYSTEM'
        }
        self.rpc_server.broadcast_json_message(leave_data, client_socket)

    def _handle_send_message(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        message = params.get('message', '')

        if not self._validate_message(message):
            return {
                'status': 'error',
                'message': 'Message cannot be empty or too long'
            }

        username = self._get_username(client_address)
        self.logger.info(f"JSON RPC message from {client_address} ({username}): {message.strip()}")

        chat_data = {
            'type': 'chat',
            'message': message.strip(),
            'username': username
        }
        self.rpc_server.broadcast_json_message(chat_data, client_socket)

        return {
            'status': 'success',
            'message': 'Message sent successfully'
        }

    def _handle_get_users(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        connected_clients = self.rpc_server.get_connected_clients()
        users = self._build_user_list(connected_clients)

        return {
            'status': 'success',
            'users': users,
            'count': len(users)
        }

    def _build_user_list(self, connected_clients: List[Tuple[str, int]]) -> List[Dict[str, str]]:
        users = []
        for addr in connected_clients:
            username = self._get_username(addr)
            users.append({
                'username': username,
                'address': f"{addr[0]}:{addr[1]}"
            })
        return users

    def start(self):
        print("Starting Chat Server...")
        self.rpc_server.start_server()

    def stop(self):
        print("Stopping Chat Server...")
        self.rpc_server.stop_server()

    def get_online_users(self):
        return list(self.user_names.values())

    def get_user_count(self):
        return len(self.user_names)
