import socket
import logging
import time
from typing import Tuple, Dict, Any, List
from rpc_server import RpcServer
from constants import ChatServerConfig, Messages, ValidationRules


class ChatServer:
    GENERAL_GROUP = "General"  # Default group name

    def __init__(self, rpc_server: RpcServer):
        self.rpc_server = rpc_server
        self.user_names: Dict[Tuple[str, int], str] = {}
        self.groups: Dict[str, Dict[str, Any]] = {}  # group_name -> {members: set, creator: str}
        self.user_current_group: Dict[Tuple[str, int], str] = {}  # client_address -> group_name
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._create_general_group()
        self._register_handlers()
        # Set disconnect callback
        self.rpc_server.disconnect_callback = self._handle_client_disconnect

    def _create_general_group(self):
        """Create the default General group"""
        self.groups[self.GENERAL_GROUP] = {
            'members': set(),
            'creator': 'SYSTEM',
            'name': self.GENERAL_GROUP,
            'message_history': []  # List to store message history
        }
        self.logger.info(f"Created default group: {self.GENERAL_GROUP}")

    def _register_handlers(self):
        self.rpc_server.register_handler('join_chat', self._handle_join_chat)
        self.rpc_server.register_handler('leave_chat', self._handle_leave_chat)
        self.rpc_server.register_handler('send_message', self._handle_send_message)
        self.rpc_server.register_handler('get_users', self._handle_get_users)
        self.rpc_server.register_handler('create_group', self._handle_create_group)
        self.rpc_server.register_handler('join_group', self._handle_join_group)
        self.rpc_server.register_handler('leave_group', self._handle_leave_group)
        self.rpc_server.register_handler('get_group_members', self._handle_get_group_members)
        self.rpc_server.register_handler('get_groups', self._handle_get_groups)

    def _validate_message(self, message: str) -> bool:
        return ValidationRules.is_valid_message(message)

    def _get_username(self, client_address: Tuple[str, int]) -> str:
        return self.user_names.get(client_address, f"{ChatServerConfig.DEFAULT_USERNAME_PREFIX}{client_address[1]}")

    def _format_chat_message(self, username: str, message: str) -> str:
        return f"{username}: {message.strip()}"

    def _handle_join_chat(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        username = self._validate_and_get_username(params, client_address)

        if not username:
            return {
                'status': 'error',
                'message': 'Invalid username'
            }

        self.user_names[client_address] = username

        # Auto-join user to General group
        self.groups[self.GENERAL_GROUP]['members'].add(client_address)
        self.user_current_group[client_address] = self.GENERAL_GROUP

        self._broadcast_join_message(username, client_socket)
        self._send_welcome_message(username, client_socket)

        self.logger.info(f"{username} ({client_address}) joined the chat and General group")

        # Get member list for General group
        members = [self._get_username(addr) for addr in self.groups[self.GENERAL_GROUP]['members']]

        # Prepare message history for the new client
        message_history = []
        if 'message_history' in self.groups[self.GENERAL_GROUP]:
            for msg_record in self.groups[self.GENERAL_GROUP]['message_history']:
                # Convert message record to format client can understand
                history_msg = {
                    'type': msg_record['type'],
                    'message': msg_record['message'],
                    'username': msg_record['username'],
                    'timestamp': msg_record['timestamp'],
                    'is_own_message': msg_record['sender_address'] == client_address,  # Flag to identify own messages
                    'group_name': self.GENERAL_GROUP
                }
                message_history.append(history_msg)

        # Broadcast updated members list to all General group members
        self._broadcast_members_update(self.GENERAL_GROUP)

        return {
            'status': 'success',
            'message': f'Joined chat as {username}',
            'users': list(self.user_names.values()),
            'group_name': self.GENERAL_GROUP,
            'members': members,
            'message_history': message_history  # Include message history
        }

    def _validate_and_get_username(self, params: Dict[str, Any], client_address: Tuple[str, int]) -> str:
        username = params.get('username', f"{ChatServerConfig.DEFAULT_USERNAME_PREFIX}{client_address[1]}")
        username = ValidationRules.sanitize_username(username)

        if username in self.user_names.values():
            username = f"{username}_{client_address[1]}"

        return username

    def _broadcast_join_message(self, username: str, client_socket: socket.socket) -> None:
        join_data = {
            'type': 'system',
            'message': f"{username} has joined the chat!",
            'username': 'SYSTEM'
        }
        self.rpc_server.broadcast_json_message(join_data, client_socket)

    def _send_welcome_message(self, username: str, client_socket: socket.socket) -> None:
        welcome_data = {
            'type': 'system',
            'message': f"Welcome to the chat, {username}!",
            'username': 'SYSTEM'
        }
        self.rpc_server.send_json_to_client(client_socket, welcome_data)

    def _handle_leave_chat(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        username = self._get_username(client_address)
        self._remove_user(client_address)
        self._broadcast_leave_message(username, client_socket)

        self.logger.info(f"{username} ({client_address}) left the chat")

        return {
            'status': 'success',
            'message': f'{username} left the chat'
        }

    def _remove_user(self, client_address: Tuple[str, int]) -> None:
        if client_address in self.user_names:
            del self.user_names[client_address]

    def _handle_client_disconnect(self, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        """Handle client disconnect - cleanup user data and notify others"""
        username = self._get_username(client_address)

        # Remove from current group
        current_group = self.user_current_group.get(client_address)
        if current_group and current_group in self.groups:
            self.groups[current_group]['members'].discard(client_address)

            # Notify group members
            leave_data = {
                'type': 'system',
                'message': f"{username} has left the chat!",
                'username': 'SYSTEM',
                'group_name': current_group
            }
            self._broadcast_to_group(current_group, leave_data, None)

            # Broadcast updated members list to remaining members
            self._broadcast_members_update(current_group)

            # Delete group if empty (but not General)
            if len(self.groups[current_group]['members']) == 0 and current_group != self.GENERAL_GROUP:
                del self.groups[current_group]
                self.logger.info(f"Group {current_group} deleted (empty)")

        # Remove user data
        if client_address in self.user_names:
            del self.user_names[client_address]
        if client_address in self.user_current_group:
            del self.user_current_group[client_address]

        self.logger.info(f"{username} ({client_address}) disconnected and cleaned up")

    def _broadcast_leave_message(self, username: str, client_socket: socket.socket) -> None:
        leave_data = {
            'type': 'system',
            'message': f"{username} has left the chat!",
            'username': 'SYSTEM'
        }
        self.rpc_server.broadcast_json_message(leave_data, client_socket)

    def _handle_send_message(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        message = params.get('message', '')

        if not self._validate_message(message):
            return {
                'status': 'error',
                'message': 'Message cannot be empty or too long'
            }

        username = self._get_username(client_address)
        self.logger.info(f"JSON RPC message from {client_address} ({username}): {message.strip()}")

        chat_data = {
            'type': 'message',
            'message': message.strip(),
            'username': username
        }

        # Check if user is in a group
        current_group = self.user_current_group.get(client_address)
        if current_group:
            # Add message to group history
            message_record = {
                'type': 'message',
                'message': message.strip(),
                'username': username,
                'timestamp': time.time(),
                'sender_address': client_address  # Store sender address for client identification
            }

            if current_group in self.groups:
                self.groups[current_group]['message_history'].append(message_record)
                self.logger.info(f"Added message to {current_group} history. Total: {len(self.groups[current_group]['message_history'])}")
                # Keep only last 100 messages to prevent memory issues
                if len(self.groups[current_group]['message_history']) > 100:
                    self.groups[current_group]['message_history'] = self.groups[current_group]['message_history'][-100:]
                    self.logger.info(f"Trimmed {current_group} history to 100 messages")

            # Broadcast to all group members (excluding sender)
            chat_data['group_name'] = current_group  # Use 'group_name' for filtering
            self._broadcast_to_group(current_group, chat_data, client_socket)  # Exclude sender
        else:
            # Broadcast to all users not in groups
            self.rpc_server.broadcast_json_message(chat_data, client_socket)

        return {
            'status': 'success',
            'message': 'Message sent successfully'
        }

    def _handle_get_users(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        connected_clients = self.rpc_server.get_connected_clients()
        users = self._build_user_list(connected_clients)

        return {
            'status': 'success',
            'users': users,
            'count': len(users)
        }

    def _build_user_list(self, connected_clients: List[Tuple[str, int]]) -> List[Dict[str, str]]:
        users = []
        for addr in connected_clients:
            username = self._get_username(addr)
            users.append({
                'username': username,
                'address': f"{addr[0]}:{addr[1]}"
            })
        return users

    def start(self):
        print("Starting Chat Server...")
        self.rpc_server.start_server()

    def stop(self):
        print("Stopping Chat Server...")
        self.rpc_server.stop_server()

    def get_online_users(self):
        return list(self.user_names.values())

    def get_user_count(self):
        return len(self.user_names)

    def _handle_create_group(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        """Create a new group chat"""
        username = self._get_username(client_address)

        # Get group name from params or generate one
        group_name = params.get('group_name', '').strip()

        if not group_name:
            # Generate unique group name if not provided
            import time
            group_name = f"Group_{int(time.time())}"

        # Check if group name already exists
        if group_name in self.groups:
            group_error_data = {
                'status': 'error',
                'message': f'Group name "{group_name}" already exists'
            }
            self.rpc_server.send_json_to_client(client_socket, group_error_data)
            return {
                'status': 'error',
                'message': f'Group name "{group_name}" already exists'
            }

        # Create group
        group_data = {
            'members': {client_address},
            'creator': username,
            'name': group_name,
            'message_history': []  # Initialize empty message history
        }

        # If this is a private chat, extract and store allowed users
        if self._is_private_chat(group_name):
            # Format: private_user1_user2
            # Extract the two usernames from the group name
            allowed_users = []
            remaining = group_name.replace('private_', '', 1)

            # The creator is one of them
            allowed_users.append(username)

            # The other user is the remaining part after removing creator
            # Try both possibilities (creator could be first or second)
            if remaining.startswith(username + '_'):
                other_user = remaining[len(username) + 1:]
                if other_user:  # Make sure we got a valid username
                    allowed_users.append(other_user)
            elif remaining.endswith('_' + username):
                other_user = remaining[:-len(username) - 1]
                if other_user:  # Make sure we got a valid username
                    allowed_users.append(other_user)

            if len(allowed_users) == 2:
                group_data['allowed_users'] = allowed_users
                self.logger.info(f"Created private chat {group_name} for users: {allowed_users}")
            else:
                self.logger.warning(f"Could not extract both users from private chat name: {group_name}")

        self.groups[group_name] = group_data

        # Add user to group
        self.user_current_group[client_address] = group_name

        self.logger.info(f"{username} created group {group_name}")

        return {
            'status': 'success',
            'message': f'Group created: {group_name}',
            'group_name': group_name,
            'members': [username]
        }

    def _is_private_chat(self, group_name: str) -> bool:
        """Check if group is a private chat between two users"""
        return group_name.startswith('private_')

    def _get_private_chat_users(self, group_name: str) -> List[str]:
        """Extract usernames from private chat group name"""
        if not self._is_private_chat(group_name):
            return []
        # Format: private_user1_user2
        parts = group_name.split('_', 1)  # Split only at first underscore after 'private'
        if len(parts) < 2:
            return []
        # The rest is "user1_user2", need to split into two usernames
        users_part = parts[1]
        # Find the middle underscore by trying to match with existing usernames
        # For now, we'll store allowed users in group metadata
        return []

    def _handle_join_group(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        """Join an existing group"""
        group_name = params.get('group_name', '')
        username = self._get_username(client_address)

        if not group_name or group_name not in self.groups:
            return {
                'status': 'error',
                'message': 'Group not found'
            }

        # Check if this is a private chat and user is allowed to join
        if self._is_private_chat(group_name):
            # Get allowed users from group metadata
            allowed_users = self.groups[group_name].get('allowed_users', [])
            if allowed_users and username not in allowed_users:
                self.logger.warning(f"{username} attempted to join private chat {group_name} but is not authorized")
                return {
                    'status': 'error',
                    'message': 'This is a private chat. You are not authorized to join.'
                }

        # Add user to group
        self.groups[group_name]['members'].add(client_address)
        self.user_current_group[client_address] = group_name

        # Notify group members
        join_data = {
            'type': 'system',
            'message': f"{username} joined the group",
            'username': 'SYSTEM',
            'group': group_name
        }
        self._broadcast_to_group(group_name, join_data, None)

        # Get member list
        members = [self._get_username(addr) for addr in self.groups[group_name]['members']]

        # Prepare message history for the new client
        message_history = []
        if 'message_history' in self.groups[group_name]:
            self.logger.info(f"Group {group_name} has {len(self.groups[group_name]['message_history'])} messages in history")
            for msg_record in self.groups[group_name]['message_history']:
                # Convert message record to format client can understand
                history_msg = {
                    'type': msg_record['type'],
                    'message': msg_record['message'],
                    'username': msg_record['username'],
                    'timestamp': msg_record['timestamp'],
                    'is_own_message': msg_record['sender_address'] == client_address,  # Flag to identify own messages
                    'group_name': group_name
                }
                message_history.append(history_msg)
        else:
            self.logger.warning(f"Group {group_name} has no message_history key!")

        self.logger.info(f"Sending {len(message_history)} messages to {username} joining {group_name}")

        return {
            'status': 'success',
            'message': f'Joined group: {group_name}',
            'group_name': group_name,
            'members': members,
            'message_history': message_history  # Include message history
        }

    def _handle_leave_group(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        """Leave current group"""
        username = self._get_username(client_address)
        current_group = self.user_current_group.get(client_address)

        if not current_group:
            return {
                'status': 'error',
                'message': 'Not in any group'
            }

        # Remove user from group
        if current_group in self.groups:
            self.groups[current_group]['members'].discard(client_address)

            # Notify remaining members
            leave_data = {
                'type': 'system',
                'message': f"{username} left the group",
                'username': 'SYSTEM',
                'group': current_group
            }
            self._broadcast_to_group(current_group, leave_data, None)

            # Broadcast updated members list to remaining members
            self._broadcast_members_update(current_group)

            # Delete group if empty (but not General group)
            if len(self.groups[current_group]['members']) == 0 and current_group != self.GENERAL_GROUP:
                del self.groups[current_group]
                self.logger.info(f"Group {current_group} deleted (empty)")

        # If leaving a non-General group, rejoin General group
        if current_group != self.GENERAL_GROUP:
            # Add user back to General group
            self.groups[self.GENERAL_GROUP]['members'].add(client_address)
            self.user_current_group[client_address] = self.GENERAL_GROUP

            # Notify General group members
            join_data = {
                'type': 'system',
                'message': f"{username} joined the group",
                'username': 'SYSTEM',
                'group_name': self.GENERAL_GROUP
            }
            self._broadcast_to_group(self.GENERAL_GROUP, join_data, None)

            # Broadcast updated members list to General group
            self._broadcast_members_update(self.GENERAL_GROUP)

            self.logger.info(f"{username} left group {current_group} and rejoined {self.GENERAL_GROUP}")

            # Get General group members
            members = [self._get_username(addr) for addr in self.groups[self.GENERAL_GROUP]['members']]

            return {
                'status': 'success',
                'message': 'Left group and rejoined General',
                'group_name': self.GENERAL_GROUP,
                'members': members
            }
        else:
            # Leaving General group (shouldn't happen normally)
            del self.user_current_group[client_address]
            self.logger.info(f"{username} left group {current_group}")

            return {
                'status': 'success',
                'message': 'Left group successfully'
            }

    def _handle_get_group_members(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        """Get members of current group"""
        current_group = self.user_current_group.get(client_address)

        if not current_group or current_group not in self.groups:
            return {
                'status': 'error',
                'message': 'Not in any group'
            }

        members = [self._get_username(addr) for addr in self.groups[current_group]['members']]

        return {
            'status': 'success',
            'group_name': current_group,
            'members': members,
            'count': len(members)
        }

    def _handle_get_groups(self, params: Dict[str, Any], client_socket: socket.socket, client_address: Tuple[str, int]) -> Dict[str, Any]:
        """Get list of all groups"""
        groups_list = []
        for group_name, group_data in self.groups.items():
            groups_list.append({
                'name': group_name,
                'creator': group_data['creator'],
                'member_count': len(group_data['members'])
            })

        return {
            'status': 'success',
            'groups': groups_list,
            'count': len(groups_list)
        }

    def _broadcast_to_group(self, group_name: str, data: Dict[str, Any], exclude_socket: socket.socket = None):
        """Broadcast message to all members of a group"""
        if group_name not in self.groups:
            return

        for member_address in self.groups[group_name]['members']:
            # Find the socket for this address
            for client_socket, addr in self.rpc_server.clients.items():
                if addr == member_address and client_socket != exclude_socket:
                    try:
                        self.rpc_server.send_json_to_client(client_socket, data)
                    except Exception as e:
                        self.logger.error(f"Error broadcasting to {member_address}: {e}")

    def _broadcast_members_update(self, group_name: str):
        """Broadcast updated members list to all members of a group"""
        if group_name not in self.groups:
            return

        # Get current members list
        members = [self._get_username(addr) for addr in self.groups[group_name]['members']]

        # Broadcast to all members
        members_data = {
            'type': 'members_update',
            'group_name': group_name,
            'members': members,
            'count': len(members)
        }
        self._broadcast_to_group(group_name, members_data, None)
