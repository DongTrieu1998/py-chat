import socket
from typing import Optional


class ChatClient:
    """
    A simple TCP chat client that connects to a server and enables
    bidirectional communication between client and server.
    """

    def __init__(self, host: str = '127.0.0.1', port: int = 65432):
        """
        Initialize the chat client with server connection details.

        Args:
            host (str): The server's IP address to connect to (default: localhost)
            port (int): The server's port number to connect to (default: 65432)
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_connected = False

    def connect_to_server(self) -> bool:
        """
        Establish connection to the server.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create a TCP socket using IPv4
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect to the server
            self.socket.connect((self.host, self.port))
            self.is_connected = True

            print(f"✅ Successfully connected to server at {self.host}:{self.port}")
            return True

        except ConnectionRefusedError:
            print(f"❌ Connection refused. Make sure the server is running on {self.host}:{self.port}")
            return False
        except socket.gaierror:
            print(f"❌ Invalid host address: {self.host}")
            return False
        except Exception as e:
            print(f"❌ Error connecting to server: {e}")
            return False

    def start_chat(self) -> None:
        """
        Start the chat session with the server.
        Handles sending messages to server and receiving replies.
        """
        if not self.is_connected or not self.socket:
            print("❌ Not connected to server. Please connect first.")
            return

        try:
            print("💬 Chat session started!")
            print("Type your messages and press Enter to send.")
            print("Press Enter with empty message to quit.\n")

            while True:
                # Get message from user
                user_message = input("📤 Your message: ")

                # Check if user wants to quit (empty message)
                if not user_message.strip():
                    print("👋 Ending chat session...")
                    break

                # Send message to server
                if not self._send_message(user_message):
                    break

                # Receive and display server response
                server_response = self._receive_message()
                if server_response is None:
                    break

                print(f"📨 Server: {server_response}")

        except KeyboardInterrupt:
            print("\n🛑 Chat interrupted by user")
        except Exception as e:
            print(f"❌ Error during chat: {e}")
        finally:
            self.disconnect()

    def _send_message(self, message: str) -> bool:
        """
        Send a message to the server.

        Args:
            message (str): The message to send

        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            # Encode message to bytes and send to server
            self.socket.sendall(message.encode('utf-8'))
            return True
        except ConnectionResetError:
            print("❌ Server disconnected unexpectedly")
            return False
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False

    def _receive_message(self) -> Optional[str]:
        """
        Receive a message from the server.

        Returns:
            str: The received message, or None if error occurred
        """
        try:
            # Receive data from server (up to 1024 bytes)
            data = self.socket.recv(1024)

            # Check if server closed connection
            if not data:
                print("🔌 Server closed the connection")
                return None

            # Decode bytes to string and return
            return data.decode('utf-8')

        except ConnectionResetError:
            print("❌ Server disconnected unexpectedly")
            return None
        except Exception as e:
            print(f"❌ Error receiving message: {e}")
            return None

    def disconnect(self) -> None:
        """
        Disconnect from the server and clean up resources.
        """
        if self.socket:
            try:
                self.socket.close()
                print("🔌 Disconnected from server")
            except Exception as e:
                print(f"❌ Error during disconnect: {e}")

        self.is_connected = False
        self.socket = None

    def is_connection_active(self) -> bool:
        """
        Check if the connection to server is still active.

        Returns:
            bool: True if connected, False otherwise
        """
        return self.is_connected and self.socket is not None


def main():
    """
    Main function to create and run the chat client.
    """
    # Create client instance with default server settings
    client = ChatClient()

    try:
        # Attempt to connect to server
        if client.connect_to_server():
            # Start chat session if connection successful
            client.start_chat()
        else:
            print("❌ Failed to connect to server. Exiting...")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    finally:
        # Ensure proper cleanup
        client.disconnect()


if __name__ == "__main__":
    main()
