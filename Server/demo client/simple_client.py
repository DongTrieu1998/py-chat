#!/usr/bin/env python3

import socket
import threading
import json
import sys


class SimpleChatClient:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.socket = None
        self.is_connected = False
        self.username = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            print(f"Connected to server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def join_chat(self, username):
        self.username = username
        join_request = {
            'method': 'join_chat',
            'params': {'username': username}
        }

        try:
            self.socket.sendall(json.dumps(join_request).encode('utf-8'))
            print(f"Joined chat as {username}")
        except Exception as e:
            print(f"Failed to join chat: {e}")

    def send_message(self, message):
        if not self.is_connected:
            print("Not connected to server")
            return

        json_request = {
            'method': 'send_message',
            'params': {'message': message}
        }

        try:
            self.socket.sendall(json.dumps(json_request).encode('utf-8'))
        except Exception as e:
            print(f"Failed to send message: {e}")

    def get_users(self):
        users_request = {
            'method': 'get_users',
            'params': {}
        }

        try:
            self.socket.sendall(json.dumps(users_request).encode('utf-8'))
        except Exception as e:
            print(f"Failed to get users: {e}")

    def listen_for_messages(self):
        buffer = ""
        while self.is_connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if data:
                    buffer += data
                    while buffer:
                        try:
                            decoder = json.JSONDecoder()
                            json_data, idx = decoder.raw_decode(buffer)
                            buffer = buffer[idx:].lstrip()
                            self._handle_json_message(json_data)
                        except json.JSONDecodeError:
                            break
                else:
                    break
            except Exception as e:
                if self.is_connected:
                    print(f"Error receiving message: {e}")
                break

    def disconnect(self):
        if self.is_connected:
            try:
                leave_request = {
                    'method': 'leave_chat',
                    'params': {}
                }
                self.socket.sendall(json.dumps(leave_request).encode('utf-8'))
            except:
                pass

            self.is_connected = False
            if self.socket:
                self.socket.close()
            print("Disconnected from server")

    def _handle_json_message(self, json_data):
        if 'status' in json_data:
            status = json_data['status']
            message = json_data.get('message', '')

            if status == 'success':
                if 'users' in json_data:
                    users = json_data['users']
                    count = json_data.get('count', len(users))
                    print(f"{message}")
                    print(f"Online users ({count}): {', '.join([u.get('username', u) if isinstance(u, dict) else u for u in users])}")
                elif message and not message.startswith('Message sent'):
                    print(f"{message}")
            elif status == 'error':
                print(f"Error: {message}")

        elif 'type' in json_data:
            msg_type = json_data['type']
            message = json_data.get('message', '')
            username = json_data.get('username', 'Unknown')

            if msg_type == 'chat':
                print(f"{username}: {message}")
            elif msg_type == 'system':
                print(f"{message}")
            else:
                print(f"[{msg_type}] {username}: {message}")

        elif 'error' in json_data:
            error_msg = json_data.get('error', 'Unknown error')
            error_code = json_data.get('code', 0)
            print(f"RPC Error ({error_code}): {error_msg}")

        else:
            print(f"Server response: {json_data}")

    def run(self):
        if not self.connect():
            return

        username = input("Enter your username: ").strip()
        if not username:
            username = f"User_{self.socket.getsockname()[1]}"

        self.join_chat(username)

        listen_thread = threading.Thread(target=self.listen_for_messages)
        listen_thread.daemon = True
        listen_thread.start()

        print("\nChat Commands:")
        print("  - Type message to send")
        print("  - /users - Get online users")
        print("  - /quit - Exit chat")
        print("-" * 40)

        try:
            while self.is_connected:
                message = input().strip()

                if not message:
                    continue

                if message == '/quit':
                    break
                elif message == '/users':
                    self.get_users()
                else:
                    self.send_message(message)

        except KeyboardInterrupt:
            print("\nClient interrupted")
        finally:
            self.disconnect()


def main():
    print("Simple Chat Client (JSON API Only)")
    print("=" * 40)

    client = SimpleChatClient()
    client.run()


if __name__ == "__main__":
    main()
