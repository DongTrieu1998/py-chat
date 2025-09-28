import socket
import threading
import sys
from typing import Optional


class ChatClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 65432, client_name: str = None):
        self.host = host
        self.port = port
        self.client_name = client_name or f"Client-{id(self)}"
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        self.running = False

    def connect_to_server(self, bind_address: tuple = None) -> bool:
        """
        Connect to server, optionally binding to specific local address/port.
        
        Args:
            bind_address: Tuple of (local_ip, local_port) to bind client socket to
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Bind to specific local address/port if provided
            if bind_address:
                self.socket.bind(bind_address)
                print(f"🔗 Binding client to local address {bind_address}")
            
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            self.running = True

            # Get actual local address after connection
            local_addr = self.socket.getsockname()
            print(f"✅ {self.client_name} connected to server at {self.host}:{self.port}")
            print(f"📍 Local address: {local_addr}")
            return True

        except OSError as e:
            if "Address already in use" in str(e):
                print(f"❌ Local address {bind_address} already in use")
            else:
                print(f"❌ Connection error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error connecting to server: {e}")
            return False

    def start_chat(self) -> None:
        if not self.is_connected or not self.socket:
            print("❌ Not connected to server. Please connect first.")
            return

        try:
            print(f"💬 Chat session started for {self.client_name}!")
            print("Type your messages and press Enter to send.")
            print("Type 'quit' or 'exit' to leave the chat.\n")

            # Start receiver thread for incoming messages
            receiver_thread = threading.Thread(target=self._receive_messages)
            receiver_thread.daemon = True
            receiver_thread.start()

            # Handle user input in main thread
            self._handle_user_input()

        except KeyboardInterrupt:
            print(f"\n🛑 {self.client_name} interrupted by user")
        except Exception as e:
            print(f"❌ Error during chat: {e}")
        finally:
            self.disconnect()

    def _receive_messages(self) -> None:
        try:
            while self.running and self.is_connected:
                data = self.socket.recv(1024)
                
                if not data:
                    print("🔌 Server closed the connection")
                    self.running = False
                    break

                message = data.decode('utf-8')
                print(f"\n📨 {message}")
                print(f"📤 {self.client_name}: ", end="", flush=True)

        except ConnectionResetError:
            if self.running:
                print("\n❌ Server disconnected unexpectedly")
            self.running = False
        except Exception as e:
            if self.running:
                print(f"\n❌ Error receiving message: {e}")
            self.running = False

    def _handle_user_input(self) -> None:
        try:
            while self.running and self.is_connected:
                user_message = input(f"📤 {self.client_name}: ")

                if user_message.lower() in ['quit', 'exit', '']:
                    print(f"👋 {self.client_name} ending chat session...")
                    break

                # Prefix message with client name
                formatted_message = f"[{self.client_name}]: {user_message}"
                if not self._send_message(formatted_message):
                    break

        except EOFError:
            print(f"\n👋 {self.client_name} ending chat session...")
        except KeyboardInterrupt:
            print(f"\n🛑 {self.client_name} interrupted by user")

    def _send_message(self, message: str) -> bool:
        try:
            self.socket.sendall(message.encode('utf-8'))
            return True
        except ConnectionResetError:
            print("❌ Server disconnected unexpectedly")
            self.running = False
            return False
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False

    def disconnect(self) -> None:
        self.running = False
        self.is_connected = False
        
        if self.socket:
            try:
                self.socket.close()
                print(f"🔌 {self.client_name} disconnected from server")
            except Exception as e:
                print(f"❌ Error during disconnect: {e}")

        self.socket = None


def main():
    # Parse command line arguments for custom configuration
    if len(sys.argv) >= 2:
        client_name = sys.argv[1]
    else:
        client_name = input("Enter client name (or press Enter for auto-generated): ").strip()
        if not client_name:
            client_name = None

    # Optional: bind to specific local port
    local_port = None
    if len(sys.argv) >= 3:
        try:
            local_port = int(sys.argv[2])
        except ValueError:
            print("Invalid port number provided")
            return

    # Create client instance
    client = ChatClient(client_name=client_name)

    try:
        # Determine bind address
        bind_address = None
        if local_port:
            bind_address = ('127.0.0.1', local_port)

        if client.connect_to_server(bind_address):
            client.start_chat()
        else:
            print("❌ Failed to connect to server. Exiting...")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()