# 📡 Chat Server JSON RPC API Specification

## Overview

This document describes the complete JSON RPC API for the Chat Server application. All communication between client and server uses JSON format over TCP sockets.

## 🏗️ Architecture

```
Client ←→ RpcServer ←→ ChatServer ←→ ChatManager
```

- **RpcServer**: Handles network communication and JSON RPC protocol
- **ChatServer**: Orchestrates between RPC server and chat logic
- **ChatManager**: Manages client list and chat operations

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
    "message": "🎉 Alice has joined the chat!",
    "username": "SYSTEM"
}
```

#### User Left
```json
{
    "type": "system",
    "message": "👋 Alice has left the chat!",
    "username": "SYSTEM"
}
```

#### Welcome Message
```json
{
    "type": "system",
    "message": "Welcome to the chat, Alice! 👋",
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
    "message": "🎉 Alice has joined the chat!",
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
    "message": "👋 Alice has left the chat!",
    "username": "SYSTEM"
}
```

## 🛠️ Implementation Notes

### Message Parsing
- Server uses `json.JSONDecoder()` with `raw_decode()` for parsing multiple JSON objects from buffer
- Client maintains buffer to handle partial JSON messages

### Threading Model
- Each client connection runs in separate thread
- Thread-safe operations using locks for client list management
- Daemon threads for message listening

### Connection Handling
- TCP socket connections on `127.0.0.1:65432`
- Graceful disconnect handling with cleanup
- Automatic client removal on connection errors

### Validation Rules
- Username: Max 50 characters, non-empty after strip
- Message: Max 1000 characters, non-empty after strip
- JSON: Must be valid JSON format

## 📋 API Summary

| Method | Purpose | Params | Response |
|--------|---------|--------|----------|
| `join_chat` | Join chat room | `username` | Success + user list |
| `send_message` | Send chat message | `message` | Success confirmation |
| `get_users` | Get online users | None | User list with count |
| `leave_chat` | Leave chat room | None | Success confirmation |

## 🔍 Testing Examples

### Using Python Client
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

# Send message
message_request = {
    "method": "send_message", 
    "params": {"message": "Hello from API test!"}
}
sock.sendall(json.dumps(message_request).encode('utf-8'))
```

### Using curl (if HTTP wrapper added)
```bash
curl -X POST http://localhost:65432/rpc \
  -H "Content-Type: application/json" \
  -d '{"method": "join_chat", "params": {"username": "CurlUser"}}'
```

## 🚀 Future Enhancements

- **Authentication**: Add user authentication with tokens
- **Rooms**: Support multiple chat rooms
- **Private Messages**: Direct messaging between users
- **File Sharing**: Upload and share files
- **Message History**: Persist and retrieve chat history
- **WebSocket Support**: Real-time web client support
- **Rate Limiting**: Prevent message spam
- **User Roles**: Admin/moderator capabilities

---

*This API specification is for Chat Server v1.0*