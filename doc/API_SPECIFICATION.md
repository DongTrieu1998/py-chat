# 📡 Chat Server JSON RPC API Specification

## Overview

This document describes the complete JSON RPC API for the Chat Server application. All communication between client and server uses JSON format over TCP sockets.

## 🏗️ Architecture

```
Client ←→ RpcServer ←→ ChatServer
         (Transport)  (Business Logic)
```

### Two-Layer Architecture

- **RpcServer (Transport Layer)**
  - Selector-based I/O multiplexing
  - Socket management (accept, recv, send, close)
  - JSON RPC message routing
  - Broadcasting to clients
  - Connection lifecycle management

- **ChatServer (Business Logic Layer)**
  - User session management
  - Chat operations (join, leave, send, get users)
  - Message validation
  - Username management
  - Business rules enforcement

## 🔄 Message Flow Architecture

### Handler Registration (Initialization)
```
ChatServer → RpcServer: register_handler('join_chat', _handle_join_chat)
ChatServer → RpcServer: register_handler('send_message', _handle_send_message)
ChatServer → RpcServer: register_handler('leave_chat', _handle_leave_chat)
ChatServer → RpcServer: register_handler('get_users', _handle_get_users)
```

### Request Processing Flow
```
1. Client sends JSON RPC → RpcServer (selector detects EVENT_READ)
2. RpcServer parses JSON → Extracts method and params
3. RpcServer routes → Calls registered handler in ChatServer
4. ChatServer processes → Executes business logic
5. ChatServer responds → Returns result to RpcServer
6. RpcServer sends → JSON response to client
7. Optional broadcast → RpcServer sends to all other clients
```

### State Management
- **RpcServer manages**: Socket connections, I/O events, message routing
- **ChatServer manages**: User sessions, usernames, chat logic
- **No shared state**: Clean separation between layers

## 📤 Client → Server Requests

### 1. Join Chat

Join the chat room with a username.

**Request:**
```json
{
    "method": "join_chat",
    "params": {
        "username": "Alice"
    }
}
```

**Success Response:**
```json
{
    "status": "success",
    "message": "Joined chat as Alice",
    "users": ["Alice", "Bob", "Charlie"]
}
```

**Error Response:**
```json
{
    "status": "error",
    "message": "Username already taken"
}
```

### 2. Send Message

Send a chat message to all users.

**Request:**
```json
{
    "method": "send_message",
    "params": {
        "message": "Hello everyone!"
    }
}
```

**Success Response:**
```json
{
    "status": "success",
    "message": "Message sent successfully"
}
```

**Error Response:**
```json
{
    "status": "error",
    "message": "Message too long"
}
```

### 3. Get Online Users

Retrieve list of currently online users.

**Request:**
```json
{
    "method": "get_users",
    "params": {}
}
```

**Success Response:**
```json
{
    "status": "success",
    "message": "Users retrieved successfully",
    "users": [
        {
            "username": "Alice",
            "address": "127.0.0.1:12345"
        },
        {
            "username": "Bob",
            "address": "127.0.0.1:12346"
        }
    ],
    "count": 2
}
```

**Simple Format Response:**
```json
{
    "status": "success",
    "users": ["Alice", "Bob", "Charlie"],
    "count": 3
}
```

### 4. Leave Chat

Leave the chat room.

**Request:**
```json
{
    "method": "leave_chat",
    "params": {}
}
```

**Success Response:**
```json
{
    "status": "success",
    "message": "Left chat successfully"
}
```

## 📥 Server → Client Broadcasts

### Chat Message Broadcast

When a user sends a message, server broadcasts it to all other users.

```json
{
    "type": "chat",
    "message": "Hello everyone!",
    "username": "Alice"
}
```

### System Message Broadcasts

#### User Joined
```json
{
    "type": "system",
    "message": "Alice has joined the chat!",
    "username": "SYSTEM"
}
```

#### User Left
```json
{
    "type": "system",
    "message": "Alice has left the chat!",
    "username": "SYSTEM"
}
```

