# Phân Tích Chi Tiết RpcServer - Tài Liệu Tiếng Việt

## Tổng Quan

File `rpc_server.py` chứa class `RpcServer` - lớp xử lý tầng vận chuyển (transport layer) của hệ thống chat server. Class này sử dụng kiến trúc **selector-based I/O multiplexing** để xử lý hàng nghìn kết nối đồng thời trong một luồng duy nhất.

## Kiến Thức Cơ Bản Cần Thiết

### 1. Socket Programming
- **Socket**: Điểm cuối (endpoint) của kết nối mạng hai chiều
- **TCP**: Giao thức truyền tải đáng tin cậy, đảm bảo thứ tự gói tin
- **Non-blocking socket**: Socket không chặn luồng khi chờ dữ liệu

### 2. I/O Multiplexing với Selectors
- **Selector**: Cơ chế giám sát nhiều socket cùng lúc
- **Event-driven**: Chỉ xử lý socket khi có sự kiện (dữ liệu sẵn sàng)
- **EVENT_READ**: Sự kiện có dữ liệu để đọc

### 3. JSON RPC
- **RPC (Remote Procedure Call)**: Gọi hàm từ xa như gọi hàm cục bộ
- **JSON**: Format dữ liệu có cấu trúc, dễ đọc và parse

---

## Phân Tích Chi Tiết Từng Hàm

### 1. `__init__(self, host, port)`

**Mục đích**: Khởi tạo RPC server với các cấu trúc dữ liệu cần thiết.

**Ý tưởng thiết kế**:
- Tạo các dictionary để quản lý trạng thái của server
- Khởi tạo selector để giám sát I/O
- Thiết lập logging để theo dõi hoạt động

**Tại sao làm như vậy**:
- **`self.selector = selectors.DefaultSelector()`**: Tự động chọn cơ chế I/O multiplexing tốt nhất cho hệ điều hành (epoll trên Linux, kqueue trên macOS, select trên Windows)
- **`self.clients: Dict[socket, Tuple[str, int]]`**: Map socket → địa chỉ client để tra cứu nhanh
- **`self.client_buffers: Dict[socket, str]`**: Lưu dữ liệu chưa xử lý xong (partial messages)
- **`self.message_handlers: Dict[str, Callable]`**: Map tên method → hàm xử lý (pattern: Strategy Pattern)

**Cơ chế**:
- Dictionary lookup có độ phức tạp O(1) - tra cứu cực nhanh
- Selector sử dụng system call hiệu quả (epoll/kqueue) thay vì polling

**Kiến thức chuyên sâu**:
- **epoll** (Linux): Cơ chế I/O multiplexing hiệu quả, không cần scan toàn bộ file descriptors
- **kqueue** (BSD/macOS): Tương tự epoll nhưng cho hệ BSD

---

### 2. `_setup_logging(self)`

**Mục đích**: Cấu hình hệ thống logging để ghi lại hoạt động của server.

**Ý tưởng thiết kế**:
- Sử dụng module `logging` chuẩn của Python
- Tạo logger riêng cho class để dễ phân biệt log

**Tại sao làm như vậy**:
- **`getattr(logging, LoggingConfig.LEVEL)`**: Chuyển string "INFO" thành `logging.INFO` một cách động
- **`self.logger = logging.getLogger(f"{self.__class__.__name__}")`**: Tạo logger với tên class, giúp dễ debug khi có nhiều class

**Cơ chế**:
- Python logging sử dụng hierarchy (cây phân cấp) để quản lý logger
- Format string cho phép tùy chỉnh cách hiển thị log

---

### 3. `register_handler(self, method_name, handler)`

**Mục đích**: Đăng ký hàm xử lý cho mỗi JSON RPC method.

**Ý tưởng thiết kế**:
- Tách biệt transport layer (RpcServer) và business logic (ChatServer)
- ChatServer đăng ký các handler, RpcServer chỉ route message

