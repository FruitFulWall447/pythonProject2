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
import struct
import pickle

vc_data_sequence = br'\vc_data'
share_screen_sequence = br'\share_screen_data'
share_camera_sequence = br'\share_camera_data'


def create_dictionary_with_message_type(message_type, keys, values):
    # Ensure both lists have the same length
    if len(keys) != len(values):
        raise ValueError("Lists must have the same length")

    # Add the message_type as the first key-value pair
    keys.insert(0, 'message_type')
    values.insert(0, message_type)

    # Create the dictionary using a dictionary comprehension
    result = {keys[i]: values[i] for i in range(len(keys))}

    return result


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


def send_data_in_chunks(sock, data):
    """Send data over a socket in chunks.

    Args:
        sock (socket.socket): The socket object for sending data.
        data (bytes): The data to be sent.

    Returns:
        bool: True if the data was sent successfully, False otherwise.
    """
    try:
        # Define the chunk size
        chunk_size = 4096  # Adjust this based on your requirements

        # Send data in chunks
        bytes_sent = 0
        while bytes_sent < len(data):
            chunk = data[bytes_sent:bytes_sent + chunk_size]
            bytes_sent += sock.send(chunk)

        return True

    except Exception as e:
        print(f"Error sending data: {e}")
        return False


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
        self.original_len = 10
        self.aes_key = None
        self.sending_data_lock = threading.Lock()
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
            self.sending_data_lock.acquire()
            encoded_data = data.encode('utf-8')
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
        finally:
            # Release the lock
            self.sending_data_lock.release()

    def send_bytes(self, data):
        try:
            # Convert the length of the data to a string
            self.sending_data_lock.acquire()
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
        finally:
            # Release the lock
            self.sending_data_lock.release()

    def send_message_dict(self, message_dict):
        try:
            pickled_data = pickle.dumps(message_dict)
            self.send_bytes(pickled_data)
        except Exception as e:
            print(e)

    def updated_current_chat(self, current_chat):
        try:
            message = {"message_type": "current_chat", "current_chat": current_chat}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def start_screen_stream(self):
        try:
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": "ScreenStream", "action": "start"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def close_screen_stream(self):
        try:
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": "ScreenStream", "action": "close"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def start_camera_stream(self):
        try:
            stream_type = "CameraStream"
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": stream_type, "action": "start"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def close_camera_stream(self):
        try:
            stream_type = "CameraStream"
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": stream_type, "action": "close"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def watch_screen_stream_of_user(self, user):
        try:
            stream_type = "ScreenStream"
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": stream_type,
                       "action": "close", "user_to_watch": user}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def watch_camera_stream_of_user(self, user):
        try:
            stream_type = "CameraStream"
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": stream_type,
                       "action": "watch", "user_to_watch": user}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def stop_watching_current_stream(self):
        try:
            message = {"message_type": "call", "call_type": "stream",
                       "action": "stop_watch"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def leave_call(self):
        try:
            # Convert the length of the data to a string
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "ended"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_new_password(self, new_password):
        try:
            message = {"message_type": "password",
                       "action": "new_password", "new_password": new_password}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_new_group_image_to_server(self, image_bytes, group_id):
        encoded_b64_image = base64.b64encode(image_bytes).decode('utf-8')
        message = {"message_type": "group",
                   "action": "update_image", "group_id": group_id, "encoded_b64_image": encoded_b64_image}
        self.send_message_dict(message)

    def create_group(self, group_members_list):
        json_group_members_list = json.dumps(group_members_list)
        message = {"message_type": "group",
                   "action": "create", "group_members_list": json_group_members_list}
        self.send_message_dict(message)

    def send_calling_user(self, user_that_is_called):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "calling", "calling_to": user_that_is_called}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def stop_ringing_to_group_or_user(self):
        try:
            message = {"message_type": "call", "call_action_type": "change_calling_status",
                       "action": "stop!"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_join_call_of_group_id(self, group_id):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "join_call", "group_id": group_id}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_accept_call_with(self, accepted_caller):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "accepted_call", "accepted_caller": accepted_caller}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_reject_call_with(self, rejected_caller):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "rejected_call", "rejected_caller": rejected_caller}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def toggle_mute_for_myself(self):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "mute_myself"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def toggle_deafen_for_myself(self):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "deafen_myself"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_login_info(self, username, password):

        message = {"message_type": "login", "username": username,
                   "password": password}
        self.send_message_dict(message)

    def send_sign_up_info(self, username, password, email):
        message_format = "sign_up"
        message = {"message_type": message_format, "username": username,
                   "password": password, "email": email}
        self.send_message_dict(message)

    def send_security_token(self, security_token):
        message_format = "security_token"
        message = {"message_type": message_format, "security_token": security_token}
        self.send_message_dict(message)

    def send_username_and_email_froget_password(self, username, password, email):
        message_format = "forget password"
        message = {"message_type": message_format, "username": username,
                   "email": email}
        self.send_message_dict(message)

    def send_message(self, sender, receiver, content, type, file_name):
        if isinstance(content, bytes):
            # If content is bytes, encode it as a Base64 string
            content = base64.b64encode(content).decode('utf-8')
        message_format = "add_message"
        message = {"message_type": message_format, "sender": sender,
                   "receiver": receiver,
                   "content": content,
                   "type": type,
                   "file_name": file_name
                   }
        self.send_message_dict(message)

    def send_profile_pic(self, profile_pic):
        if isinstance(profile_pic, bytes):
            # If content is bytes, encode it as a Base64 string
            content = base64.b64encode(profile_pic).decode('utf-8')
        elif profile_pic is None:
            str_profile_pic = "None"
            content = str_profile_pic
        message_format = "update_profile_pic"
        message = {"message_type": message_format, "b64_encoded_profile_pic": content
                   }
        self.send_message_dict(message)

    def send_vc_data(self, vc_data):
        try:
            full_message = vc_data
            compressed_message = zlib.compress(full_message)
            message_format = "vc_data"
            message = {"message_type": message_format, "compressed_vc_data": compressed_message
                       }
            self.send_message_dict(message)
        except Exception as e:
            print(f"error in send vc data is: {e}")

    def send_share_screen_data(self, share_screen_data, shape_of_frame):
        try:
            full_message = share_screen_data
            compressed_message = zlib.compress(full_message)
            message_format = "share_screen_data"
            message = {"message_type": message_format, "compressed_share_screen_data": compressed_message,
                       "shape_of_frame": shape_of_frame
                       }
            self.send_message_dict(message)
        except Exception as e:
            print(f"error is in send share screen data: {e}")

    def send_share_camera_data(self, share_camera_data, shape_of_frame):
        try:
            full_message = share_camera_data
            compressed_message = zlib.compress(full_message)
            message_format = "share_camera_data"
            message = {"message_type": message_format, "compressed_share_camera_data": compressed_message,
                       "shape_of_frame": shape_of_frame
                       }
            self.send_message_dict(message)
        except Exception as e:
            print(f"error is send share camera data: {e}")

    def send_friend_request(self, username, friend_username):
        try:
            # Convert the length of the data to a string
            message = {"message_type": "friend_request", "username_for_request": friend_username
                       }
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_remove_friend(self, friend_username):
        try:
            message = {"message_type": "friend_remove", "username_to_remove": friend_username
                       }
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def block_user(self, user_to_block):
        try:
            message = {"message_type": "block", "user_to_block": user_to_block
                       }
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def unblock_user(self, user_to_unblock):
        try:
            message = {"message_type": "unblock", "user_to_unblock": user_to_unblock
                       }
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_friends_request_rejection(self, rejected_user):
        try:
            message = {"message_type": "friend_request_status", "action": "reject", "rejected_user": rejected_user
                       }
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_friends_request_acception(self, accepted_user):
        try:
            message = {"message_type": "friend_request_status", "action": "accept", "accepted_user": accepted_user
                       }
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def ask_for_security_token(self):
        try:
            message = {"message_type": "security_token", "action": "needed"
                       }
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_sign_up_verification_code(self, code):
        try:
            message = {"message_type": "sign_up", "action": "verification_code", "code": code
                       }
            self.send_message_dict(message)
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
                return pickle.loads(data)
            except Exception as e:
                print(f"error in receiving data: {e}")
                return data

        except (socket.error, ValueError) as e:
            print(f"error is in recv_str:{e}")

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
        self.original_len = 10
        self.aes_key = None
        self.sending_data_lock = threading.Lock()
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
            self.sending_data_lock.acquire()
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
        finally:
            # Release the lock
            self.sending_data_lock.release()

    def send_bytes(self, data):
        try:
            self.sending_data_lock.acquire()
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
        finally:
            # Release the lock
            self.sending_data_lock.release()

    def send_message_dict(self, message_dict):
        try:
            pickled_data = pickle.dumps(message_dict)
            self.send_bytes(pickled_data)
        except Exception as e:
            print(e)

    def send_messages_list(self, messages_list):
        json_messages_list = json.dumps(messages_list)
        message = {"message_type": "messages_list", "messages_list": json_messages_list
                   }
        self.send_message_dict(message)

    def send_new_message(self, message):
        message = {"message_type": "new_message", "new_message": message
                   }
        self.send_message_dict(message)

    def send_new_message_of_other_chat(self):
        message = {"message_type": "new_message", "new_message": ""
                   }
        self.send_message_dict(message)

    def send_requests_list(self, list):
        json_requests_list = json.dumps(list)
        message = {"message_type": "requests_list", "requests_list": json_requests_list
                   }
        self.send_message_dict(message)

    def sent_code_to_mail(self):
        try:
            # Convert the length of the data to a string
            message = {"message_type": "code", "action": "sent", "sent_to": "email"
                       }
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def sent_friend_request_status(self, status):
        try:
            # Convert the length of the data to a string
            message = {"message_type": "friend_request", "friend_request_status": status}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_vc_data(self, vc_data, speaker):
        try:
            compressed_vc_data = zlib.compress(vc_data)
            message = {"message_type": "vc_data", "compressed_vc_data": compressed_vc_data, "speaker": speaker
                       }
            self.send_message_dict(message)
        except Exception as e:
            print(f"error in send vc data is: {e}")

    def send_share_screen_data(self, share_screen_data, speaker, shape_of_frame_bytes):
        try:
            compressed_share_screen_data = zlib.compress(share_screen_data)
            message = {"message_type": "share_screen_data", "compressed_share_screen_data":
                compressed_share_screen_data, "speaker": speaker, "frame_shape": shape_of_frame_bytes
                       }
            self.send_message_dict(message)
        except Exception as e:
            print(f"error in send share screen data is: {e}")

    def send_share_camera_data(self, share_camera_data, speaker, shape_of_frame_bytes):
        try:
            compressed_share_screen_data = zlib.compress(share_camera_data)
            message = {"message_type": "share_camera_data",
                       "compressed_share_camera_data": compressed_share_screen_data,
                       "speaker": speaker, "frame_shape": shape_of_frame_bytes
                       }
            self.send_message_dict(message)
        except Exception as e:
            print(f"error in send camera data is: {e}")

    def send_friends_list(self, friends_list):
        json_friends_list = json.dumps(friends_list)
        message = {"message_type": "friends_list",
                   "friends_list": json_friends_list
                   }
        self.send_message_dict(message)

    def send_blocked_list(self, blocked_list):
        json_blocked_list = json.dumps(blocked_list)
        message = {"message_type": "blocked_list",
                   "blocked_list": json_blocked_list
                   }
        self.send_message_dict(message)

    def send_online_users_list(self, online_users_list):
        json_online_users_list = json.dumps(online_users_list)
        message = {"message_type": "online_users_list",
                   "online_users_list": json_online_users_list
                   }
        self.send_message_dict(message)

    def send_user_groups_list(self, group_list):
        json_group_list = json.dumps(group_list)
        message = {"message_type": "groups_list",
                   "groups_list": json_group_list
                   }
        self.send_message_dict(message)

    def send_user_chats_list(self, chats_list):
        json_chats_list = json.dumps(chats_list)
        message = {"message_type": "chats_list",
                   "chats_list": json_chats_list
                   }
        self.send_message_dict(message)

    def send_user_that_calling(self, user_that_is_calling):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "calling", "user_that_called": user_that_is_calling}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_user_that_call_ended(self):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "ended"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_user_that_call_accepted(self):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "accepted"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_user_call_timeout(self):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "timeout"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_call_dict(self, call_dict):
        message = {"message_type": "call", "call_action_type": "call_dictionary",
                   "action": "dict", "dict": call_dict}
        self.send_message_dict(message)

    def send_call_list_of_dicts(self, call_dicts_list):
        json_call_dicts_list = json.dumps(call_dicts_list)
        message = {"message_type": "call", "call_action_type": "call_dictionary",
                   "action": "list_call_dicts", "list_call_dicts": json_call_dicts_list}
        self.send_message_dict(message)

    def send_profile_list_of_dicts(self, profile_dicts_list):
        json_profile_dicts_list = json.dumps(profile_dicts_list)
        message = {"message_type": "profile_dicts_list", "profile_dicts_list": json_profile_dicts_list}
        self.send_message_dict(message)

    def send_profile_dict_of_user(self, profile_dict, user):
        json_profile_dict = json.dumps(profile_dict)
        message = {"message_type": "updated_profile_dict", "profile_dict": json_profile_dict, "username": user}
        self.send_message_dict(message)

    def remove_call_to_user_of_id(self, call_id):
        try:
            message = {"message_type": "call", "call_action_type": "update_calls",
                       "action": "remove_id", "removed_id": call_id}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_stream_of_user_closed(self, user):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "stream_stopped", "user_that_stopped": user}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_confirm_login(self):
        try:
            message = {"message_type": "login", "login_status": "confirm"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_invalid_login(self):
        try:
            message = {"message_type": "login", "login_status": "invalid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_already_logged_in(self):
        try:
            message = {"message_type": "login", "login_status": "already_logged_in"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_sign_up_confirm(self):
        try:
            message = {"message_type": "sign_up", "sign_up_status": "confirm"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_sign_up_invalid(self):
        try:
            message = {"message_type": "sign_up", "sign_up_status": "invalid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_sign_up_code_invalid(self):
        try:
            message = {"message_type": "sign_up", "action": "code", 'code_status': "invalid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_sign_up_code_valid(self):
        try:
            message = {"message_type": "sign_up", "action": "code", 'code_status': "valid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_all_data_received(self):
        try:
            message = {"message_type": "data", "action": "receive", 'receive_status': "done"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_security_token_to_client(self, security_token):
        try:
            message = {"message_type": "security_token", "security_token": security_token}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_security_token_valid(self):
        try:
            message = {"message_type": "security_token", "security_status": "valid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_security_token_invalid(self):
        try:
            message = {"message_type": "security_token", "security_status": "invalid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_username_to_client_login_valid(self, username):
        try:
            message = {"message_type": "login_action", "username": username, "login_status": "valid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_username_to_client_login_invalid(self, username):
        try:
            message = {"message_type": "login_action", "username": username, "login_status": "invalid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_forget_password_info_valid(self):
        try:
            message = {"message_type": "forget_password", "forget_password_status": "valid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_forget_password_info_invalid(self):
        try:
            message = {"message_type": "forget_password", "forget_password_status": "invalid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_forget_password_code_valid(self):
        try:
            message = {"message_type": "forget_password", "action": "code", "code_status": "valid"}
            self.send_message_dict(message)
        except socket.error as e:
            print(e)

    def send_forget_password_code_invalid(self):
        try:
            message = {"message_type": "forget_password", "action": "code", "code_status": "invalid"}
            self.send_message_dict(message)
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
                return pickle.loads(data)
            except Exception as e:
                # If decoding as UTF-8 fails, treat it as binary data
                print(f"error in receiving data: {e}")
                return data

        except (socket.error, ValueError) as e:
            self.logger.error(f"Error: {e}")
            self.logger.info("Clearing socket buffer...")
            # Clear the socket buffer by receiving and discarding remaining data
            data = "error:disconnect"
            self.send_str(data)
            return None

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