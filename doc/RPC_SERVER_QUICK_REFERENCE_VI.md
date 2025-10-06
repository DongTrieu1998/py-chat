# RpcServer - Tài Liệu Tham Khảo Nhanh

## Tổng Quan Nhanh

**RpcServer** là tầng vận chuyển (transport layer) sử dụng **selector-based I/O multiplexing** để xử lý hàng nghìn kết nối đồng thời trong một luồng duy nhất.

## Các Hàm Chính và Mục Đích

### Khởi Tạo và Cấu Hình

| Hàm | Mục Đích | Khi Nào Gọi |
|-----|----------|-------------|
| `__init__(host, port)` | Khởi tạo server với các data structures | Khi tạo instance |
| `_setup_logging()` | Cấu hình logging | Tự động trong `__init__` |
| `register_handler(method, handler)` | Đăng ký handler cho JSON RPC method | Trước khi start server |

### Khởi Động Server

| Hàm | Mục Đích | Thứ Tự |
|-----|----------|---------|
| `start_server()` | Entry point khởi động server | 1 |
| `_create_and_bind_socket()` | Tạo TCP socket và bind | 2 |
| `_start_listening()` | Bắt đầu listen | 3 |
| `_register_server_socket()` | Đăng ký với selector | 4 |
| `_event_loop()` | Vòng lặp xử lý events | 5 |

### Xử Lý Kết Nối

| Hàm | Mục Đích | Khi Nào Gọi |
|-----|----------|-------------|
| `_accept_connection(socket)` | Accept kết nối mới | Khi có client connect |
| `_add_client(socket, address)` | Thêm client vào hệ thống | Sau khi accept |
| `_handle_client_event(key, mask)` | Xử lý event từ client | Khi client gửi data |
| `_remove_client(socket, address)` | Loại bỏ client | Khi disconnect hoặc lỗi |

### Xử Lý Message

| Hàm | Mục Đích | Flow |
|-----|----------|------|
| `_process_message(msg, socket, addr)` | Phát hiện loại message | 1 |
| `_detect_message_type(msg)` | Kiểm tra JSON hay plain text | 2 |
| `_handle_json_rpc(msg, socket, addr)` | Parse và route JSON RPC | 3 |

### Gửi Message

| Hàm | Mục Đích | Sử Dụng |
|-----|----------|---------|
| `_send_json_response(socket, data)` | Gửi JSON đến 1 client | Response cho request |
| `_send_error_response(socket, msg, code)` | Gửi error response | Khi có lỗi |
| `send_to_client(socket, msg)` | Gửi plain text đến 1 client | Ít dùng |
| `send_json_to_client(socket, data)` | Gửi JSON đến 1 client | Gửi message riêng |
| `broadcast_message(msg, sender)` | Broadcast plain text | Ít dùng |
| `broadcast_json_message(data, sender)` | Broadcast JSON | Thông báo cho tất cả |

### Quản Lý và Cleanup

| Hàm | Mục Đích | Khi Nào Gọi |
|-----|----------|-------------|
| `get_connected_clients()` | Lấy list địa chỉ clients | Khi cần danh sách |
| `stop_server()` | Dừng server gracefully | Ctrl+C hoặc shutdown |
| `_cleanup()` | Dọn dẹp tài nguyên | Tự động khi thoát |

## Data Structures Quan Trọng

```python
# Selector - Giám sát I/O events
self.selector: DefaultSelector

# Map socket → địa chỉ client
self.clients: Dict[socket, Tuple[str, int]]

# Buffer cho mỗi client (xử lý partial messages)
self.client_buffers: Dict[socket, str]

# Map method name → handler function
self.message_handlers: Dict[str, Callable]
```

## Luồng Xử Lý Chính

### 1. Khởi Động
```
__init__ → start_server → create socket → listen → register → event_loop
```

### 2. Client Connect
```
Client connect → Selector EVENT_READ → accept → add_client → register client
```

### 3. Client Gửi Message
```
Client send → Selector EVENT_READ → recv → process → handle_json_rpc → 
call handler → send response → broadcast (nếu cần)
```

### 4. Client Disconnect
```
Client close → Selector EVENT_READ → recv empty → remove_client → cleanup
```

### 5. Shutdown
```
Ctrl+C → stop_server → is_running=False → event_loop exit → cleanup
```

## Các Khái Niệm Quan Trọng

