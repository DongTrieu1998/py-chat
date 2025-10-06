classDiagram
    class RpcServer {
        -host: str
        -port: int
        -socket: Optional[socket.socket]
        -is_running: bool
        -selector: DefaultSelector
        -clients: Dict[socket.socket, Tuple[str, int]]
        -client_buffers: Dict[socket.socket, str]
        -message_handlers: Dict[str, Callable]
        +register_handler(method: str, handler: Callable)
        +start_server()
        +stop_server()
        +broadcast_json_message(data, sender_socket)
        +send_json_to_client(socket, data)
        +get_connected_clients(): List[Tuple[str, int]]
        -_event_loop()
        -_accept_connection(server_socket)
        -_handle_client_event(key, mask)
        -_add_client(socket, address)
        -_remove_client(socket, address)
        -_process_message(message, socket, address)
        -_handle_json_rpc(message, socket, address)
        -_cleanup()
    }

    class ChatServer {
        -rpc_server: RpcServer
        -user_names: Dict[Tuple[str, int], str]
        -logger: Logger
        +start()
        +stop()
        +get_online_users(): List[str]
        +get_user_count(): int
        -_register_handlers()
        -_handle_join_chat(params, socket, address): Dict
        -_handle_leave_chat(params, socket, address): Dict
        -_handle_send_message(params, socket, address): Dict
        -_handle_get_users(params, socket, address): Dict
        -_validate_message(message): bool
        -_get_username(address): str
        -_broadcast_join_message(username, socket)
        -_broadcast_leave_message(username, socket)
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
        +run()
        -_handle_json_message(json_data)
    }

    class Constants {
        <<enumeration>>
        MessageType
        RpcServerConfig
        ChatServerConfig
        ClientConfig
        LoggingConfig
        ErrorCodes
        Messages
        ValidationRules
    }

    ChatServer --> RpcServer : uses
    RpcServer --> Constants : uses
    ChatServer --> Constants : uses
    SimpleChatClient --> ChatServer : connects to

    note for RpcServer "Selector-based I/O multiplexing\nSingle-threaded event loop\nHandles all socket operations"
    note for ChatServer "Business logic layer\nManages user sessions\nHandles chat commands"
    note for SimpleChatClient "JSON RPC client\nNon-blocking message handling"