#### Welcome Message
```json
{
    "type": "system",
    "message": "Welcome to the chat, Alice!",
    "username": "SYSTEM"
}
```

## ❌ Error Responses

### Standard Error Format
```json
{
    "status": "error",
    "message": "Error description"
}
```

### JSON RPC Errors
```json
{
    "error": "Method not found",
    "code": -32601
}
```

### Error Codes

| Code | Description |
|------|-------------|
| -32700 | Parse error |
| -32600 | Invalid request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |

## 🔄 Message Flow Examples

### Complete Chat Session

#### 1. Client Connects and Joins
```
Client → Server:
{
    "method": "join_chat",
    "params": {"username": "Alice"}
}

Server → Client:
{
    "status": "success",
    "message": "Joined chat as Alice"
}

Server → All Other Clients:
{
    "type": "system",
    "message": "Alice has joined the chat!",
    "username": "SYSTEM"
}
```

#### 2. Client Sends Message
```
Client → Server:
{
    "method": "send_message",
    "params": {"message": "Hello everyone!"}
}

Server → Client:
{
    "status": "success",
    "message": "Message sent successfully"
}

Server → All Other Clients:
{
    "type": "chat",
    "message": "Hello everyone!",
    "username": "Alice"
}
```

#### 3. Client Requests User List
```
Client → Server:
{
    "method": "get_users",
    "params": {}
}

Server → Client:
{
    "status": "success",
    "users": ["Alice", "Bob", "Charlie"],
    "count": 3
}
```

#### 4. Client Leaves Chat
```
Client → Server:
{
    "method": "leave_chat",
    "params": {}
}

Server → Client:
{
    "status": "success",
    "message": "Left chat successfully"
}

Server → All Other Clients:
{
    "type": "system",
    "message": "Alice has left the chat!",
    "username": "SYSTEM"
}
```

## 🛠️ Implementation Notes

### Message Parsing
- Server uses `json.loads()` for parsing JSON RPC messages
- Client uses `json.JSONDecoder()` with `raw_decode()` for parsing multiple JSON objects from buffer
- Client maintains buffer to handle partial JSON messages

### I/O Model - Selector-Based
- **Single-threaded event loop** using `selectors.DefaultSelector()`
- **Non-blocking sockets** for all connections
- **I/O multiplexing** - one thread handles thousands of clients
- **Event-driven** - processes only ready sockets
- **Scalable** - low memory footprint (~10 KB per client)

### Connection Handling
- TCP socket connections on `127.0.0.1:65432` (configurable)
- Server socket registered with selector for `EVENT_READ`
- Client sockets registered with selector on accept
- Graceful disconnect handling with cleanup
- Automatic client removal on connection errors
- Selector unregisters socket before closing

### Data Structures
```python
# RpcServer
selector: DefaultSelector              # I/O multiplexing
clients: Dict[socket, Tuple[str, int]] # Socket → Address mapping
client_buffers: Dict[socket, str]      # Partial message buffers
message_handlers: Dict[str, Callable]  # Method → Handler mapping

# ChatServer
user_names: Dict[Tuple[str, int], str] # Address → Username mapping
```

### Validation Rules
- **Username**: Max 50 characters, non-empty after strip, sanitized
- **Message**: Max 1000 characters, non-empty after strip
- **JSON**: Must be valid JSON format
- **Duplicate usernames**: Automatically appended with port number

## 📋 API Summary

| Method | Purpose | Params | Response |
|--------|---------|--------|----------|
| `join_chat` | Join chat room | `username` | Success + user list |
| `send_message` | Send chat message | `message` | Success confirmation |
| `get_users` | Get online users | None | User list with count |
| `leave_chat` | Leave chat room | None | Success confirmation |

## 🔍 Testing Examples

