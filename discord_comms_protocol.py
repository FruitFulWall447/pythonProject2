import socket
import json
import time
import zlib
import pickle
import threading
import logging
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding as aes_padding
from cryptography.fernet import Fernet
import secrets


vc_data_sequence = br'\vc_data'
share_screen_sequence = br'\share_screen_data'

def generate_secure_symmetric_key():
    symmetric_key = secrets.token_bytes(32)
    return symmetric_key

def generate_aes_key():
    # Generate a random 256-bit (32-byte) key for AES-256
    aes_key = secrets.token_bytes(32)
    return aes_key


def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    return private_key.public_key(), private_key

def encrypt_with_rsa(public_key, data):
    ciphertext = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(ciphertext).decode("utf-8")

def decrypt_with_rsa(private_key, ciphertext):
    ciphertext = base64.b64decode(ciphertext)
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plaintext


def encrypt_with_aes(key, data):
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()

    # Use PKCS#7 padding
    padder = aes_padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(ciphertext)

def decrypt_with_aes(key, ciphertext):
    try:
        # get ciphertext as bytes
        ciphertext = base64.b64decode(ciphertext)
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the ciphertext
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

        # Use PKCS#7 unpadding
        unpadder = aes_padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()
        # return type bytes
        return unpadded_data
    except Exception as e:
        print(f"Error in decryption: {e}")
        return 1


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
        self.aes_key = None
        self.initiate_rsa_protocol()


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
            encoded_data = data.encode('utf-8')
            encoded_encrypted_data = encrypt_with_aes(self.aes_key, encoded_data)

            # Use the size of encoded_encrypted_data
            size_str = str(len(encoded_encrypted_data))

            # Padding adjustment
            number_of_zero = self.original_len - len(size_str)
            size = ("0" * number_of_zero) + size_str

            # Send the size as a string
            self.client.send(size.encode('utf-8'))

            # Send the actual data
            self.client.send(encoded_encrypted_data)
        except socket.error as e:
            print(e)

    def send_bytes(self, data):
        try:
            # Convert the length of the data to a string
            if self.aes_key is None:
                size_str = str(len(data))
                size = str(self.size + int(size_str))
                number_of_zero = self.original_len - len(size)
                size = ("0" * number_of_zero) + size
                # Send the size as a string
                self.client.send(size.encode('utf-8'))
                # Send the actual data as bytes
                self.client.send(data)
            else:
                encrypted_data = encrypt_with_aes(self.aes_key, data)
                size_str = str(len(encrypted_data))
                size = str(self.size + int(size_str))
                number_of_zero = self.original_len - len(size)
                size = ("0" * number_of_zero) + size
                # Send the size as a string
                self.client.send(size.encode('utf-8'))
                # Send the actual data as bytes
                self.client.send(encrypted_data)
        except socket.error as e:
            print(e)

    def updated_current_chat(self, current_chat):
        try:
            message = f"current_chat:{current_chat}"
            self.send_str(message)
        except socket.error as e:
            print(e)

    def start_stream(self):
        try:
            message = f"call:stream:start"
            self.send_str(message)
        except socket.error as e:
            print(e)

    def close_stream(self):
        try:
            message = f"call:stream:close"
            self.send_str(message)
        except socket.error as e:
            print(e)

    def watch_stream_of_user(self, user):
        try:
            message = f"call:stream:watch:{user}"
            self.send_str(message)
        except socket.error as e:
            print(e)

    def stop_watching_current_stream(self):
        try:
            message = f"call:stream:stop_watch"
            self.send_str(message)
        except socket.error as e:
            print(e)

    def leave_call(self):
        data = f"call:ended"
        try:
            # Convert the length of the data to a string
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_new_password(self, new_password):
        data = f"password:new:{new_password}"
        try:
            # Convert the length of the data to a string
            self.send_str(data)
        except socket.error as e:
            print(e)

    def create_group(self, group_members_list):
        encoded_list = json.dumps(group_members_list)
        full_message = "group:create:" + encoded_list

        self.send_str(full_message)

    def send_calling_user(self, user_that_is_called):
        data = f"call:calling:{user_that_is_called}"
        try:
            # Convert the length of the data to a string
            self.send_str(data)
        except socket.error as e:
            print(e)

    def stop_ringing_to_group_or_user(self):
        data = f"call:calling:stop!"
        try:
            # Convert the length of the data to a string
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_join_call_of_group_id(self, group_id):
        data = f"call:join:{group_id}"
        try:
            # Convert the length of the data to a string
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_accept_call_with(self, accepted_caller):
        data = f"call:accepted:{accepted_caller}"
        try:
            # Convert the length of the data to a string
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_reject_call_with(self, rejected_caller):
        data = f"call:rejected:{rejected_caller}"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def toggle_mute_for_myself(self):
        data = f"call:mute:myself"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def toggle_deafen_for_myself(self):
        data = f"call:deafen:myself"
        try:
            # Convert the length of the data to a string
            self.send_str(data)
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
        self.send_str(encoded_message)

    def send_sign_up_info(self, username, password, email):
        format = "sign up"
        message = {"format": format,
                   "username": username,
                   "password": password,
                   "email": email
                   }
        encoded_message = json.dumps(message)


        self.send_str(encoded_message)

    def send_security_token(self, security_token):
        format = "security token"
        message = {"format": format,
                   "security_token": security_token,
                   }
        encoded_message = json.dumps(message)
        self.send_str(encoded_message)

    def send_username_and_email_froget_password(self, username, password, email):
        format = "forget password"
        message = {"format": format,
                   "username": username,
                   "password": password,
                   "email": email
                   }
        encoded_message = json.dumps(message)

        self.send_str(encoded_message)

    def send_message(self, sender, receiver, content):

        message = {"sender": sender,
                   "receiver": receiver,
                   "content": content,

                   }
        encoded_message = json.dumps(message)
        full_message = "add_message:" + encoded_message

        self.send_str(full_message)

    def send_vc_data(self, vc_data):
        try:
            full_message = vc_data
            compressed_message = zlib.compress(full_message)

            # Add a specific sequence of bytes at the beginning
            sequence = br'\vc_data'  # Use raw string to treat backslash as a literal character
            full_message = sequence + compressed_message
            # Convert the length of the data to a string
            self.send_bytes(full_message)
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
            self.send_bytes(full_message)
        except Exception as e:
            print(f"error is: {e}")

    def send_friend_request(self, username, friend_username):
        data = f"friend_request:{username}:{friend_username}"
        try:
            # Convert the length of the data to a string
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_remove_friend(self, friend_username):
        data = f"friend_remove:{friend_username}"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_friends_request_rejection(self, rejected_user):
        data = f"friend_request_status:reject:{rejected_user}"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_friends_request_acception(self, accepted_user):
        data = f"friend_request_status:accept:{accepted_user}"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def ask_for_security_token(self):
        data = "security_token:needed"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_sign_up_verification_code(self, code):
        data = f"sign_up:verification_code:{code}"
        try:
            self.send_str(data)
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
                encrypted_data = data
                if data is None:
                    print("Received data is None")
                    return None
                data = decrypt_with_aes(self.aes_key, encrypted_data)
                if data.startswith(vc_data_sequence) or data.startswith(share_screen_sequence):
                    return data
                decoded_data = data.decode('utf-8')
                return decoded_data
            except Exception as e:
                print(e)
                return data

        except (socket.error, ValueError) as e:
            print(f"error is:{e}")

    def recv_bytes(self):
        try:
            # Receive the size as binary data and convert it to an integer
            size_str = self.client.recv(self.original_len).decode('utf-8')

            # Convert the size string to an integer
            size = int(size_str)

            # Receive the actual data based on the size
            data = self.receive_by_size(size)
            return data

        except (socket.error, ValueError) as e:
            print(f"Error: {e}")
            return None  # Return None in case of an error


    def return_socket(self):
        return self.client

    def close(self):
        try:
            self.client.close()
        except socket.error as e:
            print(e)

    def initiate_rsa_protocol(self):
        # create 256 bytes key
        client_symmetric_key = generate_secure_symmetric_key()
        public_key_byte_sequence = br'\server:public-key'

        # the client receives the server Rsa public key
        received_serialized_server_public_key_bytes = self.recv_bytes()
        if received_serialized_server_public_key_bytes.startswith(public_key_byte_sequence):
            received_serialized_server_public_key_bytes = received_serialized_server_public_key_bytes[len(public_key_byte_sequence):]
        else:
            print("did not expect message")
            return


        # Deserialize the received public key
        server_public_key = serialization.load_pem_public_key(
            received_serialized_server_public_key_bytes,
            backend=default_backend()
        )


        encrypted_symmetric_key = encrypt_with_rsa(server_public_key, client_symmetric_key)

        # Use send_bytes to send the encrypted key as bytes
        symmetric_key_byte_sequence = br'\server:symmetric-key'
        self.send_bytes(symmetric_key_byte_sequence + encrypted_symmetric_key.encode("utf-8"))

        encrypt_aes_key = self.recv_bytes()
        if encrypt_aes_key.startswith(symmetric_key_byte_sequence):
            encrypt_aes_key = encrypt_aes_key[len(symmetric_key_byte_sequence):]
        aes_key = decrypt_with_aes(client_symmetric_key, encrypt_aes_key)
        self.aes_key = aes_key
        self.logger.info(f"Started to communicate with the server , with AES key {self.aes_key}")