**Tại sao làm như vậy**:
- **Kiểm tra `callable(handler)`**: Đảm bảo handler là hàm, tránh lỗi runtime
- **Lưu vào dictionary**: Cho phép lookup nhanh khi có request

**Cơ chế**:
- **Strategy Pattern**: Cho phép thay đổi hành vi (handler) mà không sửa code RpcServer
- **Dependency Injection**: ChatServer "inject" logic vào RpcServer

**Ví dụ sử dụng**:
```python
chat_server.register_handler('join_chat', self._handle_join_chat)
# Khi client gửi {"method": "join_chat", ...}
# RpcServer sẽ gọi self._handle_join_chat()
```

---

### 4. `start_server(self)`

**Mục đích**: Khởi động server và bắt đầu event loop.

**Ý tưởng thiết kế**:
- Chia nhỏ quá trình khởi động thành các bước rõ ràng
- Sử dụng try-finally để đảm bảo cleanup

**Tại sao làm như vậy**:
- **Chia thành các hàm nhỏ**: Dễ test, dễ debug, dễ hiểu
- **finally block**: Đảm bảo cleanup được gọi ngay cả khi có exception

**Cơ chế**:
- Exception propagation: Lỗi được log nhưng vẫn raise để caller biết
- Resource management: Socket và selector được đóng đúng cách

**Flow**:
```
1. _create_and_bind_socket()  → Tạo socket
2. _start_listening()         → Lắng nghe kết nối
3. _register_server_socket()  → Đăng ký với selector
4. _event_loop()              → Vòng lặp xử lý sự kiện
5. _cleanup()                 → Dọn dẹp tài nguyên
```

---

### 5. `_create_and_bind_socket(self)`

**Mục đích**: Tạo TCP socket và bind vào địa chỉ/port.

**Ý tưởng thiết kế**:
- Cấu hình socket để tối ưu cho server

**Tại sao làm như vậy**:
- **`socket.AF_INET`**: Sử dụng IPv4
- **`socket.SOCK_STREAM`**: Sử dụng TCP (đáng tin cậy, có thứ tự)
- **`SO_REUSEADDR`**: Cho phép bind ngay cả khi port đang trong trạng thái TIME_WAIT (sau khi tắt server)
- **`setblocking(False)`**: Socket non-blocking - không chặn luồng khi chờ dữ liệu

**Cơ chế**:
- **SO_REUSEADDR**: Giải quyết vấn đề "Address already in use" khi restart server nhanh
- **Non-blocking**: Cho phép selector giám sát nhiều socket cùng lúc

**Kiến thức chuyên sâu**:
- **TIME_WAIT state**: Sau khi đóng TCP connection, OS giữ port trong 30-120s để đảm bảo không có gói tin cũ
- **SO_REUSEADDR**: Bỏ qua TIME_WAIT, cho phép bind ngay lập tức

---

### 6. `_start_listening(self)`

**Mục đích**: Bắt đầu lắng nghe kết nối từ client.

**Ý tưởng thiết kế**:
- Đặt socket vào chế độ passive (lắng nghe)
- Đánh dấu server đang chạy

**Tại sao làm như vậy**:
- **`listen(MAX_CONNECTIONS)`**: Đặt kích thước backlog queue - số kết nối chờ được accept
- **`self.is_running = True`**: Flag để kiểm soát event loop

**Cơ chế**:
- **Backlog queue**: OS quản lý queue các kết nối đang chờ `accept()`
- Nếu queue đầy, client mới sẽ nhận connection refused

**Kiến thức chuyên sâu**:
- **SYN queue vs Accept queue**: TCP handshake tạo 2 queue riêng biệt
- **Backlog**: Kích thước accept queue, không phải số client tối đa

---

### 7. `_register_server_socket(self)`

**Mục đích**: Đăng ký server socket với selector để giám sát kết nối mới.