### Selector (I/O Multiplexing)
- **Là gì**: Cơ chế giám sát nhiều socket cùng lúc
- **Tại sao**: Xử lý nhiều client với 1 thread
- **Cách hoạt động**: Block cho đến khi có socket sẵn sàng

### Non-Blocking Socket
- **Là gì**: Socket không chặn luồng khi chờ dữ liệu
- **Tại sao**: Cho phép selector giám sát nhiều socket
- **Cách set**: `socket.setblocking(False)`

### Event-Driven
- **Là gì**: Chỉ xử lý khi có event (dữ liệu sẵn sàng)
- **Tại sao**: Không lãng phí CPU khi chờ
- **Cách hoạt động**: `selector.select()` block cho đến khi có event

### JSON RPC
- **Là gì**: Gọi hàm từ xa bằng JSON
- **Format**: `{"method": "...", "params": {...}}`
- **Response**: `{"status": "...", "message": "...", ...}`

## Tại Sao Selector Tốt Hơn Threading?

| Tiêu Chí | Thread-Based | Selector-Based |
|----------|--------------|----------------|
| **Memory** | 8 MB/client | 10 KB/client |
| **CPU** | Context switching | No switching |
| **Scalability** | Hàng trăm | Hàng nghìn |
| **Complexity** | Cần lock | Không cần lock |
| **Debugging** | Khó (race condition) | Dễ (deterministic) |

## Ví Dụ Sử Dụng

### Khởi Tạo và Start Server
```python
# Tạo server
rpc_server = RpcServer(host='127.0.0.1', port=65432)

# Đăng ký handlers
rpc_server.register_handler('join_chat', handle_join)
rpc_server.register_handler('send_message', handle_send)

# Start server (blocking)
rpc_server.start_server()
```

### Implement Handler
```python
def handle_join(params, client_socket, client_address):
    username = params.get('username')
    
    # Xử lý logic
    user_names[client_address] = username
    
    # Broadcast thông báo
    rpc_server.broadcast_json_message({
        'type': 'system',
        'message': f'{username} has joined!',
        'username': 'SERVER'
    }, sender_socket=client_socket)
    
    # Return response
    return {
        'status': 'success',
        'message': f'Joined as {username}'
    }
```

### Gửi Message
```python
# Gửi đến 1 client
rpc_server.send_json_to_client(socket, {
    'type': 'system',
    'message': 'Welcome!'
})

# Broadcast đến tất cả (trừ sender)
rpc_server.broadcast_json_message({
    'type': 'chat',
    'message': 'Hello everyone!',
    'username': 'Alice'
}, sender_socket=sender_socket)
```

## Error Codes (JSON RPC Standard)

| Code | Ý Nghĩa | Khi Nào |
|------|---------|---------|
| -32700 | Parse error | JSON không hợp lệ |
| -32600 | Invalid request | Thiếu field bắt buộc |
| -32601 | Method not found | Method không tồn tại |
| -32602 | Invalid params | Params sai format |
| -32603 | Internal error | Lỗi server |

## Tips và Best Practices

### ✅ Nên Làm
- Handler phải nhanh (< 100ms)
- Luôn return response từ handler
- Xử lý exception trong handler
- Sử dụng `broadcast_json_message` cho thông báo chung
- Log đầy đủ để debug

### ❌ Không Nên
- Blocking call trong handler (database query lâu, file I/O)
- Modify `self.clients` trực tiếp (dùng `_add_client`, `_remove_client`)
- Raise exception từ handler (sẽ crash server)
- Gửi non-JSON data
- Quên cleanup resources

## Troubleshooting

### Server không start
```
Lỗi: Address already in use
Giải pháp: Đợi 30s hoặc kill process cũ
```

### Client disconnect liên tục
```
Nguyên nhân: Handler quá chậm, timeout
Giải pháp: Tối ưu handler, tăng timeout
```

### Memory leak
```
Nguyên nhân: Client không được remove đúng cách
Giải pháp: Kiểm tra exception handling trong handlers
```

### High CPU usage
```
Nguyên nhân: Handler chạy lâu block event loop
Giải pháp: Tách CPU-bound task ra thread riêng
```

## Tài Liệu Chi Tiết

Xem file `RPC_SERVER_DETAILED_ANALYSIS_VI.md` để hiểu sâu hơn về:
- Cơ chế hoạt động của từng hàm
- Kiến thức chuyên sâu về I/O multiplexing
- Design patterns được sử dụng
- Performance optimization techniques


