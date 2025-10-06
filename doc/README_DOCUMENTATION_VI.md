# Hướng Dẫn Sử Dụng Tài Liệu

## Tổng Quan

Thư mục `doc/` chứa tài liệu đầy đủ về hệ thống Chat Server, bao gồm tài liệu tiếng Anh và tiếng Việt.

## Cấu Trúc Tài Liệu

### 📚 Tài Liệu Tiếng Việt (Mới)

#### 1. **RPC_SERVER_DETAILED_ANALYSIS_VI.md** (845 dòng)
**Dành cho**: Developer muốn hiểu sâu về implementation

**Nội dung**:
- ✅ Phân tích chi tiết **từng hàm** trong `rpc_server.py`
- ✅ Giải thích **ý tưởng thiết kế** của mỗi hàm
- ✅ Lý do **tại sao** phải làm như vậy
- ✅ **Cơ chế hoạt động** của từng kỹ thuật
- ✅ **Kiến thức chuyên sâu** (epoll, kqueue, I/O multiplexing)
- ✅ **Design patterns** được sử dụng
- ✅ **Ưu nhược điểm** của kiến trúc

**Khi nào đọc**:
- Khi cần hiểu cách RpcServer hoạt động
- Khi muốn modify hoặc extend RpcServer
- Khi debug vấn đề liên quan đến networking
- Khi học về selector-based I/O

**Thời gian đọc**: 2-3 giờ (đọc kỹ)

---

#### 2. **RPC_SERVER_QUICK_REFERENCE_VI.md** (250 dòng)
**Dành cho**: Developer cần tra cứu nhanh

**Nội dung**:
- ✅ Bảng tóm tắt **tất cả các hàm**
- ✅ **Luồng xử lý** chính
- ✅ **Data structures** quan trọng
- ✅ **Ví dụ sử dụng** cụ thể
- ✅ **Tips và best practices**
- ✅ **Troubleshooting** các lỗi thường gặp

**Khi nào đọc**:
- Khi cần tra cứu nhanh một hàm
- Khi implement handler mới
- Khi gặp lỗi và cần fix nhanh
- Khi cần ví dụ code

**Thời gian đọc**: 15-30 phút

---

### 📚 Tài Liệu Tiếng Anh

#### 3. **API_SPECIFICATION.md** (534 dòng)
**Dành cho**: Client developer, API users

**Nội dung**:
- API endpoints (join_chat, send_message, get_users, leave_chat)
- Request/response format
- Error codes
- Message types
- Testing examples

**Khi nào đọc**:
- Khi develop client
- Khi integrate với server
- Khi cần hiểu JSON RPC protocol

---

#### 4. **server-class-diagram.md**
**Dành cho**: Architect, senior developers

**Nội dung**:
- Class diagram (Mermaid format)
- Relationships giữa RpcServer và ChatServer
- Methods và properties của mỗi class

**Khi nào đọc**:
- Khi cần overview về architecture
- Khi thiết kế feature mới
- Khi onboard developer mới

---

#### 5. **server-sequence-diagram.md**
**Dành cho**: Developer muốn hiểu flow

**Nội dung**:
- Sequence diagram (Mermaid format)
- Interaction giữa Client, RpcServer, ChatServer
- Message flow cho mỗi operation

**Khi nào đọc**:
- Khi cần hiểu flow của một operation
- Khi debug vấn đề về message routing
- Khi thiết kế test cases

---

## Lộ Trình Học Tập

### 🎯 Cho Người Mới Bắt Đầu

**Bước 1**: Đọc `RPC_SERVER_QUICK_REFERENCE_VI.md`
- Hiểu tổng quan về RpcServer
- Xem các ví dụ sử dụng
- Chạy thử server

**Bước 2**: Xem `server-sequence-diagram.md`
- Hiểu flow của các operations
- Visualize cách message được xử lý

**Bước 3**: Đọc `API_SPECIFICATION.md`
- Hiểu JSON RPC protocol
- Thử gọi API từ client

**Bước 4**: Đọc `RPC_SERVER_DETAILED_ANALYSIS_VI.md` (từng phần)
- Hiểu sâu về implementation
- Học các kỹ thuật advanced

---

### 🚀 Cho Developer Có Kinh Nghiệm

**Bước 1**: Xem `server-class-diagram.md`
- Nắm architecture nhanh

**Bước 2**: Đọc `RPC_SERVER_DETAILED_ANALYSIS_VI.md` (phần quan tâm)
- Focus vào các hàm cần modify
- Hiểu design decisions

**Bước 3**: Đọc `RPC_SERVER_QUICK_REFERENCE_VI.md`
- Tra cứu khi cần
- Reference cho best practices

---

### 🎓 Cho Người Muốn Học I/O Multiplexing

**Bước 1**: Đọc phần "Kiến Thức Cơ Bản" trong `RPC_SERVER_DETAILED_ANALYSIS_VI.md`
- Hiểu socket programming
- Hiểu selector và event-driven

