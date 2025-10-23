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
            'params': {
                'group_name': group_name
            }
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
        self.pending_private_chat = None  # Store pending private chat group name

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

        # Bind double click event
        self.users_listbox.bind('<Double-Button-1>', self._on_user_double_click)

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

    def _on_user_double_click(self, event):
        """Handle double click on user in the list - Create private chat"""
        selection = self.users_listbox.curselection()
        if selection:
            index = selection[0]
            selected_user = self.users_listbox.get(index)

            # Remove " (You)" suffix if present
            selected_user = selected_user.replace(" (You)", "").strip()

            # Don't create chat with yourself
            if selected_user == self.username:
                print(f"✗ Cannot create private chat with yourself")
                return

            print(f"✓ Double clicked on user: {selected_user}")

            # Create a private group name (sorted to ensure consistency)
            users = sorted([self.username, selected_user])
            private_group_name = f"private_{users[0]}_{users[1]}"

            print(f"→ Creating/joining private chat: {private_group_name}")

            # Store pending private chat request
            self.pending_private_chat = private_group_name

            # Try to create the group first (will fail if exists, then join)
            self.client.create_group(private_group_name)

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

                    # Clear pending private chat flag
                    self.pending_private_chat = None

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

                # Check if this is a failed private chat creation (group already exists)
                if self.pending_private_chat and 'already exists' in message:
                    print(f"→ Group already exists, joining instead: {self.pending_private_chat}")
                    # Try to join the existing group
                    self.client.join_group(self.pending_private_chat)
                    # Don't clear pending_private_chat yet, wait for join response
                else:
                    # Clear pending flag and show error
                    self.pending_private_chat = None
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