**Ý tưởng thiết kế**:
- Selector giám sát server socket để biết khi nào có client connect

**Tại sao làm như vậy**:
- **`EVENT_READ`**: Kết nối mới được coi là "dữ liệu có thể đọc" trên server socket
- **`data=None`**: Đánh dấu đây là server socket (khác với client socket có data=address)

**Cơ chế**:
- Selector sử dụng `data` field để phân biệt server socket và client socket
- Khi có event, kiểm tra `key.data is None` → đây là server socket → gọi `accept()`

---

### 8. `_event_loop(self)`

**Mục đích**: Vòng lặp chính xử lý tất cả I/O events.

**Ý tưởng thiết kế**:
- Single-threaded event loop
- Chỉ xử lý socket khi có sự kiện (không busy-wait)

**Tại sao làm như vậy**:
- **`selector.select(timeout=1)`**: Chờ tối đa 1 giây cho sự kiện
  - Timeout cho phép kiểm tra `is_running` định kỳ để thoát loop
  - Không timeout=None vì sẽ không thể dừng server gracefully
- **`key.data is None`**: Phân biệt server socket (accept) vs client socket (read)

**Cơ chế**:
- **Blocking call**: `select()` block cho đến khi có event hoặc timeout
- **Event notification**: OS thông báo socket nào sẵn sàng
- **No busy-waiting**: CPU không bị lãng phí khi không có event

**Flow**:
```
while is_running:
    events = selector.select(timeout=1)  ← Block ở đây
    for key, mask in events:
        if key.data is None:
            _accept_connection()  ← Kết nối mới
        else:
            _handle_client_event()  ← Dữ liệu từ client
```

**Kiến thức chuyên sâu**:
- **Level-triggered vs Edge-triggered**: Python selector mặc định dùng level-triggered (dễ dùng hơn)
- **Thundering herd**: Không xảy ra vì chỉ có 1 thread

---

### 9. `_accept_connection(self, server_socket)`

**Mục đích**: Chấp nhận kết nối mới từ client.

**Ý tưởng thiết kế**:
- Tách riêng logic accept để dễ test và maintain
- Xử lý exception riêng cho accept

**Tại sao làm như vậy**:
- **`accept()`**: Lấy kết nối từ backlog queue, trả về socket mới và địa chỉ client
- **`setblocking(False)`**: Đặt client socket thành non-blocking ngay sau khi accept
- **Try-except**: Accept có thể fail (ví dụ: client đóng kết nối ngay sau SYN)

**Cơ chế**:
- **New socket**: Mỗi client có socket riêng, server socket chỉ dùng để accept
- **Non-blocking**: Client socket phải non-blocking để selector hoạt động đúng

**Flow**:
```
Client connect → OS đưa vào backlog queue
                ↓
Selector phát hiện EVENT_READ trên server socket
                ↓
_accept_connection() gọi accept()
                ↓
Nhận client_socket và client_address
                ↓
_add_client() đăng ký client socket với selector
```

---

### 10. `_add_client(self, client_socket, client_address)`

**Mục đích**: Thêm client mới vào hệ thống quản lý.

**Ý tưởng thiết kế**:
- Tập trung tất cả logic "thêm client" vào một hàm
- Khởi tạo tất cả cấu trúc dữ liệu cần thiết

**Tại sao làm như vậy**:
- **`self.clients[client_socket] = client_address`**: Lưu mapping để tra cứu địa chỉ từ socket
- **`self.client_buffers[client_socket] = ""`**: Khởi tạo buffer rỗng cho client
- **`selector.register(client_socket, EVENT_READ, data=client_address)`**:
  - Đăng ký giám sát sự kiện đọc
  - Lưu address vào `data` để dễ truy cập trong event handler

**Cơ chế**:
- **Buffer per client**: Mỗi client có buffer riêng để xử lý partial messages
- **Selector registration**: Từ giờ selector sẽ thông báo khi client gửi dữ liệu