**Bước 2**: Đọc phần phân tích các hàm:
- `_event_loop()` - Hiểu event loop
- `_accept_connection()` - Hiểu accept flow
- `_handle_client_event()` - Hiểu event handling

**Bước 3**: Đọc phần "Kiến Thức Chuyên Sâu"
- epoll/kqueue
- Level-triggered vs Edge-triggered
- Performance optimization

**Bước 4**: Xem diagrams
- Visualize toàn bộ flow
- So sánh với thread-based

---

## So Sánh Các Tài Liệu

| Tài Liệu | Độ Sâu | Thời Gian | Dành Cho |
|----------|---------|-----------|----------|
| **DETAILED_ANALYSIS** | ⭐⭐⭐⭐⭐ | 2-3h | Deep understanding |
| **QUICK_REFERENCE** | ⭐⭐⭐ | 15-30m | Quick lookup |
| **API_SPECIFICATION** | ⭐⭐ | 30m | API usage |
| **Class Diagram** | ⭐⭐ | 10m | Architecture overview |
| **Sequence Diagram** | ⭐⭐⭐ | 15m | Flow understanding |

---

## Câu Hỏi Thường Gặp

### Q1: Tôi nên đọc tài liệu nào trước?
**A**: Phụ thuộc mục đích:
- **Sử dụng API**: Đọc `API_SPECIFICATION.md`
- **Hiểu code**: Đọc `RPC_SERVER_QUICK_REFERENCE_VI.md` trước
- **Modify code**: Đọc `RPC_SERVER_DETAILED_ANALYSIS_VI.md`

### Q2: Tài liệu tiếng Việt có đầy đủ không?
**A**: Có! Tài liệu tiếng Việt phân tích chi tiết hơn cả tài liệu tiếng Anh, bao gồm:
- Giải thích từng hàm
- Ý tưởng thiết kế
- Kiến thức chuyên sâu
- Ví dụ cụ thể

### Q3: Tôi không hiểu selector là gì?
**A**: Đọc phần "Kiến Thức Cơ Bản Cần Thiết" trong `RPC_SERVER_DETAILED_ANALYSIS_VI.md`, sau đó xem diagram "So Sánh: Selector-Based vs Thread-Based"

### Q4: Làm sao để debug khi có lỗi?
**A**: 
1. Xem phần "Troubleshooting" trong `RPC_SERVER_QUICK_REFERENCE_VI.md`
2. Đọc phần phân tích hàm liên quan trong `DETAILED_ANALYSIS`
3. Check logs với level DEBUG

### Q5: Tôi muốn thêm feature mới, bắt đầu từ đâu?
**A**:
1. Xem `server-class-diagram.md` để hiểu architecture
2. Xem `server-sequence-diagram.md` để hiểu flow
3. Đọc phần "register_handler" trong `DETAILED_ANALYSIS`
4. Xem ví dụ trong `QUICK_REFERENCE`

---

## Tips Đọc Hiệu Quả

### ✅ Nên
- Đọc theo thứ tự từ tổng quan → chi tiết
- Chạy code trong khi đọc để hiểu rõ hơn
- Đặt breakpoint và debug để xem flow
- Vẽ diagram riêng để ghi nhớ
- Đọc nhiều lần các phần khó

### ❌ Không Nên
- Đọc toàn bộ một lúc (sẽ quá tải)
- Bỏ qua phần "Kiến Thức Cơ Bản"
- Đọc mà không chạy code
- Đọc mà không hiểu (hỏi hoặc research thêm)

---

## Đóng Góp

Nếu bạn tìm thấy lỗi hoặc muốn bổ sung:
1. Tạo issue mô tả vấn đề
2. Hoặc tạo pull request với sửa đổi
3. Hoặc liên hệ maintainer

---

## Tài Nguyên Bổ Sung

### Học Thêm Về I/O Multiplexing
- [Python selectors documentation](https://docs.python.org/3/library/selectors.html)
- [The C10K problem](http://www.kegel.com/c10k.html)
- [epoll vs select vs poll](https://man7.org/linux/man-pages/man7/epoll.7.html)

### Học Thêm Về Socket Programming
- [Python socket documentation](https://docs.python.org/3/library/socket.html)
- [Beej's Guide to Network Programming](https://beej.us/guide/bgnet/)
- [TCP/IP Illustrated](https://en.wikipedia.org/wiki/TCP/IP_Illustrated)

### Học Thêm Về JSON RPC
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [JSON RPC Best Practices](https://www.simple-is-better.org/rpc/)

---

## Kết Luận

Tài liệu được tổ chức theo nhiều cấp độ để phù hợp với mọi đối tượng:
- **Quick Reference**: Tra cứu nhanh
- **Detailed Analysis**: Hiểu sâu
- **API Spec**: Sử dụng API
- **Diagrams**: Visualize architecture

Chúc bạn học tốt! 🚀