class GeneralChatWindow:
    """Main chat window for General group (uses Tk as main window)"""

    def __init__(self, username, client, group_name, members, message_history=None):
        self.username = username
        self.client = client
        self.group_name = group_name
        self.is_active = True
        self.refresh_job = None
        self.other_chat_window = None  # Track other group chat windows
        self.message_history = message_history or []  # Store initial message history
        self.pending_private_chat = None  # Store pending private chat group name
        self.private_chat_invitations = set()  # Track users who sent private chat invitations

        # Create main window (Tk instead of Toplevel)
        self.window = tk.Tk()
        self.window.title(f"User: {username}")
        self.window.geometry("1000x650")
        self.window.configure(bg="#F0F0F0")

        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

        # Set message handler
        self.client.message_handler = self._handle_message

        # Setup UI
        self._setup_ui()

        # Update members list
        self._update_members_list(members)

        # Display initial message history if available
        if self.message_history:
            self._display_message_history(self.message_history)

        # Start auto-refresh
        self._auto_refresh_members()

        # Start message processing
        self.window.after(100, self._process_messages)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        """Setup the UI components"""
        # Main container
        main_frame = tk.Frame(self.window, bg="#F0F0F0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Group actions and members
        left_panel = tk.Frame(main_frame, bg="#FFFFFF", relief=tk.SOLID, bd=1, width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)

        # Group actions header
        actions_header = tk.Frame(left_panel, bg="#4A90E2")
        actions_header.pack(fill=tk.X)

        tk.Label(
            actions_header,
            text="🏠 Groups",
            font=("Segoe UI", 11, "bold"),
            bg="#4A90E2",
            fg="white"
        ).pack(pady=8)

        # Create Group button
        create_btn = tk.Button(
            left_panel,
            text="➕ Create Group",
            font=("Segoe UI", 10),
            bg="#5CB85C",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._create_group
        )
        create_btn.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Join Group button
        join_btn = tk.Button(
            left_panel,
            text="🚪 Join Group",
            font=("Segoe UI", 10),
            bg="#5BC0DE",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._join_group
        )
        join_btn.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Separator
        tk.Frame(left_panel, bg="#E0E0E0", height=1).pack(fill=tk.X, padx=5, pady=5)

        # Members header
        members_header = tk.Frame(left_panel, bg="#4A90E2")
        members_header.pack(fill=tk.X)

        tk.Label(
            members_header,
            text="👥 Members",
            font=("Segoe UI", 11, "bold"),
            bg="#4A90E2",
            fg="white"
        ).pack(pady=8)

        # Members list
        members_frame = tk.Frame(left_panel, bg="#FFFFFF")
        members_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.members_listbox = tk.Listbox(
            members_frame,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#333333",
            selectbackground="#E3F2FD",
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.members_listbox.pack(fill=tk.BOTH, expand=True)

        # Bind double click event
        self.members_listbox.bind('<Double-Button-1>', self._on_member_double_click)

        # Right panel - Chat area
        self._setup_chat_panel(main_frame)

    def _setup_chat_panel(self, parent):
        """Setup the chat panel on the right"""
        right_panel = tk.Frame(parent, bg="#FFFFFF", relief=tk.SOLID, bd=1)
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

        # Chat display area
        chat_frame = tk.Frame(right_panel, bg="#F5F5F5")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Scrollbar
        scrollbar = tk.Scrollbar(chat_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Chat text widget
        self.chat_display = tk.Text(
            chat_frame,
            font=("Segoe UI", 10),
            bg="#F5F5F5",
            fg="#333333",
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.chat_display.yview)

        # Configure tags for chat bubbles
        self.chat_display.tag_config("self", justify=tk.RIGHT, foreground="#FFFFFF", background="#4A90E2", spacing1=5, spacing3=5, lmargin1=100, lmargin2=100, rmargin=10)
        self.chat_display.tag_config("other", justify=tk.LEFT, foreground="#333333", background="#E8E8E8", spacing1=5, spacing3=5, lmargin1=10, lmargin2=10, rmargin=100)
        self.chat_display.tag_config("system", justify=tk.CENTER, foreground="#888888", font=("Segoe UI", 9, "italic"), spacing1=5, spacing3=5)

        # Configure username tags
        self.chat_display.tag_config("username_self", justify=tk.RIGHT, foreground="#666666", font=("Segoe UI", 8), spacing1=2)
        self.chat_display.tag_config("username_other", justify=tk.LEFT, foreground="#666666", font=("Segoe UI", 8), spacing1=2)

        # Message input area
        input_frame = tk.Frame(right_panel, bg="#FFFFFF")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Message entry
        self.message_entry = tk.Entry(
            input_frame,
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
        send_btn = tk.Button(
            input_frame,
            text="Send",
            font=("Segoe UI", 10, "bold"),
            bg="#4A90E2",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._send_message,
            width=10
        )
        send_btn.pack(side=tk.RIGHT, ipady=8)

    # Copy all other methods from ChatWindow
    def _create_group(self):
        """Show dialog to create a new group"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Create Group")
        dialog.geometry("400x150")
        dialog.configure(bg="#F0F0F0")
        dialog.transient(self.window)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (75)
        dialog.geometry(f'400x150+{x}+{y}')

        # Label
        tk.Label(
            dialog,
            text="Enter Group Name:",
            font=("Segoe UI", 11),
            bg="#F0F0F0"
        ).pack(pady=(20, 5))

        # Entry
        entry = tk.Entry(
            dialog,
            font=("Segoe UI", 11),
            width=30
        )
        entry.pack(pady=5, padx=20)
        entry.focus_set()

        # Hint
        tk.Label(
            dialog,
            text="(Leave empty for auto-generated name)",
            font=("Segoe UI", 9),
            fg="#888888",
            bg="#F0F0F0"
        ).pack()

        def on_create():
            group_name = entry.get().strip()
            self.client.create_group(group_name)
            dialog.destroy()

        # Buttons frame
        btn_frame = tk.Frame(dialog, bg="#F0F0F0")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Create",
            font=("Segoe UI", 10),
            bg="#5CB85C",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=on_create,
            width=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Cancel",
            font=("Segoe UI", 10),
            bg="#D9534F",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.LEFT, padx=5)

        entry.bind('<Return>', lambda e: on_create())
    
    def show_error_message_pop_up(self, message):
        """Show dialog to create a new group"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Error")
        dialog.geometry("180x80")
        dialog.configure(bg="#F0F0F0")
        dialog.transient(self.window)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (75)
        dialog.geometry(f'400x150+{x}+{y}')

        # Label
        tk.Label(
            dialog,
            text=str(message),
            font=("Segoe UI", 11),
            bg="#F0F0F0"
        ).pack(pady=(20, 5))

        # Buttons frame
        btn_frame = tk.Frame(dialog, bg="#F0F0F0")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Close",
            font=("Segoe UI", 10),
            bg="#D9534F",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.LEFT, padx=5)

    def _join_group(self):
        """Show dialog to join an existing group"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Join Group")
        dialog.geometry("400x150")
        dialog.configure(bg="#F0F0F0")
        dialog.transient(self.window)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (75)
        dialog.geometry(f'400x150+{x}+{y}')

        # Label
        tk.Label(
            dialog,
            text="Enter Group Name to Join:",
            font=("Segoe UI", 11),
            bg="#F0F0F0"
        ).pack(pady=(20, 10))

        # Entry
        entry = tk.Entry(
            dialog,
            font=("Segoe UI", 11),
            width=30
        )
        entry.pack(pady=10, padx=20)
        entry.focus_set()

        def on_join():
            group_name = entry.get().strip()
            if group_name:
                self.client.join_group(group_name)
                dialog.destroy()

        # Buttons frame
        btn_frame = tk.Frame(dialog, bg="#F0F0F0")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Join",
            font=("Segoe UI", 10),
            bg="#5BC0DE",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=on_join,
            width=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Cancel",
            font=("Segoe UI", 10),
            bg="#D9534F",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.LEFT, padx=5)

        entry.bind('<Return>', lambda e: on_join())

    def _send_message(self):
        """Send a message"""
        message = self.message_entry.get().strip()
        if message:
            # Display own message immediately
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "You\n", "username_self")
            self.chat_display.insert(tk.END, f"{message}\n", "self")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)

            # Send to server
            self.client.send_message(message)
            self.message_entry.delete(0, tk.END)

    def _update_members_list(self, members):
        """Update the members list"""
        self.members_listbox.delete(0, tk.END)
        for member in members:
            prefix = "👤 " if member != self.username else "👤 (You) "
            display_name = f"{prefix}{member}"

            # Add red dot indicator if there's a private chat invitation from this user
            if member in self.private_chat_invitations:
                display_name = "🔴 " + display_name

            self.members_listbox.insert(tk.END, display_name)

    def _on_member_double_click(self, event):
        """Handle double click on member in the list - Create private chat"""
        selection = self.members_listbox.curselection()
        if selection:
            index = selection[0]
            selected_member = self.members_listbox.get(index)

            # Remove prefix "� ", "�👤 " and " (You) " if present
            # Remove prefix "🔴 ", "👤 " and " (You) " if present
            selected_member = selected_member.replace("🔴 ", "").replace("👤 ", "").replace("(You) ", "").strip()
            # Don't create chat with yourself
            if selected_member == self.username:
                print(f"✗ Cannot create private chat with yourself")
                return

            print(f"✓ Double clicked on member: {selected_member}")

            # Remove from invitation list if present
            if selected_member in self.private_chat_invitations:
                self.private_chat_invitations.discard(selected_member)
                # Refresh the members list to remove the red dot
                self.client.get_group_members()

            # Create a private group name (sorted to ensure consistency)
            users = sorted([self.username, selected_member])
            private_group_name = f"private_{users[0]}_{users[1]}"

            print(f"→ Creating/joining private chat: {private_group_name}")

            # Store pending private chat request
            self.pending_private_chat = private_group_name

            # Try to create the group first
            self.client.create_group(private_group_name)

    def _auto_refresh_members(self):
        """Auto-refresh members list every 3 seconds"""
        if not self.is_active:
            return

        self.client.get_group_members()
        self.refresh_job = self.window.after(3000, self._auto_refresh_members)

    def _process_messages(self):
        """Process messages from queue"""
        if not self.is_active:
            return

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
        """Handle incoming messages"""
        # Handle group creation/join - open new ChatWindow
        if 'status' in json_data:
            if json_data['status'] == 'success':
                if 'group_name' in json_data:
                    group_name = json_data['group_name']
                    # Only open new window if it's not the General group
                    if group_name != self.group_name:
                        members = json_data.get('members', [])
                        message_history = json_data.get('message_history', [])
                        print(f"[DEBUG] GeneralChatWindow: creating ChatWindow for {group_name} with {len(message_history)} messages")

                        # Clear pending private chat flag
                        self.pending_private_chat = None

                        # Close previous other chat window if exists
                        if self.other_chat_window:
                            try:
                                self.other_chat_window.window.destroy()
                            except:
                                pass
                        # Hide General window
                        self.window.withdraw()
                        # Open new chat window for other group with message history
                        self.other_chat_window = ChatWindow(self.username, self.client, group_name, members, self, message_history)
                        return
                    else:
                        # Client rejoined General group - clear chat display and show history
                        message = json_data.get('message', '')
                        if 'rejoined General' in message or 'Left group and rejoined General' in message:
                            self._clear_chat_display()
                            # Display message history if available
                            message_history = json_data.get('message_history', [])
                            if message_history:
                                self._display_message_history(message_history)
                            # Update members list
                            members = json_data.get('members', [])
                            if members:
                                self._update_members_list(members)
                        return
            elif json_data['status'] == 'error':
                message = json_data.get('message', 'Unknown error')

                # Check if this is a failed private chat creation (group already exists)
                if self.pending_private_chat and 'already exists' in message:
                    print(f"→ Group already exists, joining instead: {self.pending_private_chat}")
                    # Try to join the existing group
                    self.client.join_group(self.pending_private_chat)
                    # Don't clear pending_private_chat yet, wait for join response
                else:
                    # Clear pending flag and show error
                    self.pending_private_chat = None
                    self.show_error_message_pop_up(message)
                return

            # Handle members list update
            if 'members' in json_data and 'group_name' not in json_data:
                members = json_data['members']
                self._update_members_list(members)
                return

        # Handle members update
        if 'type' in json_data and json_data['type'] == 'members_update':
            message_group = json_data.get('group_name', None)
            # Only update if it's for this group
            if message_group == self.group_name:
                members = json_data.get('members', [])
                self._update_members_list(members)
            return
        
        if 'type' in json_data and json_data['type'] == 'private_chat_invitation':
            from_user = json_data.get('from_user', 'Unknown')
            group_name = json_data.get('group_name', 'Unknown')
            print(f"----> Received private chat invitation from {from_user} (group: {group_name})")

            # Add to invitation list
            self.private_chat_invitations.add(from_user)

            # Refresh members list IMMEDIATELY to show red dot indicator
            # Get current members from listbox
            current_members = []
            for i in range(self.members_listbox.size()):
                member_text = self.members_listbox.get(i)
                # Remove all prefixes to get clean username
                member = member_text.replace("🔴 ", "").replace("👤 ", "").replace("(You) ", "").strip()
                current_members.append(member)

            # Update display immediately
            self._update_members_list(current_members)
            return

        # Handle chat messages
        if 'type' in json_data:
            msg_type = json_data['type']
            username = json_data.get('username', 'Unknown')
            message = json_data.get('message', '')
            message_group = json_data.get('group_name', None)  # Changed from 'group' to 'group_name'

            # Filter: Only show messages from this group
            if msg_type == 'message' and message_group != self.group_name:
                return  # Ignore messages from other groups

            self.chat_display.config(state=tk.NORMAL)

            if msg_type == 'system':
                self.chat_display.insert(tk.END, f"{message}\n", "system")
            elif msg_type == 'message':
                # Only show messages from others (sender already displayed their own)
                if username != self.username:
                    # Show username label
                    self.chat_display.insert(tk.END, f"{username}\n", "username_other")
                    # Show message
                    self.chat_display.insert(tk.END, f"{message}\n", "other")

            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)

    def show(self):
        """Show the window again"""
        self.client.message_handler = self._handle_message
        self.window.deiconify()

        # Clear chat display when returning to General group
        self._clear_chat_display()

        self.client.get_group_members()

    def _clear_chat_display(self):
        """Clear all messages from chat display"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _display_message_history(self, message_history):
        """Display message history from server"""
        if not message_history:
            return

        self.chat_display.config(state=tk.NORMAL)

        for msg in message_history:
            msg_type = msg.get('type', 'message')
            username = msg.get('username', 'Unknown')
            message = msg.get('message', '')
            is_own_message = msg.get('is_own_message', False)

            if msg_type == 'system':
                self.chat_display.insert(tk.END, f"{message}\n", "system")
            elif msg_type == 'message':
                if is_own_message:
                    # Own message - display on right
                    self.chat_display.insert(tk.END, "You\n", "username_self")
                    self.chat_display.insert(tk.END, f"{message}\n", "self")
                else:
                    # Other's message - display on left
                    self.chat_display.insert(tk.END, f"{username}\n", "username_other")
                    self.chat_display.insert(tk.END, f"{message}\n", "other")

        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _on_close(self):
        """Handle window close"""
        self.is_active = False
        if self.refresh_job:
            self.window.after_cancel(self.refresh_job)
        self.client.disconnect()
        self.window.destroy()

    def run(self):
        self.window.mainloop()


class ChatWindow:
    """Chat window for other groups (Toplevel)"""
    def __init__(self, username, client, group_name, members, parent_window, message_history=None):
        self.username = username
        self.client = client
        self.group_name = group_name
        self.parent_window = parent_window  # Can be GeneralChatWindow or LobbyWindow
        self.is_active = True  # Flag to track if window is active
        self.refresh_job = None  # Store refresh job ID
        self.message_history = message_history or []  # Store initial message history
        self.pending_private_chat = None  # Store pending private chat group name
        print(f"[DEBUG] ChatWindow constructor: received {len(self.message_history)} messages for group {group_name}")

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

        # Display initial message history if available (AFTER widgets are created)
        if self.message_history:
            self._display_message_history(self.message_history)

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
            text="⬅ Back to General",
            command=self._back_to_parent,
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

        # Bind double click event
        self.users_listbox.bind('<Double-Button-1>', self._on_user_double_click_other_group)

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

    def _back_to_parent(self):
        """Leave group and go back to parent window"""
        # Stop auto refresh
        self.is_active = False
        if self.refresh_job:
            self.window.after_cancel(self.refresh_job)

        # Leave group
        self.client.leave_group()

        # Set message handler back to parent immediately so it can receive the leave_group response
        self.client.message_handler = self.parent_window._handle_message

        # Destroy window and show parent
        self.window.destroy()
        self.parent_window.show()

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

    def _on_user_double_click_other_group(self, event):
        """Handle double click on user in the other group list - Create private chat"""
        selection = self.users_listbox.curselection()
        if selection:
            index = selection[0]
            selected_user = self.users_listbox.get(index)

            # Remove " (You)" suffix if present
            selected_user = selected_user.replace(" (You)", "").strip()

            # Don't create chat with yourself
            if selected_user == self.username:
                print(f"✗ Cannot create private chat with yourself")
                return

            print(f"✓ Double clicked on user in group '{self.group_name}': {selected_user}")

            # Create a private group name (sorted to ensure consistency)
            users = sorted([self.username, selected_user])
            private_group_name = f"private_{users[0]}_{users[1]}"

            print(f"→ Creating/joining private chat: {private_group_name}")

            # Store pending private chat request
            self.pending_private_chat = private_group_name

            # Try to create the group first
            self.client.create_group(private_group_name)

    def _display_message_history(self, message_history):
        """Display message history from server"""
        print(f"[DEBUG] _display_message_history called with {len(message_history) if message_history else 0} messages")
        if not message_history:
            print("[DEBUG] No message history to display")
            return

        # Clear existing messages first
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)

        for msg in message_history:
            msg_type = msg.get('type', 'message')
            username = msg.get('username', 'Unknown')
            message = msg.get('message', '')
            is_own_message = msg.get('is_own_message', False)



            if msg_type == 'system':
                # Add system message directly without calling _add_system_message
                self.chat_display.insert(tk.END, f"[SYSTEM] {message}\n", "system")
            elif msg_type == 'message':
                # Add chat message directly based on ownership
                if is_own_message:
                    # Own message - right aligned with blue bubble
                    self.chat_display.insert(tk.END, f"{username}\n", "username_self")
                    self.chat_display.insert(tk.END, f"  {message}  \n", "self_bubble")
                    self.chat_display.insert(tk.END, "\n", "self_align")
                else:
                    # Other's message - left aligned with white bubble
                    self.chat_display.insert(tk.END, f"{username}\n", "username_other")
                    self.chat_display.insert(tk.END, f"  {message}  \n", "other_bubble")
                    self.chat_display.insert(tk.END, "\n", "other_align")

        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

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
                # Handle group creation/join - switch to new group
                if 'group_name' in json_data:
                    group_name = json_data['group_name']
                    # If it's a different group, switch to it
                    if group_name != self.group_name:
                        members = json_data.get('members', [])
                        message_history = json_data.get('message_history', [])

                        # Clear pending private chat flag
                        self.pending_private_chat = None

                        # Leave current group and switch to new one
                        self.client.leave_group()

                        # Update this window to show the new group
                        self.group_name = group_name
                        self.window.title(f"Chat - {group_name}")
                        self._update_users_list(members)

                        # Clear and display new message history
                        self.chat_display.config(state=tk.NORMAL)
                        self.chat_display.delete(1.0, tk.END)
                        self.chat_display.config(state=tk.DISABLED)

                        if message_history:
                            self._display_message_history(message_history)

                        self._add_system_message(f"Switched to {group_name}")
                        return
                    else:
                        # Same group - just update members
                        members = json_data.get('members', [])
                        self._update_users_list(members)

                        # Display message history if available (for new joins)
                        message_history = json_data.get('message_history', [])
                        print(f"[DEBUG] ChatWindow received message_history: {len(message_history) if message_history else 0} messages")
                        if message_history:
                            print(f"[DEBUG] First message: {message_history[0] if message_history else 'None'}")
                            self._display_message_history(message_history)
                        else:
                            print("[DEBUG] No message history in server response")
                elif message and not message.startswith('Message sent'):
                    self._add_system_message(message)
            elif status == 'error':
                # Check if this is a failed private chat creation (group already exists)
                if self.pending_private_chat and 'already exists' in message:
                    print(f"→ Group already exists, joining instead: {self.pending_private_chat}")
                    # Try to join the existing group
                    self.client.join_group(self.pending_private_chat)
                    # Don't clear pending_private_chat yet, wait for join response
                else:
                    # Clear pending flag and show error
                    self.pending_private_chat = None
                    self._add_system_message(f"Error: {message}")

        # Handle broadcast messages
        elif 'type' in json_data:
            msg_type = json_data['type']
            message_group = json_data.get('group_name', None)

            # Handle members update
            if msg_type == 'members_update':
                # Only update if it's for this group
                if message_group == self.group_name:
                    members = json_data.get('members', [])
                    self._update_users_list(members)
                return

            message = json_data.get('message', '')
            username = json_data.get('username', 'Unknown')

            # Filter: Only show messages from this group
            if msg_type == 'message' and message_group != self.group_name:
                return  # Ignore messages from other groups

            if msg_type == 'message':
                # Only display messages from others (sender already displayed their own)
                if username != self.username:
                    self._add_chat_message(username, message)
            elif msg_type == 'system':
                self._add_system_message(message)

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

        # Set message handler back to parent immediately so it can receive the leave_group response
        self.client.message_handler = self.parent_window._handle_message

        # Destroy window and show parent
        self.window.destroy()
        self.parent_window.show()


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

        # Wait for join_chat response with General group info
        try:
            response = client.message_queue.get(timeout=5)

            # Skip system messages and members_update, get the actual join response
            while response.get('type') in ['system', 'members_update']:
                response = client.message_queue.get(timeout=5)

            if response.get('status') == 'success' and 'group_name' in response:
                group_name = response['group_name']
                members = response.get('members', [])
                message_history = response.get('message_history', [])

                # Create main window (Tk) as ChatWindow for General group
                main_window = GeneralChatWindow(username, client, group_name, members, message_history)
                main_window.run()
            else:
                messagebox.showerror("Error", "Failed to join General group")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize: {str(e)}")

    login_window = LoginWindow(on_login)
    login_window.run()


if __name__ == "__main__":
    main()