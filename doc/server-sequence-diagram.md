sequenceDiagram
    participant Client as SimpleChatClient
    participant RPC as RpcServer
    participant Chat as ChatServer
    participant Manager as ChatManager

    Note over Client,Manager: Client Connection & Join
    Client->>RPC: connect()
    RPC->>Chat: _handle_join()
    Chat->>Manager: add_client()
    Manager->>Manager: broadcast_message("User joined")
    Manager-->>Chat: success
    Chat-->>RPC: success
    RPC-->>Client: connection established

    Note over Client,Manager: Send Message
    Client->>RPC: send_message(JSON RPC)
    RPC->>Chat: _handle_message()
    Chat->>Manager: handle_message()
    Manager->>Manager: broadcast_message()
    Manager-->>Chat: success
    Chat-->>RPC: success

    Note over Client,Manager: Get Users
    Client->>RPC: get_users(JSON RPC)
    RPC->>Chat: _handle_get_users()
    Chat->>Manager: get_client_list()
    Manager-->>Chat: user_list
    Chat-->>RPC: JSON response
    RPC-->>Client: user_list

    Note over Client,Manager: Client Disconnect
    Client->>RPC: disconnect()
    RPC->>Chat: _handle_leave()
    Chat->>Manager: remove_client()
    Manager->>Manager: broadcast_message("User left")
    Manager-->>Chat: success
    Chat-->>RPC: success
    RPC-->>Client: disconnected