**Tại sao cần buffer**:
```
Client gửi: {"method": "join_chat", "params": {"username": "Alice"}}
TCP có thể chia thành nhiều gói:
  Gói 1: {"method": "join_
  Gói 2: chat", "params": {"user
  Gói 3: name": "Alice"}}

Buffer giúp ghép các gói lại thành message hoàn chỉnh
```

---

### 11. `_handle_client_event(self, key, mask)`

**Mục đích**: Xử lý sự kiện từ client (đọc dữ liệu hoặc phát hiện disconnect).

**Ý tưởng thiết kế**:
- Đọc dữ liệu từ socket
- Phân biệt giữa dữ liệu thật và disconnect (EOF)
- Xử lý nhiều loại exception khác nhau

**Tại sao làm như vậy**:
- **`recv(BUFFER_SIZE)`**: Đọc tối đa BUFFER_SIZE bytes
  - Trả về data nếu có dữ liệu
  - Trả về empty bytes `b''` nếu client đóng kết nối (EOF)
- **`if data:` vs `else:`**: Phân biệt dữ liệu thật vs disconnect
- **Multiple exception handlers**: Xử lý từng loại lỗi cụ thể

**Cơ chế**:
- **EOF detection**: `recv()` trả về empty khi client đóng kết nối gracefully
- **ConnectionResetError**: Client đóng kết nối đột ngột (không graceful)
- **UnicodeDecodeError**: Client gửi dữ liệu không phải UTF-8

**Exception handling**:
```python
try:
    data = recv()
    if data:
        process_message()  # Dữ liệu thật
    else:
        remove_client()    # EOF - client disconnect
except UnicodeDecodeError:
    remove_client()        # Dữ liệu không hợp lệ
except ConnectionResetError:
    remove_client()        # Client crash
except Exception:
    remove_client()        # Lỗi khác
```

---

### 12. `_process_message(self, message, client_socket, client_address)`

**Mục đích**: Xác định loại message và route đến handler phù hợp.

**Ý tưởng thiết kế**:
- Phát hiện loại message (JSON RPC vs plain text)
- Route đến handler tương ứng
- Từ chối message không hợp lệ

**Tại sao làm như vậy**:
- **`_detect_message_type()`**: Tách logic phát hiện loại message
- **Chỉ hỗ trợ JSON RPC**: Server này chỉ chấp nhận JSON RPC, từ chối plain text
- **Send error response**: Thông báo cho client biết lỗi

**Cơ chế**:
- **Message type detection**: Thử parse JSON, nếu thành công → JSON RPC
- **Early rejection**: Từ chối message không hợp lệ sớm, không xử lý tiếp

---

### 13. `_detect_message_type(self, message)`

**Mục đích**: Phát hiện message là JSON hay plain text.

**Ý tưởng thiết kế**:
- Thử parse JSON
- Nếu thành công → JSON, nếu fail → plain text

**Tại sao làm như vậy**:
- **Try-except**: Cách đơn giản nhất để kiểm tra JSON hợp lệ
- **Return enum**: Sử dụng enum thay vì string để tránh typo

**Cơ chế**:
- **JSON validation**: `json.loads()` sẽ raise `JSONDecodeError` nếu không hợp lệ
- **Exception as control flow**: Sử dụng exception để kiểm tra (Pythonic way)

---

### 14. `_handle_json_rpc(self, message, client_socket, client_address)`

**Mục đích**: Xử lý JSON RPC request - parse và gọi handler tương ứng.

**Ý tưởng thiết kế**:
- Parse JSON để lấy method và params
- Lookup handler từ dictionary
- Gọi handler và trả response