### Using Python Client (Raw Socket)
```python
import json
import socket

# Connect to server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 65432))

# Join chat
join_request = {
    "method": "join_chat",
    "params": {"username": "TestUser"}
}
sock.sendall(json.dumps(join_request).encode('utf-8'))

# Receive response
response = sock.recv(1024).decode('utf-8')
print(f"Join response: {response}")

# Send message
message_request = {
    "method": "send_message",
    "params": {"message": "Hello from API test!"}
}
sock.sendall(json.dumps(message_request).encode('utf-8'))

# Get users
users_request = {
    "method": "get_users",
    "params": {}
}
sock.sendall(json.dumps(users_request).encode('utf-8'))
response = sock.recv(1024).decode('utf-8')
print(f"Users: {response}")

# Leave chat
leave_request = {
    "method": "leave_chat",
    "params": {}
}
sock.sendall(json.dumps(leave_request).encode('utf-8'))

sock.close()
```

### Using SimpleChatClient
```python
from Server.demo_client.simple_client import SimpleChatClient

# Create and run client
client = SimpleChatClient(host='127.0.0.1', port=65432)
client.run()
```

### Testing Multiple Concurrent Clients
```python
import threading
import time
from Server.demo_client.simple_client import SimpleChatClient

def run_client(client_id):
    client = SimpleChatClient()
    if client.connect():
        client.join_chat(f"User{client_id}")
        time.sleep(1)
        client.send_message(f"Hello from User{client_id}!")
        time.sleep(2)
        client.disconnect()

# Launch 10 concurrent clients
threads = []
for i in range(10):
    t = threading.Thread(target=run_client, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("All clients finished!")
```

## 🔧 Technical Details

### Request Flow
1. **Client sends JSON RPC request** → TCP socket
2. **Selector detects EVENT_READ** → RpcServer event loop
3. **RpcServer receives and parses** → JSON RPC message
4. **RpcServer routes to handler** → Looks up in message_handlers dict
5. **ChatServer processes request** → Business logic execution
6. **ChatServer returns response** → Back to RpcServer
7. **RpcServer sends response** → Client socket
8. **Optional: Broadcast to others** → All connected clients except sender

### Broadcast Flow
1. **ChatServer calls broadcast_json_message()** → RpcServer method
2. **RpcServer iterates clients dict** → All connected sockets
3. **Sends JSON to each client** → Except sender socket
4. **Handles errors gracefully** → Removes failed clients

### Performance Characteristics
- **Latency**: Low (single-threaded, no context switching)
- **Throughput**: High (efficient I/O multiplexing)
- **Scalability**: Thousands of concurrent connections
- **Memory**: ~10 KB per client (vs ~8 MB with threads)
- **CPU**: Low overhead (event-driven, no polling)

## 🚀 Future Enhancements

### Protocol Enhancements
- **Authentication**: Add user authentication with tokens
- **Encryption**: TLS/SSL support for secure communication
- **Compression**: Message compression for bandwidth efficiency
- **Heartbeat**: Keep-alive mechanism for connection health

### Feature Enhancements
- **Rooms**: Support multiple chat rooms
- **Private Messages**: Direct messaging between users
- **File Sharing**: Upload and share files
- **Message History**: Persist and retrieve chat history
- **User Presence**: Online/offline/away status
- **Typing Indicators**: Show when users are typing
- **Read Receipts**: Message delivery confirmation

### Scalability Enhancements
- **Horizontal Scaling**: Multiple server instances with load balancer
- **Redis Integration**: Shared state across server instances
- **Message Queue**: Async processing with RabbitMQ/Kafka
- **Database**: PostgreSQL/MongoDB for persistence
- **Caching**: Redis for frequently accessed data

### Client Support
- **WebSocket Support**: Real-time web client support
- **HTTP REST API**: Alternative to raw TCP
- **Mobile SDKs**: iOS and Android client libraries
- **Web Client**: Browser-based chat interface

### Administration
- **Rate Limiting**: Prevent message spam
- **User Roles**: Admin/moderator capabilities
- **Moderation Tools**: Ban, mute, kick users
- **Analytics**: Usage statistics and monitoring
- **Logging**: Comprehensive audit logs

---

*This API specification is for Chat Server v2.0 (Selector-based Architecture)*