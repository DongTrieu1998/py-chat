import socket
import selectors
import json
import logging
from typing import Optional, Tuple, List, Callable, Dict, Any

from constants import (
    MessageType, RpcServerConfig, ErrorCodes, Messages, LoggingConfig
)


class RpcServer:
    def __init__(self, host: str = RpcServerConfig.DEFAULT_HOST, port: int = RpcServerConfig.DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_running = False
        self.selector = selectors.DefaultSelector()
        self.clients: Dict[socket.socket, Tuple[str, int]] = {}
        self.client_buffers: Dict[socket.socket, str] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=getattr(logging, LoggingConfig.LEVEL),
            format=LoggingConfig.FORMAT
        )
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    def register_handler(self, method_name: str, handler: Callable) -> None:
        if not callable(handler):
            raise ValueError(f"Handler for method '{method_name}' must be callable")

        self.message_handlers[method_name] = handler
        self.logger.info(f"Registered handler for method: {method_name}")

    def start_server(self) -> None:
        try:
            self._create_and_bind_socket()
            self._start_listening()
            self.logger.info(f"RPC Server started on {self.host}:{self.port}")
            self._register_server_socket()
            self._event_loop()
        except Exception as e:
            self.logger.error(f"Error starting RPC server: {e}")
            raise
        finally:
            self._cleanup()

    def _create_and_bind_socket(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(False)
        self.socket.bind((self.host, self.port))

    def _start_listening(self) -> None:
        self.socket.listen(RpcServerConfig.MAX_CONNECTIONS)
        self.is_running = True
        print(f"RPC Server started and listening on {self.host}:{self.port}")
        print("Waiting for client connections...")

    def _register_server_socket(self) -> None:
        self.selector.register(self.socket, selectors.EVENT_READ, data=None)

    def _event_loop(self) -> None:
        while self.is_running:
            try:
                events = self.selector.select(timeout=1)
                for key, mask in events:
                    if key.data is None:
                        self._accept_connection(key.fileobj)
                    else:
                        self._handle_client_event(key, mask)
            except Exception as e:
                self.logger.error(f"Error in event loop: {e}")
                break

    def _accept_connection(self, server_socket: socket.socket) -> None:
        try:
            client_socket, client_address = server_socket.accept()
            self.logger.info(f"New client connected from {client_address}")
            client_socket.setblocking(False)
            self._add_client(client_socket, client_address)
        except Exception as e:
            self.logger.error(f"Error accepting connection: {e}")

    def _add_client(self, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        self.clients[client_socket] = client_address
        self.client_buffers[client_socket] = ""
        self.selector.register(client_socket, selectors.EVENT_READ, data=client_address)
        self.logger.info(f"RPC session started with {client_address}")

    def _handle_client_event(self, key: selectors.SelectorKey, mask: int) -> None:
        client_socket = key.fileobj
        client_address = key.data

        try:
            data = client_socket.recv(RpcServerConfig.BUFFER_SIZE)
            if data:
                message = data.decode('utf-8')
                self.logger.debug(f"Received from {client_address}: {message}")
                self._process_message(message, client_socket, client_address)
            else:
                self.logger.info(f"Client {client_address} disconnected")
                self._remove_client(client_socket, client_address)
        except UnicodeDecodeError as e:
            self.logger.error(f"Unicode decode error from {client_address}: {e}")
            self._remove_client(client_socket, client_address)
        except ConnectionResetError:
            self.logger.info(f"Client {client_address} disconnected unexpectedly")
            self._remove_client(client_socket, client_address)
        except Exception as e:
            self.logger.error(f"Error handling client {client_address}: {e}")
            self._remove_client(client_socket, client_address)

    def _process_message(self, message: str, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        message_type = self._detect_message_type(message)

        if message_type == MessageType.JSON_RPC:
            self._handle_json_rpc(message, client_socket, client_address)
        else:
            self._send_error_response(
                client_socket,
                'Only JSON RPC messages are supported',
                ErrorCodes.INVALID_REQUEST
            )

    def _detect_message_type(self, message: str) -> MessageType:
        try:
            json.loads(message)
            return MessageType.JSON_RPC
        except json.JSONDecodeError:
            return MessageType.PLAIN_TEXT

    def _handle_json_rpc(self, message: str, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        try:
            rpc_data = json.loads(message)
            method = rpc_data.get('method')
            params = rpc_data.get('params', {})

            if method in self.message_handlers:
                response = self.message_handlers[method](params, client_socket, client_address)
                if response:
                    self._send_json_response(client_socket, response)
            else:
                self._send_error_response(client_socket, f'Method {method} not found', ErrorCodes.METHOD_NOT_FOUND)

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self._send_error_response(client_socket, 'Invalid JSON', ErrorCodes.PARSE_ERROR)
        except Exception as e:
            self.logger.error(f"Error processing JSON RPC: {e}")
            self._send_error_response(client_socket, 'Internal error', ErrorCodes.INTERNAL_ERROR)

    def _send_json_response(self, client_socket: socket.socket, response: Dict[str, Any]) -> None:
        try:
            json_str = json.dumps(response)
            client_socket.sendall(json_str.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Error sending JSON response: {e}")

    def _send_error_response(self, client_socket: socket.socket, error_message: str, error_code: int) -> None:
        error_response = {
            'error': error_message,
            'code': error_code
        }
        self._send_json_response(client_socket, error_response)

    def broadcast_message(self, message: str, sender_socket: Optional[socket.socket] = None):
        for client_socket, client_address in list(self.clients.items()):
            if client_socket != sender_socket:
                try:
                    client_socket.sendall(message.encode('utf-8'))
                except Exception as e:
                    self.logger.error(f"Error broadcasting to {client_address}: {e}")
                    self._remove_client(client_socket, client_address)

    def send_to_client(self, client_socket: socket.socket, message: str) -> None:
        try:
            client_socket.sendall(message.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Error sending message to client: {e}")

    def send_json_to_client(self, client_socket: socket.socket, data: Dict[str, Any]) -> None:
        try:
            json_str = json.dumps(data)
            client_socket.sendall(json_str.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Error sending JSON message to client: {e}")

    def broadcast_json_message(self, data: Dict[str, Any], sender_socket: Optional[socket.socket] = None) -> None:
        try:
            json_str = json.dumps(data)
            for client_socket, client_address in list(self.clients.items()):
                if client_socket != sender_socket:
                    try:
                        client_socket.sendall(json_str.encode('utf-8'))
                    except Exception as e:
                        self.logger.error(f"Error broadcasting to {client_address}: {e}")
                        self._remove_client(client_socket, client_address)
        except json.JSONEncodeError as e:
            self.logger.error(f"Error encoding JSON for broadcast: {e}")

    def _remove_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        try:
            self.selector.unregister(client_socket)
        except Exception:
            pass

        try:
            client_socket.close()
        except Exception:
            pass

        if client_socket in self.clients:
            del self.clients[client_socket]

        if client_socket in self.client_buffers:
            del self.client_buffers[client_socket]

        print(f"Removed client {client_address}")

    def get_connected_clients(self) -> List[Tuple[str, int]]:
        return list(self.clients.values())

    def stop_server(self) -> None:
        print("\nShutting down RPC server...")
        self.is_running = False

    def _cleanup(self) -> None:
        for client_socket in list(self.clients.keys()):
            try:
                client_socket.close()
            except Exception as e:
                self.logger.error(f"Error closing client socket: {e}")

        self.clients.clear()
        self.client_buffers.clear()

        try:
            self.selector.close()
        except Exception as e:
            self.logger.error(f"Error closing selector: {e}")

        if self.socket:
            self.socket.close()

        self.logger.info("RPC Server cleanup completed")