**Tại sao làm như vậy**:
- **`rpc_data.get('method')`**: Lấy tên method từ JSON
- **`rpc_data.get('params', {})`**: Lấy params, mặc định là dict rỗng nếu không có
- **`if method in self.message_handlers:`**: Kiểm tra method có được đăng ký không
- **`handler(params, client_socket, client_address)`**: Gọi handler với đầy đủ context

**Cơ chế**:
- **Dynamic dispatch**: Gọi hàm dựa trên tên method trong runtime
- **Handler signature**: Handler nhận (params, socket, address) để có đủ thông tin xử lý

**JSON RPC format**:
```json
Request:
{
    "method": "join_chat",
    "params": {"username": "Alice"}
}

Response (từ handler):
{
    "status": "success",
    "message": "Joined as Alice"
}
```

**Error handling**:
- **JSONDecodeError**: JSON không hợp lệ → PARSE_ERROR
- **Method not found**: Method không tồn tại → METHOD_NOT_FOUND
- **Exception**: Lỗi trong handler → INTERNAL_ERROR

---

### 15. `_send_json_response(self, client_socket, response)`

**Mục đích**: Gửi JSON response về client.

**Ý tưởng thiết kế**:
- Serialize dict thành JSON string
- Encode thành bytes và gửi qua socket

**Tại sao làm như vậy**:
- **`json.dumps(response)`**: Chuyển dict → JSON string
- **`encode('utf-8')`**: Chuyển string → bytes (socket chỉ gửi bytes)
- **`sendall()`**: Đảm bảo gửi hết dữ liệu (không như `send()` có thể gửi một phần)

**Cơ chế**:
- **sendall() vs send()**:
  - `send()`: Có thể gửi một phần, trả về số bytes đã gửi
  - `sendall()`: Loop cho đến khi gửi hết, hoặc raise exception

**Kiến thức chuyên sâu**:
- **TCP send buffer**: OS có buffer, `send()` copy vào buffer và return
- **Buffer full**: Nếu buffer đầy, `send()` chỉ gửi một phần
- **sendall()**: Tự động retry cho đến khi gửi hết

---

### 16. `_send_error_response(self, client_socket, error_message, error_code)`

**Mục đích**: Gửi error response theo chuẩn JSON RPC.

**Ý tưởng thiết kế**:
- Tạo error response với format chuẩn
- Reuse `_send_json_response()` để gửi

**Tại sao làm như vậy**:
- **Standardized error format**: Client biết cách parse error
- **Error codes**: Sử dụng mã lỗi chuẩn JSON RPC (-32xxx)
- **DRY principle**: Không duplicate code gửi JSON

**Error codes (JSON RPC standard)**:
```
-32700: Parse error (JSON không hợp lệ)
-32600: Invalid request (thiếu field bắt buộc)
-32601: Method not found (method không tồn tại)
-32602: Invalid params (params sai format)
-32603: Internal error (lỗi server)
```

---

### 17. `broadcast_message(self, message, sender_socket)`

**Mục đích**: Gửi plain text message đến tất cả client (trừ sender).

**Ý tưởng thiết kế**:
- Iterate qua tất cả client
- Bỏ qua sender
- Xử lý lỗi cho từng client riêng biệt

**Tại sao làm như vậy**:
- **`list(self.clients.items())`**: Tạo copy để tránh "dictionary changed size during iteration"
- **`if client_socket != sender_socket:`**: Không gửi lại cho người gửi
- **Try-except per client**: Lỗi ở 1 client không ảnh hưởng client khác
- **`_remove_client()` on error**: Client lỗi sẽ bị remove tự động

**Cơ chế**:
- **Broadcast pattern**: Gửi message đến nhiều recipient
- **Best-effort delivery**: Cố gắng gửi, nếu fail thì remove client

**Tại sao cần `list()`**:
```python
# SAI - sẽ raise RuntimeError
for client in self.clients.items():
    if error:
        del self.clients[client]  # Thay đổi dict đang iterate

# ĐÚNG - iterate trên copy
for client in list(self.clients.items()):
    if error:
        del self.clients[client]  # OK vì iterate trên copy
```

