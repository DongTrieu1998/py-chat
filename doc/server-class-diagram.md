classDiagram
    class RpcServer {
        -host: str
        -port: int
        -socket: Optional[socket.socket]
        -is_running: bool
        -clients: List[Tuple[socket.socket, Tuple[str, int]]]
        -clients_lock: threading.Lock
        -handlers: Dict[str, Callable]
        +register_handler(method: str, handler: Callable)
        +start_server()
        +stop_server()
        -_accept_connections()
        -_handle_client(client_socket, client_address)
        -_remove_client(client_socket, client_address)
        -_cleanup()
    }

    class ChatManager {
        -clients: Dict[socket.socket, dict]
        -clients_lock: threading.Lock
        +add_client(client_socket, address, name)
        +remove_client(client_socket, address)
        +broadcast_message(message, exclude)
        +handle_message(client_socket, message)
        +get_client_count(): int
        +get_client_list(): List[str]
    }

    class ChatServer {
        -host: str
        -port: int
        -rpc_server: RpcServer
        -chat_manager: ChatManager
        +start_server()
        +stop_server()
        -_setup_handlers()
        -_handle_join(client_socket, address)
        -_handle_message(client_socket, message)
        -_handle_leave(client_socket, address)
    }

    class SimpleChatClient {
        -host: str
        -port: int
        -socket: Optional[socket.socket]
        -is_connected: bool
        -username: str
        +connect(): bool
        +join_chat(username)
        +send_message(message)
        +get_users()
        +disconnect()
        +listen_for_messages()
        -_handle_json_message(json_data)
    }

    ChatServer --> RpcServer : uses
    ChatServer --> ChatManager : uses
    RpcServer --> ChatManager : delegates to
    SimpleChatClient --> ChatServer : connects to