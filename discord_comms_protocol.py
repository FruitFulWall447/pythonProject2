import socket
import json
import time
import zlib
import pickle
import threading
import logging


class client_net:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Create a StreamHandler with the desired format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # Add the StreamHandler to the logger
        self.logger.addHandler(stream_handler)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = "127.0.0.1"
        self.port = 4444
        self.addr = (self.server_ip, self.port)
        self.logger.debug(f"trying to connect to addr: {self.addr}")
        self.id = self.connect()
        self.size = 0000000
        self.original_len = 7
        self.lock = threading.Lock()


    def connect(self):
        try:
            self.client.connect(self.addr)
            self.logger.info("connected to server")
        except:
            self.logger.info("couldn't connect to server")
            pass

    def send_str(self, data):
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))
        except socket.error as e:
            print(e)

    def leave_call(self):
        data = f"call:ended"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))
        except socket.error as e:
            print(e)

    def create_group(self, group_members_list):
        encoded_list = json.dumps(group_members_list)
        full_message = "group:create:" + encoded_list

        # Convert the length of the data to a string
        size_str = str(len(full_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.client.send(size.encode('utf-8'))
        self.client.send(full_message.encode())

    def send_calling_user(self, user_that_is_called):
        data = f"call:calling:{user_that_is_called}"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))
        except socket.error as e:
            print(e)

    def stop_ringing_to_group_or_user(self):
        data = f"call:calling:stop!"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)

    def send_accept_call_with(self, accepted_caller):
        data = f"call:accepted:{accepted_caller}"
        try:
            # Convert the length of the data to a string
            if self.client.fileno() == -1:
                self.logger.error("Socket is closed.")
            else:
                size_str = str(len(data.encode('utf-8')))
                size = str(self.size + int(size_str))
                number_of_zero = self.original_len - len(size)
                size = ("0" * number_of_zero) + size
                # Send the size as a string
                self.client.send(size.encode('utf-8'))
                # Send the actual data
                self.client.send(data.encode('utf-8'))
        except socket.error as e:
            print(e)

    def send_reject_call_with(self, rejected_caller):
        data = f"call:rejected:{rejected_caller}"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)

    def toggle_mute_for_myself(self):
        data = f"call:mute:myself"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)

    def toggle_deafen_for_myself(self):
        data = f"call:deafen:myself"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)


    def send_login_info(self, username, password):
        format = "login"
        message = {"format": format,
                   "username": username,
                   "password": password
                   }
        encoded_message = json.dumps(message)


        # Convert the length of the data to a string
        size_str = str(len(encoded_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.client.send(size.encode('utf-8'))
        self.client.send(encoded_message.encode())

    def send_sign_up_info(self, username, password, email):
        format = "sign up"
        message = {"format": format,
                   "username": username,
                   "password": password,
                   "email": email
                   }
        encoded_message = json.dumps(message)


        # Convert the length of the data to a string
        size_str = str(len(encoded_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.client.send(size.encode('utf-8'))
        self.client.send(encoded_message.encode())

    def send_security_token(self, security_token):
        format = "security token"
        message = {"format": format,
                   "security_token": security_token,
                   }
        encoded_message = json.dumps(message)


        # Convert the length of the data to a string
        size_str = str(len(encoded_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.client.send(size.encode('utf-8'))
        self.client.send(encoded_message.encode())

    def send_username_and_email_froget_password(self, username, password, email):
        format = "forget password"
        message = {"format": format,
                   "username": username,
                   "password": password,
                   "email": email
                   }
        encoded_message = json.dumps(message)


        # Convert the length of the data to a string
        size_str = str(len(encoded_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.client.send(size.encode('utf-8'))
        self.client.send(encoded_message.encode())

    def send_message(self, sender, receiver, content):

        message = {"sender": sender,
                   "receiver": receiver,
                   "content": content,

                   }
        encoded_message = json.dumps(message)
        full_message = "add_message:" + encoded_message

        # Convert the length of the data to a string
        size_str = str(len(full_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.client.send(size.encode('utf-8'))
        self.client.send(full_message.encode())

    def send_vc_data(self, vc_data):
        try:
            full_message = vc_data
            compressed_message = zlib.compress(full_message)

            # Add a specific sequence of bytes at the beginning
            sequence = br'\vc_data'  # Use raw string to treat backslash as a literal character
            full_message = sequence + compressed_message
            # Convert the length of the data to a string
            size_str = str(len(full_message))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            self.client.send(full_message)
        except Exception as e:
            print(f"error is: {e}")

    def send_share_screen_data(self, share_screen_data):
        try:
            full_message = share_screen_data
            compressed_message = zlib.compress(full_message)

            # Add a specific sequence of bytes at the beginning
            sequence = br'\share_screen_data'  # Use raw string to treat backslash as a literal character
            full_message = sequence + compressed_message
            # Convert the length of the data to a string
            size_str = str(len(full_message))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            self.client.send(full_message)
        except Exception as e:
            print(f"error is: {e}")


    def send_friend_request(self, username, friend_username):
        data = f"friend_request:{username}:{friend_username}"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)

    def send_remove_friend(self, friend_username):
        data = f"friend_remove:{friend_username}"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)


    def send_friends_request_rejection(self, rejected_user):
        data = f"friend_request_status:reject:{rejected_user}"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)

    def send_friends_request_acception(self, accepted_user):
        data = f"friend_request_status:accept:{accepted_user}"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.client.send(size.encode('utf-8'))
            # Send the actual data
            self.client.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)


    def receive_by_size(self, size, buffer_size=16384):
        received_data = bytearray()

        while len(received_data) < size:
            remaining_size = size - len(received_data)
            try:
                chunk = self.client.recv(min(buffer_size, remaining_size))
            except socket.error as e:
                # Handle socket errors, e.g., connection reset
                print(f"Socket error: {e}")
                return None

            if not chunk:
                # Connection closed
                return None

            received_data.extend(chunk)

        return bytes(received_data)

    def recv_login_info(self):
        try:
            size_str = self.client.recv(self.original_len).decode('utf-8')

            # Convert the size string to an integer
            size = int(size_str)

            # Receive the actual data based on the size
            data = self.receive_by_size(size)
            message = json.loads(data)
            username = message.get("username")
            password = message.get("password")
            return username, password
            # Process username and password here
        except json.JSONDecodeError as json_error:
            print(f"Error decoding JSON: {json_error}")

    def recv_str(self):
        try:
            # Receive the size as binary data and convert it to an integer
            size_str = self.client.recv(self.original_len).decode('utf-8')

            # Convert the size string to an integer
            size = int(size_str)

            # Receive the actual data based on the size
            data = self.receive_by_size(size)
            try:
                decoded_data = data.decode('utf-8')
                return decoded_data
            except Exception as e:
                # If decoding as UTF-8 fails, treat it as binary data
                return data

        except (socket.error, ValueError) as e:
            print(f"error is:{e}")


    def return_socket(self):
        return self.client

    def close(self):
        try:
            self.client.close()
        except socket.error as e:
            print(e)


class server_net:
    def __init__(self, s):
        self.server = s
        self.size = 0000000
        self.original_len = 7

    def receive_by_size(self, size, buffer_size=16384):
        received_data = bytearray()

        while len(received_data) < size:
            remaining_size = size - len(received_data)
            try:
                chunk = self.server.recv(min(buffer_size, remaining_size))
            except socket.error as e:
                # Handle socket errors, e.g., connection reset
                print(f"Socket error: {e}")
                return None

            if not chunk:
                # Connection closed
                return None

            received_data.extend(chunk)

        return bytes(received_data)

    def send_str(self, data):
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.server.send(size.encode('utf-8'))
            # Send the actual data
            self.server.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)

    def send_messages_list(self, list):

        encoded_list = json.dumps(list)
        full_message = "messages_list:" + encoded_list

        # Convert the length of the data to a string
        size_str = str(len(full_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.server.send(size.encode('utf-8'))
        self.server.send(full_message.encode())

    def send_requests_list(self, list):
        encoded_list = json.dumps(list)
        full_message = "requests_list:" + encoded_list

        # Convert the length of the data to a string
        size_str = str(len(full_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.server.send(size.encode('utf-8'))
        self.server.send(full_message.encode())


    def send_vc_data(self, vc_data):
        try:
            full_message = vc_data
            full_message = zlib.compress(full_message)
            # Convert the length of the data to a string
            size_str = str(len(full_message))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.server.send(size.encode('utf-8'))
            self.server.send(full_message)
        except Exception as e:
            print(f"error is: {e}")


    def send_friends_list(self, list):
        encoded_list = json.dumps(list)
        full_message = "friends_list:" + encoded_list

        # Convert the length of the data to a string
        size_str = str(len(full_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.server.send(size.encode('utf-8'))
        self.server.send(full_message.encode())

    def send_online_users_list(self, online_users_list):
        encoded_list = json.dumps(online_users_list)
        full_message = "online_users:" + encoded_list

        # Convert the length of the data to a string
        size_str = str(len(full_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.server.send(size.encode('utf-8'))
        self.server.send(full_message.encode())

    def send_user_groups_list(self, group_list):
        encoded_list = json.dumps(group_list)
        full_message = "groups_list:" + encoded_list

        # Convert the length of the data to a string
        size_str = str(len(full_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.server.send(size.encode('utf-8'))
        self.server.send(full_message.encode())

    def send_user_chats_list(self, chats_list):
        encoded_list = json.dumps(chats_list)
        full_message = "chats_list:" + encoded_list

        # Convert the length of the data to a string
        size_str = str(len(full_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        # Send the size as a string
        self.server.send(size.encode('utf-8'))
        self.server.send(full_message.encode())

    def send_user_that_calling(self, user_that_is_calling):
        data = f"call:calling:{user_that_is_calling}"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.server.send(size.encode('utf-8'))
            # Send the actual data
            self.server.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)

    def send_call_dict(self, call_dict):
        encoded_object = json.dumps(call_dict)
        full_message = "call:dict:" + encoded_object

        size_str = str(len(full_message.encode('utf-8')))
        size = str(self.size + int(size_str))
        number_of_zero = self.original_len - len(size)
        size = ("0" * number_of_zero) + size
        self.server.send(size.encode('utf-8'))
        self.server.send(full_message.encode())

    def remove_call_to_user_of_id(self, call_id):
        data = f"call:remove_id:{call_id}"
        try:
            # Convert the length of the data to a string
            size_str = str(len(data.encode('utf-8')))
            size = str(self.size + int(size_str))
            number_of_zero = self.original_len - len(size)
            size = ("0" * number_of_zero) + size
            # Send the size as a string
            self.server.send(size.encode('utf-8'))
            # Send the actual data
            self.server.send(data.encode('utf-8'))

        except socket.error as e:
            print(e)

    def recv_login_info(self):
        try:
            size_str = self.server.recv(self.original_len).decode('utf-8')

            # Convert the size string to an integer
            size = int(size_str)

            # Receive the actual data based on the size
            data = self.receive_by_size(size)
            if data:
                message = json.loads(data)
                format = message.get("format")
                username = message.get("username")
                password = message.get("password")
                email = message.get("email")
                security = message.get("security_token")
                return username, password, format, email, security
            else:
                return None, None, None
            # Process username and password here
        except json.JSONDecodeError as json_error:
            print(f"Error decoding JSON: {json_error}")
        except TypeError as type_error:
            print(f"TypeError: {type_error}")
        except ValueError as e:
            print("Value error")


    def recv_str(self):
        try:
            # Receive the size as binary data and convert it to an integer
            size_str = self.server.recv(self.original_len).decode('utf-8')

            # Convert the size string to an integer
            size = int(size_str)

            # Receive the actual data based on the size
            data = self.receive_by_size(size)
            try:
                decoded_data = data.decode('utf-8')
                return decoded_data
            except Exception as e:
                # If decoding as UTF-8 fails, treat it as binary data
                return data

        except (socket.error, ValueError) as e:
            print(f"error...{e}")


    def return_socket(self):
        return self.server

    def close(self):
        try:
            self.server.close()
        except socket.error as e:
            print(e)