---

### 18. `send_to_client(self, client_socket, message)`

**Mục đích**: Gửi plain text message đến một client cụ thể.

**Ý tưởng thiết kế**:
- Gửi message đến 1 client
- Xử lý lỗi nhưng không remove client

**Tại sao làm như vậy**:
- **Không remove client**: Để caller quyết định xử lý lỗi
- **Log error**: Ghi lại lỗi để debug

**Sử dụng**:
- Gửi message riêng cho 1 client
- Ví dụ: Welcome message khi join

---

### 19. `send_json_to_client(self, client_socket, data)`

**Mục đích**: Gửi JSON message đến một client cụ thể.

**Ý tưởng thiết kế**:
- Tương tự `send_to_client()` nhưng cho JSON
- Serialize dict thành JSON trước khi gửi

**Tại sao làm như vậy**:
- **Convenience method**: Không cần serialize thủ công
- **Type safety**: Nhận dict, đảm bảo là JSON-serializable

---

### 20. `broadcast_json_message(self, data, sender_socket)`

**Mục đích**: Broadcast JSON message đến tất cả client (trừ sender).

**Ý tưởng thiết kế**:
- Serialize JSON một lần
- Gửi cùng JSON string đến tất cả client
- Xử lý lỗi cho từng client

**Tại sao làm như vậy**:
- **Serialize once**: Hiệu quả hơn serialize nhiều lần
- **`json.dumps()` outside loop**: Tối ưu performance
- **Remove failed clients**: Tự động dọn dẹp client lỗi

**Cơ chế**:
- **Optimization**: Serialize 1 lần cho N clients thay vì N lần
- **Error isolation**: Lỗi ở 1 client không ảnh hưởng broadcast

**Performance**:
```
Cách 1 (chậm):
for client in clients:
    json_str = json.dumps(data)  # Serialize N lần
    send(json_str)

Cách 2 (nhanh):
json_str = json.dumps(data)      # Serialize 1 lần
for client in clients:
    send(json_str)               # Chỉ gửi
```

---

### 21. `_remove_client(self, client_socket, client_address)`

**Mục đích**: Loại bỏ client khỏi hệ thống và giải phóng tài nguyên.

**Ý tưởng thiết kế**:
- Dọn dẹp tất cả tài nguyên liên quan đến client
- Xử lý exception để tránh crash khi cleanup

**Tại sao làm như vậy**:
- **Unregister từ selector trước**: Ngừng giám sát socket
- **Close socket**: Giải phóng file descriptor
- **Xóa khỏi dictionaries**: Giải phóng memory
- **Try-except cho từng bước**: Một bước fail không ảnh hưởng bước khác

**Cơ chế**:
- **Graceful cleanup**: Cố gắng cleanup tất cả, không raise exception
- **Order matters**: Unregister trước close để tránh selector access closed socket

**Tại sao cần try-except**:
```python
# Socket có thể đã bị close trước đó
try:
    selector.unregister(socket)  # Có thể raise nếu chưa register
except:
    pass  # Bỏ qua, không quan trọng

try:
    socket.close()  # Có thể raise nếu đã close
except:
    pass  # Bỏ qua, không quan trọng
```

**Cleanup checklist**:
1. ✅ Unregister khỏi selector
2. ✅ Close socket
3. ✅ Xóa khỏi `self.clients`
4. ✅ Xóa khỏi `self.client_buffers`

---

### 22. `get_connected_clients(self)`

**Mục đích**: Lấy danh sách địa chỉ của tất cả client đang kết nối.

**Ý tưởng thiết kế**:
- Trả về list các địa chỉ (không phải socket)
- Tạo copy để tránh caller modify internal state

**Tại sao làm như vậy**:
- **`list(self.clients.values())`**: Tạo copy của values
- **Return addresses, not sockets**: Caller không cần biết socket
- **Encapsulation**: Ẩn implementation detail (socket) khỏi caller