class server_net:
    def __init__(self, s, addr):
        self.client_address = addr
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Create a StreamHandler with the desired format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        self.server = s
        self.size = 0000000
        self.original_len = 7
        self.aes_key = None
        self.initiate_rsa_protocol()


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
            encoded_data = data.encode('utf-8')
            encoded_encrypted_data = encrypt_with_aes(self.aes_key, encoded_data)

            # Use the size of encoded_encrypted_data
            size_str = str(len(encoded_encrypted_data))

            # Padding adjustment
            number_of_zero = self.original_len - len(size_str)
            size = ("0" * number_of_zero) + size_str

            # Send the size as a string
            self.server.send(size.encode('utf-8'))

            # Send the actual data
            self.server.send(encoded_encrypted_data)
        except socket.error as e:
            print(e)

    def send_bytes(self, data):
        try:
            # Convert the length of the data to a string
            if self.aes_key is None:
                size_str = str(len(data))
                size = str(self.size + int(size_str))
                number_of_zero = self.original_len - len(size)
                size = ("0" * number_of_zero) + size
                # Send the size as a string
                self.server.send(size.encode('utf-8'))
                # Send the actual data as bytes
                self.server.send(data)
            else:
                encrypted_data = encrypt_with_aes(self.aes_key, data)
                size_str = str(len(encrypted_data))
                size = str(self.size + int(size_str))
                number_of_zero = self.original_len - len(size)
                size = ("0" * number_of_zero) + size
                # Send the size as a string
                self.server.send(size.encode('utf-8'))
                # Send the actual data as bytes
                self.server.send(encrypted_data)
        except socket.error as e:
            print(e)

    def send_messages_list(self, list):

        encoded_list = json.dumps(list)
        full_message = "messages_list:" + encoded_list

        # Convert the length of the data to a string
        self.send_str(full_message)

    def send_requests_list(self, list):
        encoded_list = json.dumps(list)
        full_message = "requests_list:" + encoded_list

        # Convert the length of the data to a string
        self.send_str(full_message)

    def sent_code_to_mail(self):
        data = f"code:sent:email"
        try:
            # Convert the length of the data to a string
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_vc_data(self, vc_data, speaker):
        try:
            compressed_vc_data = zlib.compress(vc_data)
            sequence = br'\vc_data'  # Use raw string to treat backslash as a literal character
            encoded_speaker = (speaker + ":").encode("utf-8")
            full_message = sequence + encoded_speaker + compressed_vc_data
            # Convert the length of the data to a string
            self.send_bytes(full_message)
        except Exception as e:
            print(f"error is: {e}")

    def send_share_screen_data(self, share_screen_data, speaker):
        try:
            compressed_vc_data = zlib.compress(share_screen_data)
            share_screen_sequence = br'\share_screen_data'
            encoded_speaker = (speaker + ":").encode("utf-8")
            full_message = share_screen_sequence + encoded_speaker + compressed_vc_data
            # Convert the length of the data to a string
            self.send_bytes(full_message)
        except Exception as e:
            print(f"error is: {e}")

    def send_friends_list(self, list):
        encoded_list = json.dumps(list)
        full_message = "friends_list:" + encoded_list

        # Convert the length of the data to a string
        self.send_str(full_message)

    def send_online_users_list(self, online_users_list):
        encoded_list = json.dumps(online_users_list)
        full_message = "online_users:" + encoded_list

        # Convert the length of the data to a string
        self.send_str(full_message)

    def send_user_groups_list(self, group_list):
        encoded_list = json.dumps(group_list)
        full_message = "groups_list:" + encoded_list

        # Convert the length of the data to a string
        self.send_str(full_message)

    def send_user_chats_list(self, chats_list):
        encoded_list = json.dumps(chats_list)
        full_message = "chats_list:" + encoded_list

        # Convert the length of the data to a string
        self.send_str(full_message)

    def send_user_that_calling(self, user_that_is_calling):
        data = f"call:calling:{user_that_is_calling}"
        try:
            # Convert the length of the data to a string
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_call_dict(self, call_dict):
        encoded_object = json.dumps(call_dict)
        full_message = "call:dict:" + encoded_object

        # Convert the length of the data to a string
        self.send_str(full_message)

    def send_call_list_of_dicts(self, call_dicts_list):
        encoded_list = json.dumps(call_dicts_list)
        full_message = "call:list_call_dicts:" + encoded_list

        # Convert the length of the data to a string
        self.send_str(full_message)

    def remove_call_to_user_of_id(self, call_id):
        data = f"call:remove_id:{call_id}"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_stream_of_user_closed(self, user):
        data = f"call:stream:stopped:{user}"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_confirm_login(self):
        data = f"login:confirm"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_invalid_login(self):
        data = f"login:invalid"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_already_logged_in(self):
        data = f"login:already_logged_in"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_sign_up_confirm(self):
        data = f"sign_up:confirm"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_sign_up_invalid(self):
        data = f"sign_up:invalid"
        try:
            self.send_str(data)

        except socket.error as e:
            print(e)

    def send_sign_up_code_invalid(self):
        data = f"sign_up:code:invalid"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_sign_up_code_valid(self):
        data = f"sign_up:code:valid"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_security_token_to_client(self, security_token):
        data = f"security_token:{security_token}"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_security_token_valid(self):
        data = f"security_token:valid"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_security_token_invalid(self):
        data = f"security_token:invalid"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_username_to_client_login_valid(self, username):
        data = f"username:{username}:login:valid"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_username_to_client_login_invalid(self, username):
        data = f"username:{username}:login:invalid"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_forget_password_info_valid(self):
        data = f"forget_password:valid"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_forget_password_info_invalid(self):
        data = f"forget_password:invalid"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_forget_password_code_valid(self):
        data = f"forget_password:code:valid"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def send_forget_password_code_invalid(self):
        data = f"forget_password:code:invalid"
        try:
            self.send_str(data)
        except socket.error as e:
            print(e)

    def recv_login_info(self):
        try:
            size_str = self.server.recv(self.original_len).decode('utf-8')

            # Convert the size string to an integer
            size = int(size_str)

            # Receive the actual data based on the size
            encrypted_data = self.receive_by_size(size)
            print(encrypted_data)
            if encrypted_data:
                data = decrypt_with_aes(self.aes_key, encrypted_data)
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
                encrypted_data = data
                if data is None:
                    print("Received data is None")
                    return None
                data = decrypt_with_aes(self.aes_key, encrypted_data)
                if data.startswith(vc_data_sequence) or data.startswith(share_screen_sequence):
                    return data
                else:
                    decoded_data = data.decode('utf-8')
                    return decoded_data
            except Exception as e:
                # If decoding as UTF-8 fails, treat it as binary data
                return data

        except (socket.error, ValueError) as e:
            self.logger.error(f"Error: {e}")
            self.logger.info("Clearing socket buffer...")
            # Clear the socket buffer by receiving and discarding remaining data
            try:
                while True:
                    discarded_data = self.server.recv(4096)
                    if not discarded_data:
                        break  # No more data to receive
                return 1
            except socket.error as e:
                self.logger.error(f"Error while clearing socket buffer: {e}")

                return None  # Return None to indicate failure due to unexpected data


    def recv_bytes(self):
        try:
            # Receive the size as binary data and convert it to an integer
            size_str = self.server.recv(self.original_len).decode('utf-8')

            # Convert the size string to an integer
            size = int(size_str)

            # Receive the actual data based on the size
            data = self.receive_by_size(size)
            return data

        except (socket.error, ValueError) as e:
            print(f"Error: {e}")
            return None  # Return None in case of an error


    def return_socket(self):
        return self.server

    def close(self):
        try:
            self.server.close()
        except socket.error as e:
            print(e)

    def initiate_rsa_protocol(self):
        server_public_key, server_private_key = generate_rsa_key_pair()

        # send the server_public_key to the client
        serialized_server_public_key = server_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        public_key_byte_sequence = br'\server:public-key'
        self.send_bytes(public_key_byte_sequence + serialized_server_public_key)

        symmetric_key_byte_sequence = br'\server:symmetric-key'

        received_encrypted_symmetric_key_bytes = self.recv_bytes()
        if received_encrypted_symmetric_key_bytes.startswith(symmetric_key_byte_sequence):
            received_encrypted_symmetric_key_bytes = received_encrypted_symmetric_key_bytes[len(symmetric_key_byte_sequence):]
        else:
            self.logger.critical("did not expect this kind of message")
            return
        if received_encrypted_symmetric_key_bytes is not None:
            decrypted_symmetric_key = decrypt_with_rsa(server_private_key, received_encrypted_symmetric_key_bytes)
            aes_key = generate_aes_key()
            self.logger.info(f"Started to communicate with client {self.client_address}, with AES key {aes_key}")
            try:
                encrypted_aes_key = encrypt_with_aes(decrypted_symmetric_key, aes_key)
                self.send_bytes(symmetric_key_byte_sequence + encrypted_aes_key)
                self.aes_key = aes_key
            except Exception as e:
                print(e)


        else:
            print("Error receiving the symmetric key.")