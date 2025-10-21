#!/usr/bin/env python3

import socket
import threading
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext
import queue


class ChatClient:
    """Chat client logic"""
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.socket = None
        self.is_connected = False
        self.username = None
        self.message_queue = queue.Queue()
        self.message_handler = None  # Will be set by window

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            return True
        except Exception:
            return False

    def join_chat(self, username):
        self.username = username
        join_request = {
            'method': 'join_chat',
            'params': {'username': username}
        }
        try:
            self.socket.sendall(json.dumps(join_request).encode('utf-8'))
            return True
        except Exception:
            return False

    def send_message(self, message):
        if not self.is_connected:
            return
        json_request = {
            'method': 'send_message',
            'params': {'message': message}
        }
        try:
            self.socket.sendall(json.dumps(json_request).encode('utf-8'))
        except Exception:
            pass

    def get_users(self):
        users_request = {
            'method': 'get_users',
            'params': {}
        }
        try:
            self.socket.sendall(json.dumps(users_request).encode('utf-8'))
        except Exception:
            pass

    def create_group(self, group_name=''):
        """Create a new group"""
        request = {
            'method': 'create_group',
            'params': {'group_name': group_name}
        }
        try:
            self.socket.sendall(json.dumps(request).encode('utf-8'))
        except Exception:
            pass

    def join_group(self, group_name):
        """Join an existing group"""
        request = {
            'method': 'join_group',
            'params': {'group_name': group_name}
        }
        try:
            self.socket.sendall(json.dumps(request).encode('utf-8'))
        except Exception:
            pass

    def leave_group(self):
        """Leave current group"""
        request = {
            'method': 'leave_group',
            'params': {}
        }
        try:
            self.socket.sendall(json.dumps(request).encode('utf-8'))
        except Exception:
            pass

    def get_group_members(self):
        """Get members of current group"""
        request = {
            'method': 'get_group_members',
            'params': {}
        }
        try:
            self.socket.sendall(json.dumps(request).encode('utf-8'))
        except Exception:
            pass

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
                            self.message_queue.put(json_data)
                        except json.JSONDecodeError:
                            break
                else:
                    break
            except Exception:
                if self.is_connected:
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





class LoginWindow:
    """Login window for username input"""
    def __init__(self, on_login_callback):
        self.on_login_callback = on_login_callback
        self.window = tk.Tk()
        self.window.title("Chat Login")
        self.window.geometry("500x300")
        self.window.resizable(False, False)
        self.window.configure(bg="#F0F0F0")

        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.window.winfo_screenheight() // 2) - (300 // 2)
        self.window.geometry(f"500x300+{x}+{y}")

        self._create_widgets()

    def _create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.window, bg="#F0F0F0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        # Title
        title_label = tk.Label(
            main_frame,
            text="💬 Chat Login",
            font=("Segoe UI", 24, "bold"),
            bg="#F0F0F0",
            fg="#333333"
        )
        title_label.pack(pady=(0, 30))

        # Username entry
        self.username_entry = tk.Entry(
            main_frame,
            font=("Segoe UI", 14),
            bg="#FFFFFF",
            fg="#333333",
            relief=tk.SOLID,
            bd=1
        )
        self.username_entry.pack(fill=tk.X, ipady=10, pady=(0, 20))
        self.username_entry.insert(0, "Enter your username...")
        self.username_entry.config(fg="#999999")
        self.username_entry.bind('<FocusIn>', self._on_entry_focus)
        self.username_entry.bind('<FocusOut>', self._on_entry_unfocus)
        self.username_entry.bind('<Return>', lambda e: self._on_login())

        # Login button
        self.login_btn = tk.Button(
            main_frame,
            text="Join Chat",
            font=("Segoe UI", 14, "bold"),
            bg="#4A90E2",
            fg="#FFFFFF",
            activebackground="#357ABD",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self._on_login
        )
        self.login_btn.pack(fill=tk.X, ipady=12)

        # Focus on entry
        self.window.after(100, self.username_entry.focus_set)

    def _on_entry_focus(self, event):
        if self.username_entry.get() == "Enter your username...":
            self.username_entry.delete(0, tk.END)
            self.username_entry.config(fg="#333333")

    def _on_entry_unfocus(self, event):
        if not self.username_entry.get():
            self.username_entry.insert(0, "Enter your username...")
            self.username_entry.config(fg="#999999")

    def _on_login(self):
        username = self.username_entry.get().strip()
        if not username or username == "Enter your username...":
            messagebox.showwarning("Invalid Input", "Please enter a username")
            self.username_entry.delete(0, tk.END)
            self.username_entry.config(fg="#333333")
            self.username_entry.focus_set()
            return
        self.window.destroy()
        self.on_login_callback(username)

    def run(self):
        self.window.mainloop()