**Sử dụng**:
```python
# ChatServer dùng để map address → username
addresses = rpc_server.get_connected_clients()
for addr in addresses:
    username = user_names.get(addr, "Unknown")
```

---

### 23. `stop_server(self)`

**Mục đích**: Dừng server một cách graceful.

**Ý tưởng thiết kế**:
- Đặt flag để event loop thoát
- Không force close ngay lập tức

**Tại sao làm như vậy**:
- **`self.is_running = False`**: Event loop sẽ kiểm tra flag và thoát
- **Graceful shutdown**: Cho phép event loop hoàn thành iteration hiện tại
- **Print message**: Thông báo cho user biết server đang tắt

**Cơ chế**:
- **Flag-based control**: Event loop kiểm tra flag mỗi iteration
- **Timeout in select()**: Đảm bảo loop kiểm tra flag trong 1 giây

**Flow**:
```
User nhấn Ctrl+C
    ↓
Signal handler gọi stop_server()
    ↓
is_running = False
    ↓
Event loop kiểm tra flag
    ↓
Thoát loop
    ↓
_cleanup() được gọi (trong finally block)
```

---

### 24. `_cleanup(self)`

**Mục đích**: Dọn dẹp tất cả tài nguyên khi server tắt.

**Ý tưởng thiết kế**:
- Đóng tất cả client socket
- Đóng selector
- Đóng server socket
- Xóa tất cả data structures

**Tại sao làm như vậy**:
- **Close all clients first**: Thông báo cho client biết server tắt
- **Clear dictionaries**: Giải phóng memory
- **Close selector**: Giải phóng OS resources
- **Close server socket last**: Ngừng nhận kết nối mới

**Cơ chế**:
- **Try-except per operation**: Một lỗi không ngăn cleanup khác
- **list(self.clients.keys())**: Tạo copy để tránh modify during iteration

**Cleanup order**:
```
1. Close all client sockets
2. Clear self.clients dictionary
3. Clear self.client_buffers dictionary
4. Close selector
5. Close server socket
6. Log completion
```

**Tại sao order quan trọng**:
- Close clients trước để gửi FIN packet (graceful close)
- Close selector sau khi không còn socket nào được giám sát
- Close server socket cuối cùng để ngừng accept

---

## Tổng Kết Kiến Trúc

### Luồng Xử Lý Hoàn Chỉnh

#### 1. Khởi động Server
```
__init__() → Khởi tạo data structures
    ↓
start_server()
    ↓
_create_and_bind_socket() → Tạo TCP socket
    ↓
_start_listening() → Listen trên port
    ↓
_register_server_socket() → Đăng ký với selector
    ↓
_event_loop() → Bắt đầu xử lý events
```

#### 2. Client Kết Nối
```
Client connect → TCP handshake
    ↓
Selector phát hiện EVENT_READ trên server socket
    ↓
_accept_connection() → Accept kết nối
    ↓
_add_client() → Thêm vào clients dict, đăng ký với selector
```

#### 3. Client Gửi Message
```
Client gửi JSON RPC
    ↓
Selector phát hiện EVENT_READ trên client socket
    ↓
_handle_client_event() → Đọc dữ liệu
    ↓
_process_message() → Phát hiện loại message
    ↓
_handle_json_rpc() → Parse JSON, lookup handler
    ↓
handler() → ChatServer xử lý business logic
    ↓
_send_json_response() → Gửi response về client
    ↓
broadcast_json_message() → Broadcast đến client khác (nếu cần)
```

#### 4. Client Disconnect
```
Client đóng kết nối
    ↓
Selector phát hiện EVENT_READ
    ↓
_handle_client_event() → recv() trả về empty (EOF)
    ↓
_remove_client() → Cleanup tài nguyên
```

