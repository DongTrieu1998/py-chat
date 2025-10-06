#!/usr/bin/env python3

from rpc_server import RpcServer
from chat_server import ChatServer


def main():
    rpc_server = RpcServer(host='127.0.0.1', port=65432)
    chat_server = ChatServer(rpc_server)

    try:
        print("Starting Chat Application...")
        print("=" * 50)
        chat_server.start()

    except KeyboardInterrupt:
        print("\nServer interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print("Cleaning up...")
        chat_server.stop()
        print("Server shutdown completed")


if __name__ == "__main__":
    main()
