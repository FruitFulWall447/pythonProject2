import socket
import json
import zlib
import threading
import logging
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding as aes_padding
import secrets
import pickle
vc_data_sequence = br'\vc_data'
share_screen_sequence = br'\share_screen_data'
share_camera_sequence = br'\share_camera_data'


def slice_up_data(data, mtu):
    sliced_data = []
    for start_index in range(0, len(data), mtu):
        end_index = start_index + mtu
        sliced_data.append(data[start_index:end_index])
    return sliced_data


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
        if isinstance(ciphertext, int):
            return 1
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


class ClientNet:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Create a StreamHandler with the desired format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # Add the StreamHandler to the logger
        self.logger.addHandler(stream_handler)
        self.client_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_ip = "127.0.0.1"
        self.port = 5555
        self.addr = (self.server_ip, self.port)
        self.logger.debug(f"trying to connect to addr: {self.addr}")
        self.size = 0000000
        self.original_len = 10
        self.mtu = None
        self.aes_key = None
        self.connected = False
        self.sending_tcp_data_lock = threading.Lock()

    def if_connected(self):
        self.connect_udp()
        self.initiate_rsa_protocol()
        self.check_max_packet_size_udp()

    def connect_tcp(self):
        try:
            self.client_tcp_socket.connect(self.addr)
            self.logger.info("tcp socket connected to server")
            self.if_connected()
            return True
        except Exception as e:
            self.logger.info(f"couldn't connect tcp socket to server {e}")
            return False

    def connect_udp(self):
        try:
            self.client_udp_socket.connect(self.addr)
            self.logger.info("udp socket connected to server")
            address = self.client_udp_socket.getsockname()
            print("Socket address:", address)
        except:
            self.logger.info("couldn't connect udp socket to server")
            pass

    def send_bytes(self, data):
        try:
            # Convert the length of the data to a string
            self.sending_tcp_data_lock.acquire()
            if self.aes_key is None:
                size_str = str(len(data))
                size = str(self.size + int(size_str))
                number_of_zero = self.original_len - len(size)
                size = ("0" * number_of_zero) + size
                # Send the size as a string
                self.client_tcp_socket.send(size.encode('utf-8'))
                # Send the actual data as bytes
                self.client_tcp_socket.send(data)
            else:
                encrypted_data = encrypt_with_aes(self.aes_key, data)
                size_str = str(len(encrypted_data))
                size = str(self.size + int(size_str))
                number_of_zero = self.original_len - len(size)
                size = ("0" * number_of_zero) + size
                # Send the size as a string
                self.client_tcp_socket.send(size.encode('utf-8'))
                # Send the actual data as bytes
                self.client_tcp_socket.send(encrypted_data)
        except socket.error as e:
            print(e)
        finally:
            # Release the lock
            self.sending_tcp_data_lock.release()

    def send_large_udp_data(self, data, data_type, shape_of_frame=None):
        if len(data) > self.mtu:
            sliced_data = slice_up_data(data, int(self.mtu * 0.8))
        else:
            sliced_data = [data]

        for i, data_slice in enumerate(sliced_data):
            message = {
                "message_type": data_type,
                "is_first": i == 0,
                "is_last": i == len(sliced_data) - 1,
                "sliced_data": data_slice,
                "shape_of_frame": shape_of_frame
            }
            self.send_message_dict_udp(message)

    def send_bytes_udp(self, data):
        try:
            # Encrypt the data if encryption is enabled
            if self.aes_key is not None:
                encrypted_data = encrypt_with_aes(self.aes_key, data)
                data = encrypted_data

            self.client_udp_socket.sendto(data, self.addr)
        except socket.error as e:
            print(f"error in sending udp {e} , data size = {len(data)}")
            raise

    def check_max_packet_size_udp(self):
        data = b'a'
        try:
            while True:
                self.send_bytes_udp(data)
                data += (b'a' * 100)
        except socket.error as e:
            self.logger.info(f"Network mtu is: {len(data) - 10}")
            self.mtu = len(data) - 10

    def send_message_dict_udp(self, message_dict):
        try:
            pickled_data = pickle.dumps(message_dict)
            self.send_bytes_udp(pickled_data)
        except Exception as e:
            print(e)

    def send_message_dict_tcp(self, message_dict):
        try:
            pickled_data = pickle.dumps(message_dict)
            self.send_bytes(pickled_data)
        except Exception as e:
            print(e)

    def connect_between_udp_port_address_to_username(self):
        udp_address = self.client_udp_socket.getsockname()
        tcp_address = self.client_tcp_socket.getsockname()
        message = {"message_type": "connect_udp_port", "udp_address": udp_address, "tcp_address": tcp_address}
        self.send_message_dict_tcp(message)

    def send_song_search(self, search_str):
        try:
            message = {"message_type": "song_search", "search_str": search_str}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_remove_song_from_playlist(self, song_title):
        try:
            message = {"message_type": "remove_song", "song_title": song_title}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def save_song_in_playlist(self, song_dict):
        try:
            message = {"message_type": "save_song", "song_dict": song_dict}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def ask_for_song_bytes_by_playlist_index(self, index):
        try:
            message = {"message_type": "playlist_song_bytes_by_index", "index": index}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def updated_current_chat(self, current_chat):
        try:
            message = {"message_type": "current_chat", "current_chat": current_chat}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def ask_for_more_messages(self):
        try:
            message = {"message_type": "more_messages"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def start_screen_stream(self):
        try:
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": "ScreenStream", "action": "start"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def close_screen_stream(self):
        try:
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": "ScreenStream", "action": "close"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def start_camera_stream(self):
        try:
            stream_type = "CameraStream"
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": stream_type, "action": "start"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def close_camera_stream(self):
        try:
            stream_type = "CameraStream"
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": stream_type, "action": "close"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def watch_screen_stream_of_user(self, user):
        try:
            stream_type = "ScreenStream"
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": stream_type,
                       "action": "watch", "user_to_watch": user}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def watch_camera_stream_of_user(self, user):
        try:
            stream_type = "CameraStream"
            message = {"message_type": "call", "call_action_type": "stream", "stream_type": stream_type,
                       "action": "watch", "user_to_watch": user}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def stop_watching_current_stream(self):
        try:
            message = {"message_type": "call", "call_action_type": "stream",
                       "action": "stop_watch"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def leave_call(self):
        try:
            # Convert the length of the data to a string
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "ended"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_new_password(self, new_password):
        try:
            message = {"message_type": "password",
                       "action": "new_password", "new_password": new_password}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_new_group_image_to_server(self, image_bytes, group_id):
        encoded_b64_image = base64.b64encode(image_bytes).decode('utf-8')
        message = {"message_type": "group",
                   "action": "update_image", "group_id": group_id, "encoded_b64_image": encoded_b64_image}
        self.send_message_dict_tcp(message)

    def create_group(self, group_members_list):
        json_group_members_list = json.dumps(group_members_list)
        message = {"message_type": "group",
                   "action": "create", "group_members_list": json_group_members_list}
        self.send_message_dict_tcp(message)

    def add_user_to_group(self, group_id, users_list):
        message = {"message_type": "group", "action": "add_user",
                   "group_id": group_id, "users_to_add": json.dumps(users_list)}
        self.send_message_dict_tcp(message)

    def send_calling_user(self, user_that_is_called):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "calling", "calling_to": user_that_is_called}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def stop_ringing_to_group_or_user(self):
        try:
            message = {"message_type": "call", "call_action_type": "change_calling_status",
                       "action": "stop!"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_join_call_of_group_id(self, group_id):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "join_call", "group_id": group_id}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_accept_call_with(self, accepted_caller):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "accepted_call", "accepted_caller": accepted_caller}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_reject_call_with(self, rejected_caller):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "rejected_call", "rejected_caller": rejected_caller}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def toggle_mute_for_myself(self):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "mute_myself"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def toggle_deafen_for_myself(self):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "deafen_myself"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_login_info(self, username, password):

        message = {"message_type": "login", "username": username,
                   "password": password}
        self.send_message_dict_tcp(message)

    def send_sign_up_info(self, username, password, email):
        message_format = "sign_up"
        message = {"message_type": message_format, "username": username,
                   "password": password, "email": email}
        self.send_message_dict_tcp(message)

    def send_security_token(self, security_token):
        message_format = "security_token"
        message = {"message_type": message_format, "security_token": security_token}
        self.send_message_dict_tcp(message)

    def send_username_and_email_froget_password(self, username, password, email):
        message_format = "forget password"
        message = {"message_type": message_format, "username": username,
                   "email": email}
        self.send_message_dict_tcp(message)

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
        self.send_message_dict_tcp(message)

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
        self.send_message_dict_tcp(message)

    def send_vc_data(self, vc_data):
        try:
            full_message = vc_data
            compressed_message = zlib.compress(full_message)
            message_format = "vc_data"
            self.send_large_udp_data(compressed_message, message_format)
        except Exception as e:
            print(f"error in send vc data is: {e}")

    def send_share_screen_data(self, share_screen_data, shape_of_frame):
        try:
            full_message = share_screen_data
            compressed_message = zlib.compress(full_message)
            message_format = "share_screen_data"
            self.send_large_udp_data(compressed_message, message_format, shape_of_frame)
        except Exception as e:
            print(f"error is in send share screen data: {e}")

    def send_share_camera_data(self, share_camera_data, shape_of_frame):
        try:
            full_message = share_camera_data
            compressed_message = zlib.compress(full_message)
            message_format = "share_camera_data"
            self.send_large_udp_data(compressed_message, message_format, shape_of_frame)
        except Exception as e:
            print(f"error is send share camera data: {e}")

    def send_settings_dict_to_server(self, settings_dict):
        try:
            message = {"message_type": "settings_dict", "settings_dict": settings_dict
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_friend_request(self, friend_username):
        try:
            # Convert the length of the data to a string
            message = {"message_type": "friend_request", "username_for_request": friend_username
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_remove_friend(self, friend_username):
        try:
            message = {"message_type": "friend_remove", "username_to_remove": friend_username
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_exit_group(self, group_id):
        try:
            message = {"message_type": "exit_group", "group_to_exit_id": group_id
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_remove_chat(self, chat):
        try:
            message = {"message_type": "remove_chat", "chat_to_remove": chat
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_remove_user_from_group(self, user, group_id):
        try:
            message = {"message_type": "remove_user_from_group", "user_to_remove": user
                       , "group_id": group_id
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def block_user(self, user_to_block):
        try:
            message = {"message_type": "block", "user_to_block": user_to_block
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def unblock_user(self, user_to_unblock):
        try:
            message = {"message_type": "unblock", "user_to_unblock": user_to_unblock
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_friends_request_rejection(self, rejected_user):
        try:
            message = {"message_type": "friend_request_status", "action": "reject", "rejected_user": rejected_user
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_friends_request_acception(self, accepted_user):
        try:
            message = {"message_type": "friend_request_status", "action": "accept", "accepted_user": accepted_user
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def ask_for_security_token(self):
        try:
            message = {"message_type": "security_token", "action": "needed"
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def update_security_token(self):
        try:
            message = {"message_type": "security_token", "action": "update"
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_sign_up_verification_code(self, code):
        try:
            message = {"message_type": "sign_up", "action": "verification_code", "code": code
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_login_2fa_code(self, code):
        try:
            message = {"message_type": "login", "action": "2fa", "code": code
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_logout_message(self):
        try:
            message = {"message_type": "logout"
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def receive_by_size(self, size, buffer_size=16384):
        received_data = bytearray()

        while len(received_data) < size:
            remaining_size = size - len(received_data)
            try:
                chunk = self.client_tcp_socket.recv(min(buffer_size, remaining_size))
            except socket.error as e:
                # Handle socket errors, e.g., connection reset
                print(f"Socket error: {e}")
                return None

            if not chunk:
                # Connection closed
                return None

            received_data.extend(chunk)

        return bytes(received_data)

    def recv_str(self):
        try:
            # Receive the size as binary data and convert it to an integer
            size_str = self.client_tcp_socket.recv(self.original_len).decode('utf-8')

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
            print(f"error in recv_str:{e}")
            return None

    def recv_bytes(self):
        try:
            # Receive the size as binary data and convert it to an integer
            size_str = self.client_tcp_socket.recv(self.original_len).decode('utf-8')

            # Convert the size string to an integer
            size = int(size_str)

            # Receive the actual data based on the size
            data = self.receive_by_size(size)
            return data

        except (socket.error, ValueError) as e:
            print(f"Error: {e}")
            return None  # Return None in case of an error

    def recv_udp(self):
        fragment_data, address = self.client_udp_socket.recvfrom(100000)
        return decrypt_with_aes(self.aes_key, fragment_data), address

    def return_socket(self):
        return self.client_tcp_socket

    def close(self):
        try:
            self.client_tcp_socket.close()
            self.client_udp_socket.close()
        except socket.error as e:
            print(e)

    def initiate_rsa_protocol(self):
        # create 256 bytes key
        client_symmetric_key = generate_aes_key()
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