#### 5. Tắt Server
```
Ctrl+C → Signal
    ↓
stop_server() → is_running = False
    ↓
Event loop thoát
    ↓
_cleanup() → Đóng tất cả socket, giải phóng tài nguyên
```

---

## Các Pattern và Kỹ Thuật Được Sử Dụng

### 1. I/O Multiplexing Pattern
- **Vấn đề**: Làm sao xử lý nhiều client với 1 thread?
- **Giải pháp**: Selector giám sát nhiều socket, chỉ xử lý socket có event
- **Lợi ích**: Không cần thread per client, tiết kiệm tài nguyên

### 2. Strategy Pattern
- **Vấn đề**: Làm sao tách transport logic khỏi business logic?
- **Giải pháp**: Handler registration - ChatServer inject logic vào RpcServer
- **Lợi ích**: RpcServer không biết gì về chat logic, dễ test và maintain

### 3. Event-Driven Architecture
- **Vấn đề**: Làm sao tránh busy-waiting?
- **Giải pháp**: Selector block cho đến khi có event
- **Lợi ích**: CPU không bị lãng phí, scalable

### 4. Graceful Degradation
- **Vấn đề**: Lỗi ở 1 client có crash toàn server không?
- **Giải pháp**: Try-except per client, remove client khi lỗi
- **Lợi ích**: Server vẫn chạy ngay cả khi có client lỗi

### 5. Resource Management
- **Vấn đề**: Làm sao đảm bảo cleanup khi có exception?
- **Giải pháp**: Try-finally block, cleanup trong finally
- **Lợi ích**: Không leak socket/memory

---

## Ưu Điểm của Kiến Trúc Selector-Based

### 1. Hiệu Quả Tài Nguyên
- **Memory**: ~10 KB per client (vs ~8 MB với thread)
- **CPU**: Không context switching, không lock contention
- **File descriptors**: Chỉ cần 1 FD per client

### 2. Scalability
- **Hàng nghìn connections**: Có thể xử lý 10,000+ clients
- **Linear scaling**: Performance tăng tuyến tính với số client
- **No thread limit**: Không bị giới hạn bởi số thread tối đa

### 3. Simplicity
- **Single-threaded**: Không cần lock, không race condition
- **Deterministic**: Dễ debug, dễ reasoning
- **No deadlock**: Không có khả năng deadlock

### 4. Performance
- **Low latency**: Không overhead của context switching
- **High throughput**: Xử lý nhiều request/giây
- **Efficient I/O**: Sử dụng epoll/kqueue (OS-level optimization)

---

## Nhược Điểm và Giới Hạn

### 1. CPU-Bound Tasks
- **Vấn đề**: Handler chạy lâu sẽ block event loop
- **Giải pháp**: Handler phải nhanh, hoặc dùng thread pool cho CPU-bound task

### 2. Blocking Calls
- **Vấn đề**: Bất kỳ blocking call nào cũng block toàn bộ server
- **Giải pháp**: Tất cả I/O phải non-blocking

### 3. Single Core
- **Vấn đề**: Chỉ dùng 1 CPU core
- **Giải pháp**: Chạy nhiều process (multi-process) nếu cần dùng nhiều core

---

## Kết Luận

File `rpc_server.py` implement một **selector-based I/O multiplexing server** hiệu quả và scalable. Kiến trúc này phù hợp cho:

✅ **I/O-bound applications** (chat, web server, proxy)
✅ **High concurrency** (nhiều client đồng thời)
✅ **Low latency** (real-time messaging)
✅ **Resource-constrained environments** (ít RAM, ít CPU)

Không phù hợp cho:
❌ **CPU-bound tasks** (image processing, video encoding)
❌ **Long-running handlers** (phải tách ra thread riêng)

Đây là một implementation chất lượng production-ready với:
- Error handling đầy đủ
- Resource cleanup đúng cách
- Logging chi tiết
- Code dễ maintain và extend


