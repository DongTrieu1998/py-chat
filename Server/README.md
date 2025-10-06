# 🚀 Chat Server - JSON RPC API

A modern multi-client chat server with JSON RPC API for real-time messaging.

## 🎯 **What is this?**

This is a **chat server** that allows multiple users to:
- ✅ Join chat rooms with custom usernames
- 💬 Send and receive messages in real-time
- 👥 See who's currently online
- 🚪 Leave chat gracefully

**Key Feature**: All communication uses **JSON RPC API** - structured, reliable, and extensible.

## 🚀 **Quick Start**

### 1. Start the Server
```bash
cd Server
python main.py
```

You'll see:
```
🚀 Starting Chat Application...
🚀 RPC Server started and listening on 127.0.0.1:65432
Waiting for client connections...
```

### 2. Connect Clients
Open new terminals and run:
```bash
python simple_client.py
```

Enter your username and start chatting!

## 💬 **How to Use**

### **Basic Chat Commands:**
- **Send message**: Just type your message and press Enter
- **See online users**: Type `/users`
- **Leave chat**: Type `/quit`

### **Example Session:**
```
🚀 Simple Chat Client (JSON API Only)
Enter your username: Alice
🎉 Joined chat as Alice

📝 Chat Commands:
  - Type message to send
  - /users - Get online users
  - /quit - Exit chat
----------------------------------------

Hello everyone!           # Send message
/users                    # Check who's online
👥 Online users (2): Alice, Bob
📊 Total users: 2

/quit                     # Leave chat
```

## 📡 **JSON RPC API**

The server provides these API methods:

### **1. Join Chat**
```json
{
    "method": "join_chat",
    "params": {"username": "Alice"}
}
```
**Response**: Welcome message + user added to chat

### **2. Send Message**
```json
{
    "method": "send_message",
    "params": {"message": "Hello everyone!"}
}
```
**Response**: Message broadcasted to all users

### **3. Get Online Users**
```json
{
    "method": "get_users",
    "params": {}
}
```
**Response**: List of currently online users

### **4. Leave Chat**
```json
{
    "method": "leave_chat",
    "params": {}
}
```
**Response**: User removed + goodbye message broadcasted

## 🔄 **Message Types**

The server sends different types of messages:

### **Chat Messages**
```json
{
    "type": "chat",
    "message": "Hello everyone!",
    "username": "Alice"
}
```

### **System Messages**
```json
{
    "type": "system",
    "message": "🎉 Alice has joined!",
    "username": "SYSTEM"
}
```

### **API Responses**
```json
{
    "status": "success",
    "message": "Message sent successfully"
}
```

## 🎮 **Multi-Client Demo**

### **Scenario: 3 Users Chatting**

**Terminal 1 - Server:**
```bash
python main.py
🚀 RPC Server started on 127.0.0.1:65432
✅ New client connected: Alice
✅ New client connected: Bob
✅ New client connected: Charlie
```

**Terminal 2 - Alice:**
```
Enter username: Alice
🎉 Joined chat as Alice
Hello everyone!                    # Alice sends message
📨 Bob: Hi Alice!                  # Receives Bob's message
📨 Charlie: Hey there!             # Receives Charlie's message
/users                             # Check online users
👥 Online users (3): Alice, Bob, Charlie
```

**Terminal 3 - Bob:**
```
Enter username: Bob
🎉 Joined chat as Bob
📨 Alice: Hello everyone!          # Receives Alice's message
Hi Alice!                          # Bob sends message
📨 Charlie: Hey there!             # Receives Charlie's message
```

**Terminal 4 - Charlie:**
```
Enter username: Charlie
🎉 Joined chat as Charlie
📨 Alice: Hello everyone!          # Receives Alice's message
📨 Bob: Hi Alice!                  # Receives Bob's message
Hey there!                         # Charlie sends message
/quit                              # Charlie leaves
👋 Charlie ending chat session...
```

## 🛠️ **Server Features**

### **✅ What Works:**
- ✅ **Multi-client support** - Handle multiple users simultaneously
- ✅ **Real-time messaging** - Instant message delivery
- ✅ **User management** - Join/leave with usernames
- ✅ **Online user list** - See who's currently connected
- ✅ **JSON RPC API** - Structured, reliable communication
- ✅ **Thread-safe** - Concurrent client handling
- ✅ **Error handling** - Graceful error responses
- ✅ **Logging** - Comprehensive server logs

### **🔧 Server Configuration:**
- **Host**: `127.0.0.1` (localhost)
- **Port**: `65432`
- **Protocol**: TCP with JSON RPC
- **Max clients**: Unlimited (limited by system resources)
- **Message format**: JSON only

## 🚨 **Troubleshooting**

### **Common Issues:**

**1. "Address already in use"**
```bash
# Kill existing server process
pkill -f "python main.py"
# Or wait 30 seconds for socket to close
```

**2. "Connection refused"**
```bash
# Make sure server is running first
cd Server && python main.py
```

**3. "JSON decode error"**
```bash
# Client sends invalid JSON - server will respond with error
# Check client implementation
```

## 📝 **Notes**

- **JSON Only**: Server only accepts JSON RPC messages
- **Thread Safety**: Each client runs in separate thread
- **Graceful Shutdown**: Use Ctrl+C to stop server
- **No Persistence**: Messages are not saved to disk
- **Local Only**: Currently configured for localhost only