class LobbyWindow:
    """Lobby window to show online users and create/join groups"""
    def __init__(self, username, client):
        self.username = username
        self.client = client
        self.window = tk.Tk()
        self.window.title("Chat Lobby")
        self.window.geometry("600x500")
        self.window.resizable(False, False)
        self.window.configure(bg="#F0F0F0")

        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"600x500+{x}+{y}")

        self.chat_window = None

        # Set message handler to this window
        self.client.message_handler = self._handle_message

        self._create_widgets()

        # Start processing messages
        self.window.after(100, self._process_messages)

        # Auto refresh users
        self.window.after(500, self._auto_refresh_users)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.window, bg="#F0F0F0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        tk.Label(
            main_frame,
            text=f"👋 Welcome, {self.username}!",
            font=("Segoe UI", 18, "bold"),
            bg="#F0F0F0",
            fg="#333333"
        ).pack(pady=(0, 20))

        # Buttons frame
        buttons_frame = tk.Frame(main_frame, bg="#F0F0F0")
        buttons_frame.pack(fill=tk.X, pady=(0, 20))

        # Create Group button
        tk.Button(
            buttons_frame,
            text="➕ Create Group Chat",
            command=self._create_group,
            bg="#4A90E2",
            fg="#FFFFFF",
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            width=20
        ).pack(side=tk.LEFT, padx=(0, 10), ipady=10)

        # Join Group button
        tk.Button(
            buttons_frame,
            text="🚪 Join Group Chat",
            command=self._join_group,
            bg="#27AE60",
            fg="#FFFFFF",
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            width=20
        ).pack(side=tk.LEFT, ipady=10)

        # Online users section
        tk.Label(
            main_frame,
            text="👥 Online Users",
            font=("Segoe UI", 14, "bold"),
            bg="#F0F0F0",
            fg="#333333"
        ).pack(anchor=tk.W, pady=(0, 10))

        # Users listbox
        users_frame = tk.Frame(main_frame, bg="#FFFFFF", relief=tk.SOLID, bd=1)
        users_frame.pack(fill=tk.BOTH, expand=True)

        self.users_listbox = tk.Listbox(
            users_frame,
            font=("Segoe UI", 11),
            bg="#FFFFFF",
            fg="#333333",
            relief=tk.FLAT,
            bd=0
        )
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _create_group(self):
        """Show dialog to create a new group"""
        # Simple dialog to enter group name
        dialog = tk.Toplevel(self.window)
        dialog.title("Create Group")
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.configure(bg="#F0F0F0")

        # Center dialog
        dialog.transient(self.window)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Enter Group Name:",
            font=("Segoe UI", 12),
            bg="#F0F0F0",
            fg="#333333"
        ).pack(pady=(20, 10))

        entry = tk.Entry(
            dialog,
            font=("Segoe UI", 12),
            bg="#FFFFFF",
            fg="#333333",
            relief=tk.SOLID,
            bd=1
        )
        entry.pack(fill=tk.X, padx=40, ipady=8)
        entry.focus_set()

        # Info label
        tk.Label(
            dialog,
            text="(Leave empty for auto-generated name)",
            font=("Segoe UI", 9),
            bg="#F0F0F0",
            fg="#999999"
        ).pack(pady=(5, 0))

        def on_create():
            group_name = entry.get().strip()
            self.client.create_group(group_name)
            dialog.destroy()

        entry.bind('<Return>', lambda e: on_create())

        tk.Button(
            dialog,
            text="Create",
            command=on_create,
            bg="#4A90E2",
            fg="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(pady=15, ipady=8, ipadx=30)

    def _join_group(self):
        """Show dialog to join a group"""
        # Simple dialog to enter group name
        dialog = tk.Toplevel(self.window)
        dialog.title("Join Group")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.configure(bg="#F0F0F0")

        # Center dialog
        dialog.transient(self.window)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Enter Group Name:",
            font=("Segoe UI", 12),
            bg="#F0F0F0",
            fg="#333333"
        ).pack(pady=(20, 10))

        entry = tk.Entry(
            dialog,
            font=("Segoe UI", 12),
            bg="#FFFFFF",
            fg="#333333",
            relief=tk.SOLID,
            bd=1
        )
        entry.pack(fill=tk.X, padx=40, ipady=8)
        entry.focus_set()

        def on_join():
            group_name = entry.get().strip()
            if group_name:
                self.client.join_group(group_name)
                dialog.destroy()

        entry.bind('<Return>', lambda e: on_join())

        tk.Button(
            dialog,
            text="Join",
            command=on_join,
            bg="#27AE60",
            fg="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(pady=20, ipady=8, ipadx=30)

    def _auto_refresh_users(self):
        """Auto refresh users every 3 seconds"""
        if self.client.is_connected:
            self.client.get_users()
            self.window.after(3000, self._auto_refresh_users)

    def _update_users_list(self, users):
        """Update the users listbox"""
        self.users_listbox.delete(0, tk.END)
        for user in users:
            username = user.get('username', user) if isinstance(user, dict) else user
            display_name = username + (" (You)" if username == self.username else "")
            self.users_listbox.insert(tk.END, display_name)

    def _process_messages(self):
        """Process messages from queue"""
        try:
            while True:
                json_data = self.client.message_queue.get_nowait()
                # Only process if this window's handler is active
                if self.client.message_handler == self._handle_message:
                    self._handle_message(json_data)
        except queue.Empty:
            pass
        finally:
            if self.client.is_connected:
                self.window.after(100, self._process_messages)

    def _handle_message(self, json_data):
        """Handle incoming JSON messages"""
        # Handle status responses
        if 'status' in json_data:
            status = json_data['status']

            if status == 'success':
                # Handle group creation/join
                if 'group_name' in json_data:
                    group_name = json_data['group_name']
                    members = json_data.get('members', [])

                    # Open chat window for this group
                    self.window.withdraw()  # Hide lobby
                    self.chat_window = ChatWindow(self.username, self.client, group_name, members, self)
                    # Don't call run() - Toplevel windows don't need mainloop()

                # Handle users list
                elif 'users' in json_data:
                    users = json_data['users']
                    self._update_users_list(users)

            elif status == 'error':
                message = json_data.get('message', 'Unknown error')
                messagebox.showerror("Error", message)

    def show(self):
        """Show the lobby window again"""
        # Set message handler back to lobby
        self.client.message_handler = self._handle_message
        self.window.deiconify()

        # Refresh users list
        self.client.get_users()

    def _on_close(self):
        """Handle window close"""
        self.client.disconnect()
        self.window.destroy()

    def run(self):
        self.window.mainloop()


class ChatWindow:
    """Main chat window for group chat"""
    def __init__(self, username, client, group_name, members, lobby_window):
        self.username = username
        self.client = client
        self.group_name = group_name
        self.lobby_window = lobby_window
        self.is_active = True  # Flag to track if window is active
        self.refresh_job = None  # Store refresh job ID

        # Create window
        self.window = tk.Toplevel()
        self.window.title(f"User: {username}")
        self.window.geometry("1000x650")
        self.window.configure(bg="#F0F0F0")

        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.window.winfo_screenheight() // 2) - (650 // 2)
        self.window.geometry(f"1000x650+{x}+{y}")

        # Set message handler to this window
        self.client.message_handler = self._handle_message

        self._create_widgets()

        # Initialize members list
        self._update_users_list(members)

        # Start processing messages
        self.window.after(100, self._process_messages)

        # Auto refresh group members every 3 seconds
        self.refresh_job = self.window.after(1000, self._auto_refresh_members)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        # Main container
        main_container = tk.Frame(self.window, bg="#F0F0F0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Group members list
        left_panel = tk.Frame(main_container, bg="#FFFFFF", relief=tk.SOLID, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # Back button
        tk.Button(
            left_panel,
            text="⬅ Back to Lobby",
            command=self._back_to_lobby,
            bg="#E74C3C",
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(fill=tk.X, padx=5, pady=5)

        # Members header
        tk.Label(
            left_panel,
            text="👥 Group Members",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#333333"
        ).pack(pady=10)

        # Members listbox
        self.users_listbox = tk.Listbox(
            left_panel,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#333333",
            relief=tk.FLAT,
            bd=0,
            width=20
        )
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # Right panel - Chat area
        right_panel = tk.Frame(main_container, bg="#F0F0F0")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Chat header
        header_frame = tk.Frame(right_panel, bg="#FFFFFF", relief=tk.SOLID, bd=1)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(
            header_frame,
            text=f"💬 Chat - {self.group_name}",
            font=("Segoe UI", 12, "bold"),
            bg="#FFFFFF",
            fg="#333333"
        ).pack(pady=10)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            right_panel,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            state=tk.DISABLED,
            bg="#F5F5F5",
            fg="#333333",
            relief=tk.SOLID,
            bd=1
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Configure tags for chat bubbles
        self.chat_display.tag_config("system", foreground="#999999", font=("Segoe UI", 9, "italic"), justify="center")

        # Self message (right aligned, blue bubble)
        self.chat_display.tag_config("self_bubble",
                                     background="#4A90E2",
                                     foreground="#FFFFFF",
                                     font=("Segoe UI", 10),
                                     relief=tk.RAISED,
                                     borderwidth=1,
                                     justify="right")
        self.chat_display.tag_config("self_align", justify="right")

        # Other message (left aligned, white bubble)
        self.chat_display.tag_config("other_bubble",
                                     background="#FFFFFF",
                                     foreground="#333333",
                                     font=("Segoe UI", 10),
                                     relief=tk.RAISED,
                                     borderwidth=1,
                                     justify="left")
        self.chat_display.tag_config("other_align", justify="left")

        # Username tags
        self.chat_display.tag_config("username_self",
                                     foreground="#4A90E2",
                                     font=("Segoe UI", 8, "bold"),
                                     justify="right")
        self.chat_display.tag_config("username_other",
                                     foreground="#666666",
                                     font=("Segoe UI", 8, "bold"),
                                     justify="left")

        # Message input area
        input_frame = tk.Frame(right_panel, bg="#FFFFFF", relief=tk.SOLID, bd=1)
        input_frame.pack(fill=tk.X)

        input_inner = tk.Frame(input_frame, bg="#FFFFFF")
        input_inner.pack(fill=tk.X, padx=10, pady=10)

        # Message entry
        self.message_entry = tk.Entry(
            input_inner,
            font=("Segoe UI", 11),
            bg="#FFFFFF",
            fg="#333333",
            relief=tk.SOLID,
            bd=1
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 5))
        self.message_entry.bind('<Return>', lambda e: self._send_message())
        self.message_entry.focus_set()

        # Send button
        tk.Button(
            input_inner,
            text="Send",
            command=self._send_message,
            bg="#4A90E2",
            fg="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            width=10
        ).pack(side=tk.RIGHT, ipady=8)

        # Add welcome message
        self._add_system_message(f"Welcome {self.username}! You are now connected.")

    def _send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return

        # Display own message immediately on the right
        self._add_chat_message(self.username, message)

        # Send to server
        self.client.send_message(message)
        self.message_entry.delete(0, tk.END)
        self.message_entry.focus_set()

    def _back_to_lobby(self):
        """Leave group and go back to lobby"""
        # Stop auto refresh
        self.is_active = False
        if self.refresh_job:
            self.window.after_cancel(self.refresh_job)

        # Leave group
        self.client.leave_group()

        # Set message handler back to lobby
        self.client.message_handler = self.lobby_window._handle_message

        # Destroy window and show lobby
        self.window.destroy()
        self.lobby_window.show()

    def _auto_refresh_members(self):
        """Auto refresh group members every 3 seconds"""
        if not self.is_active:
            return  # Stop refreshing if window is not active

        if self.client.is_connected:
            self.client.get_group_members()
            self.refresh_job = self.window.after(3000, self._auto_refresh_members)

    def _add_chat_message(self, username, message):
        self.chat_display.config(state=tk.NORMAL)

        if username == self.username:
            # Own message - right aligned with blue bubble
            self.chat_display.insert(tk.END, f"{username}\n", "username_self")
            self.chat_display.insert(tk.END, f"  {message}  \n", "self_bubble")
            self.chat_display.insert(tk.END, "\n", "self_align")
        else:
            # Other's message - left aligned with white bubble
            self.chat_display.insert(tk.END, f"{username}\n", "username_other")
            self.chat_display.insert(tk.END, f"  {message}  \n", "other_bubble")
            self.chat_display.insert(tk.END, "\n", "other_align")

        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _add_system_message(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"[SYSTEM] {message}\n", "system")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _update_users_list(self, members):
        """Update group members list"""
        self.users_listbox.delete(0, tk.END)
        for member in members:
            username = member if isinstance(member, str) else member.get('username', member)
            display_name = username + (" (You)" if username == self.username else "")
            self.users_listbox.insert(tk.END, display_name)

    def _process_messages(self):
        """Process messages from queue"""
        if not self.is_active:
            return  # Stop processing if window is not active

        try:
            while True:
                json_data = self.client.message_queue.get_nowait()
                # Only process if this window's handler is active
                if self.client.message_handler == self._handle_message:
                    self._handle_message(json_data)
        except queue.Empty:
            pass
        finally:
            if self.client.is_connected and self.is_active:
                self.window.after(100, self._process_messages)

    def _handle_message(self, json_data):
        """Handle incoming JSON messages"""
        # Handle status responses
        if 'status' in json_data:
            status = json_data['status']
            message = json_data.get('message', '')

            if status == 'success':
                # Handle group members list
                if 'members' in json_data and 'group_name' in json_data:
                    members = json_data['members']
                    self._update_users_list(members)
                elif message and not message.startswith('Message sent'):
                    self._add_system_message(message)
            elif status == 'error':
                self._add_system_message(f"Error: {message}")

        # Handle broadcast messages
        elif 'type' in json_data:
            msg_type = json_data['type']
            message = json_data.get('message', '')
            username = json_data.get('username', 'Unknown')

            if msg_type == 'chat':
                # Don't display own message again (already displayed when sent)
                if username != self.username:
                    self._add_chat_message(username, message)
            elif msg_type == 'system':
                self._add_system_message(message)
            else:
                self._add_system_message(f"[{msg_type}] {username}: {message}")

        # Handle errors
        elif 'error' in json_data:
            error_msg = json_data.get('error', 'Unknown error')
            self._add_system_message(f"Error: {error_msg}")

    def _on_close(self):
        """Handle window close"""
        # Stop auto refresh
        self.is_active = False
        if self.refresh_job:
            self.window.after_cancel(self.refresh_job)

        # Leave group
        self.client.leave_group()

        # Set message handler back to lobby
        self.client.message_handler = self.lobby_window._handle_message

        # Destroy window and show lobby
        self.window.destroy()
        self.lobby_window.show()


def main():
    """Main entry point"""
    def on_login(username):
        # Create client and connect
        client = ChatClient()
        if not client.connect():
            messagebox.showerror("Connection Error", "Could not connect to server")
            return

        # Join chat
        if not client.join_chat(username):
            messagebox.showerror("Join Error", "Could not join chat")
            return

        # Start listening thread
        listen_thread = threading.Thread(target=client.listen_for_messages, daemon=True)
        listen_thread.start()

        # Show lobby window
        lobby_window = LobbyWindow(username, client)
        lobby_window.run()

    login_window = LoginWindow(on_login)
    login_window.run()


if __name__ == "__main__":
    main()