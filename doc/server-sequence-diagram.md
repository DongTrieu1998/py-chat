sequenceDiagram
    participant Client as SimpleChatClient
    participant RPC as RpcServer
    participant Selector as selector
    participant Chat as ChatServer
    participant Users as user_names

    Note over Client,Users: Server Initialization
    Chat->>RPC: register_handler('join_chat', _handle_join_chat)
    Chat->>RPC: register_handler('send_message', _handle_send_message)
    Chat->>RPC: register_handler('leave_chat', _handle_leave_chat)
    Chat->>RPC: register_handler('get_users', _handle_get_users)
    RPC->>Selector: register(server_socket, EVENT_READ)

    Note over Client,Users: Client Connection
    Client->>RPC: TCP connect()
    RPC->>Selector: accept() new connection
    RPC->>Selector: register(client_socket, EVENT_READ)
    RPC->>RPC: clients[socket] = address
    RPC-->>Client: connection established

    Note over Client,Users: Join Chat
    Client->>RPC: {"method": "join_chat", "params": {"username": "Alice"}}
    Selector->>RPC: EVENT_READ on client_socket
    RPC->>RPC: recv() and parse JSON RPC
    RPC->>RPC: lookup handler in message_handlers
    RPC->>Chat: _handle_join_chat(params, socket, address)
    Chat->>Chat: validate username
    Chat->>Users: user_names[address] = "Alice"
    Chat->>RPC: broadcast_json_message(join_data, socket)
    RPC->>Client: broadcast to all clients
    Chat-->>RPC: {"status": "success", "message": "Joined as Alice"}
    RPC-->>Client: send JSON response

    Note over Client,Users: Send Message
    Client->>RPC: {"method": "send_message", "params": {"message": "Hello!"}}
    Selector->>RPC: EVENT_READ on client_socket
    RPC->>RPC: recv() and parse JSON RPC
    RPC->>Chat: _handle_send_message(params, socket, address)
    Chat->>Chat: validate message
    Chat->>Users: username = user_names[address]
    Chat->>RPC: broadcast_json_message(chat_data, socket)
    RPC->>Client: broadcast to all clients except sender
    Chat-->>RPC: {"status": "success"}
    RPC-->>Client: send JSON response

    Note over Client,Users: Get Users
    Client->>RPC: {"method": "get_users", "params": {}}
    Selector->>RPC: EVENT_READ on client_socket
    RPC->>RPC: recv() and parse JSON RPC
    RPC->>Chat: _handle_get_users(params, socket, address)
    Chat->>RPC: get_connected_clients()
    RPC-->>Chat: list of addresses
    Chat->>Users: map addresses to usernames
    Chat-->>RPC: {"status": "success", "users": [...]}
    RPC-->>Client: send JSON response

    Note over Client,Users: Client Disconnect
    Client->>RPC: close connection
    Selector->>RPC: EVENT_READ (EOF detected)
    RPC->>RPC: recv() returns empty
    RPC->>Selector: unregister(client_socket)
    RPC->>RPC: del clients[socket]
    RPC->>RPC: close(socket)
    Note over Chat,Users: user_names cleaned up on next operation