import socket
import threading
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
        self.clients: List[Tuple[socket.socket, Tuple[str, int]]] = []
        self.clients_lock = threading.Lock()
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
            self._accept_connections()
        except Exception as e:
            self.logger.error(f"Error starting RPC server: {e}")
            raise
        finally:
            self._cleanup()

    def _create_and_bind_socket(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(RpcServerConfig.SOCKET_TIMEOUT)
        self.socket.bind((self.host, self.port))

    def _start_listening(self) -> None:
        self.socket.listen(RpcServerConfig.MAX_CONNECTIONS)
        self.is_running = True
        print(f"RPC Server started and listening on {self.host}:{self.port}")
        print("Waiting for client connections...")

    def _accept_connections(self) -> None:
        while self.is_running:
            try:
                client_socket, client_address = self.socket.accept()
                self.logger.info(f"New client connected from {client_address}")

                self._add_client(client_socket, client_address)
                self._start_client_handler(client_socket, client_address)

            except socket.timeout:
                continue
            except socket.error as e:
                if self.is_running:
                    self.logger.error(f"Error accepting connection: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in accept_connections: {e}")
                break

    def _add_client(self, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        with self.clients_lock:
            self.clients.append((client_socket, client_address))

    def _start_client_handler(self, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        client_thread = threading.Thread(
            target=self._handle_client,
            args=(client_socket, client_address),
            name=f"ClientHandler-{client_address[0]}:{client_address[1]}"
        )
        client_thread.daemon = True
        client_thread.start()

    def _handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        try:
            with client_socket:
                self.logger.info(f"RPC session started with {client_address}")
                client_socket.settimeout(RpcServerConfig.SOCKET_TIMEOUT)

                while self.is_running:
                    try:
                        message_data = self._receive_message(client_socket)
                        if not message_data:
                            self.logger.info(f"Client {client_address} disconnected")
                            break

                        message = message_data.decode('utf-8')
                        self.logger.debug(f"Received from {client_address}: {message}")

                        self._process_message(message, client_socket, client_address)

                    except socket.timeout:
                        continue
                    except UnicodeDecodeError as e:
                        self.logger.error(f"Unicode decode error from {client_address}: {e}")
                        break

        except ConnectionResetError:
            self.logger.info(f"Client {client_address} disconnected unexpectedly")
        except Exception as e:
            self.logger.error(f"Error handling client {client_address}: {e}")
        finally:
            self._remove_client(client_socket, client_address)

    def _receive_message(self, client_socket: socket.socket) -> bytes:
        return client_socket.recv(RpcServerConfig.BUFFER_SIZE)

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
        with self.clients_lock:
            for client_socket, client_address in self.clients[:]:
                if client_socket != sender_socket:
                    try:
                        client_socket.sendall(message.encode('utf-8'))
                    except:
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
            with self.clients_lock:
                for client_socket, client_address in self.clients[:]:
                    if client_socket != sender_socket:
                        try:
                            client_socket.sendall(json_str.encode('utf-8'))
                        except Exception as e:
                            self.logger.error(f"Error broadcasting to {client_address}: {e}")
                            self._remove_client(client_socket, client_address)
        except json.JSONEncodeError as e:
            self.logger.error(f"Error encoding JSON for broadcast: {e}")

    def _remove_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        with self.clients_lock:
            try:
                self.clients.remove((client_socket, client_address))
                client_socket.close()
                print(f"Removed client {client_address}")
            except ValueError:
                pass

    def get_connected_clients(self) -> List[Tuple[str, int]]:
        with self.clients_lock:
            return [client_address for _, client_address in self.clients]

    def stop_server(self) -> None:
        print("\nShutting down RPC server...")
        self.is_running = False
        if self.socket:
            self.socket.close()

    def _cleanup(self) -> None:
        with self.clients_lock:
            for client_socket, _ in self.clients:
                try:
                    client_socket.close()
                except Exception as e:
                    self.logger.error(f"Error closing client socket: {e}")
            self.clients.clear()

        if self.socket:
            self.socket.close()
        self.logger.info("RPC Server cleanup completed")
