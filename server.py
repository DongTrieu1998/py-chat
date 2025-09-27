import socket
from typing import Optional, Tuple


class ChatServer:
    """
    A simple TCP chat server that handles client connections and enables
    bidirectional communication between server and client.
    """

    def __init__(self, host: str = '127.0.0.1', port: int = 65432):
        """
        Initialize the chat server with host and port configuration.

        Args:
            host (str): The IP address to bind the server to (default: localhost)
            port (int): The port number to listen on (default: 65432)
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_running = False

    def start_server(self) -> None:
        """
        Start the server and begin listening for client connections.
        This method creates the socket, binds it to the address, and starts listening.
        """
        try:
            # Create a TCP socket using IPv4
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Allow socket address reuse (helpful for development)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind the socket to the specified host and port
            self.socket.bind((self.host, self.port))

            # Start listening for incoming connections (max 1 pending connection)
            self.socket.listen(1)
            self.is_running = True

            print(f"🚀 Server started and listening on {self.host}:{self.port}")
            print("Waiting for client connections...")

            # Accept and handle client connections
            self._accept_connections()

        except Exception as e:
            print(f"❌ Error starting server: {e}")
        finally:
            self._cleanup()

    def _accept_connections(self) -> None:
        """
        Accept incoming client connections and handle them.
        Currently handles one client at a time.
        """
        while self.is_running:
            try:
                # Accept a client connection (blocking call)
                client_socket, client_address = self.socket.accept()
                print(f"✅ New client connected from {client_address}")

                # Handle the client communication
                self._handle_client(client_socket, client_address)

            except socket.error as e:
                if self.is_running:  # Only show error if server is supposed to be running
                    print(f"❌ Error accepting connection: {e}")
                break

    def _handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        """
        Handle communication with a connected client.

        Args:
            client_socket: The socket object for the connected client
            client_address: Tuple containing client's IP address and port
        """
        try:
            with client_socket:
                print(f"💬 Chat session started with {client_address}")
                print("Type your messages to send to the client. Press Ctrl+C to disconnect.")

                while True:
                    # Receive message from client
                    message_data = client_socket.recv(1024)

                    # Check if client disconnected
                    if not message_data:
                        print(f"🔌 Client {client_address} disconnected")
                        break

                    # Decode and display client message
                    client_message = message_data.decode('utf-8')
                    print(f"📨 Client: {client_message}")

                    # Get server response from user input
                    server_reply = input("📤 Server reply: ")

                    # Send reply back to client
                    client_socket.sendall(server_reply.encode('utf-8'))

        except ConnectionResetError:
            print(f"🔌 Client {client_address} disconnected unexpectedly")
        except KeyboardInterrupt:
            print(f"\n🛑 Disconnecting from client {client_address}")
        except Exception as e:
            print(f"❌ Error handling client {client_address}: {e}")

    def stop_server(self) -> None:
        """
        Stop the server and close the socket.
        """
        print("\n🛑 Shutting down server...")
        self.is_running = False
        if self.socket:
            self.socket.close()

    def _cleanup(self) -> None:
        """
        Clean up resources when server stops.
        """
        if self.socket:
            self.socket.close()
        print("🧹 Server cleanup completed")


def main():
    """
    Main function to create and start the chat server.
    """
    # Create server instance with default settings
    server = ChatServer()

    try:
        # Start the server
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Server interrupted by user")
    finally:
        # Ensure proper cleanup
        server.stop_server()


if __name__ == "__main__":
    main()
