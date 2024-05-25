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


class ServerNet:
    def __init__(self, s, addr):
        self.client_tcp_socket_address = addr
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
        self.sending_tcp_data_lock = threading.Lock()
        self.initiate_rsa_protocol()

    def get_aes_key(self):
        return self.aes_key

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
            self.sending_tcp_data_lock.acquire()
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
            self.sending_tcp_data_lock.release()

    def send_bytes(self, data):
        try:
            self.sending_tcp_data_lock.acquire()
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
            self.sending_tcp_data_lock.release()

    def send_message_dict_tcp(self, message_dict):
        try:
            pickled_data = pickle.dumps(message_dict)
            self.send_bytes(pickled_data)
        except Exception as e:
            print(e)

    def send_played_song_bytes(self, song_bytes, title):
        message = {"message_type": "playlist_current_song_bytes", "audio_bytes": song_bytes, "title": title
                   }
        self.send_message_dict_tcp(message)

    def send_searched_song_info(self, searched_song_dict):
        message = {"message_type": "searched_song_result", "searched_song_dict": searched_song_dict
                   }
        self.send_message_dict_tcp(message)

    def send_settings_dict(self, settings_dict):
        message = {"message_type": "settings_dict", "settings_dict": settings_dict
                   }
        self.send_message_dict_tcp(message)

    def send_messages_list(self, messages_list):
        json_messages_list = json.dumps(messages_list)
        message = {"message_type": "messages_list", "messages_list": json_messages_list
                   }
        self.send_message_dict_tcp(message)

    def send_addition_messages_list(self, addition_messages_list):
        json_messages_list = json.dumps(addition_messages_list)
        message = {"message_type": "message_list_addition", "message_list_addition": json_messages_list
                   }
        self.send_message_dict_tcp(message)

    def send_new_message_content(self, chat, message_dict):
        message = {"message_type": "new_message",
                   "chat_name": chat,
                   "message_dict": json.dumps(message_dict)
                   }
        self.send_message_dict_tcp(message)

    def send_requests_list(self, list):
        json_requests_list = json.dumps(list)
        message = {"message_type": "requests_list", "requests_list": json_requests_list
                   }
        self.send_message_dict_tcp(message)

    def sent_code_to_mail(self):
        try:
            # Convert the length of the data to a string
            message = {"message_type": "code", "action": "sent", "sent_to": "email"
                       }
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def sent_friend_request_status(self, status):
        try:
            # Convert the length of the data to a string
            message = {"message_type": "friend_request", "friend_request_status": status}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_username_to_client(self, username):
        try:
            # Convert the length of the data to a string
            message = {"message_type": "login_action", "username": username, "login_status": True}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_username_to_client_and_2fa(self, username):
        try:
            # Convert the length of the data to a string
            message = {"message_type": "login_action", "username": username, "login_status": "2fa"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_vc_data(self, vc_data, speaker):
        try:
            compressed_vc_data = zlib.compress(vc_data)
            message = {"message_type": "vc_data", "compressed_vc_data": compressed_vc_data, "speaker": speaker
                       }
            self.send_message_dict_tcp(message)
        except Exception as e:
            print(f"error in send vc data is: {e}")

    def send_share_screen_data(self, share_screen_data, speaker, shape_of_frame_bytes):
        try:
            compressed_share_screen_data = zlib.compress(share_screen_data)
            message = {"message_type": "share_screen_data", "compressed_share_screen_data":
                compressed_share_screen_data, "speaker": speaker, "frame_shape": shape_of_frame_bytes
                       }
            self.send_message_dict_tcp(message)
        except Exception as e:
            print(f"error in send share screen data is: {e}")

    def send_share_camera_data(self, share_camera_data, speaker, shape_of_frame_bytes):
        try:
            compressed_share_screen_data = zlib.compress(share_camera_data)
            message = {"message_type": "share_camera_data",
                       "compressed_share_camera_data": compressed_share_screen_data,
                       "speaker": speaker, "frame_shape": shape_of_frame_bytes
                       }
            self.send_message_dict_tcp(message)
        except Exception as e:
            print(f"error in send camera data is: {e}")

    def send_to_client_he_has_all_of_the_messages(self):
        message = {"message_type": "messages_status",
                   "messages_status": "up_to_data"
                   }
        self.send_message_dict_tcp(message)

    def add_new_chat(self, chat_to_add):
        message = {"message_type": "add_chat",
                   "chat_to_add": chat_to_add
                   }
        self.send_message_dict_tcp(message)

    def send_new_group(self, group_dict):
        message = {"message_type": "new_group_dict",
                   "group_dict": json.dumps(group_dict)
                   }
        self.send_message_dict_tcp(message)

    def update_group(self, group_dict):
        message = {"message_type": "update_group_dict",
                   "group_dict": json.dumps(group_dict)
                   }
        self.send_message_dict_tcp(message)

    def send_friends_list(self, friends_list):
        json_friends_list = json.dumps(friends_list)
        message = {"message_type": "friends_list",
                   "friends_list": json_friends_list
                   }
        self.send_message_dict_tcp(message)

    def playlist_songs_list(self, songs_dicts_list):
        pickled_songs_list = pickle.dumps(songs_dicts_list)
        message = {"message_type": "playlist_songs",
                   "playlist_songs_list": pickled_songs_list
                   }
        self.send_message_dict_tcp(message)

    def send_blocked_list(self, blocked_list):
        json_blocked_list = json.dumps(blocked_list)
        message = {"message_type": "blocked_list",
                   "blocked_list": json_blocked_list
                   }
        self.send_message_dict_tcp(message)

    def send_online_users_list(self, online_users_list):
        json_online_users_list = json.dumps(online_users_list)
        message = {"message_type": "online_users_list",
                   "online_users_list": json_online_users_list
                   }
        self.send_message_dict_tcp(message)

    def send_user_groups_list(self, group_list):
        json_group_list = json.dumps(group_list)
        message = {"message_type": "groups_list",
                   "groups_list": json_group_list
                   }
        self.send_message_dict_tcp(message)

    def send_user_chats_list(self, chats_list):
        json_chats_list = json.dumps(chats_list)
        message = {"message_type": "chats_list",
                   "chats_list": json_chats_list
                   }
        self.send_message_dict_tcp(message)

    def send_user_that_calling(self, user_that_is_calling):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "calling", "user_that_called": user_that_is_calling}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_user_that_call_ended(self):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "ended"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_user_that_call_accepted(self):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "accepted"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_user_call_timeout(self):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "timeout"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_call_dict(self, call_dict):
        message = {"message_type": "call", "call_action_type": "call_dictionary",
                   "action": "dict", "dict": call_dict}
        self.send_message_dict_tcp(message)

    def send_call_list_of_dicts(self, call_dicts_list):
        json_call_dicts_list = json.dumps(call_dicts_list)
        message = {"message_type": "call", "call_action_type": "call_dictionary",
                   "action": "list_call_dicts", "list_call_dicts": json_call_dicts_list}
        self.send_message_dict_tcp(message)

    def send_profile_list_of_dicts(self, profile_dicts_list):
        message = {"message_type": "profile_dicts_list", "profile_dicts_list": profile_dicts_list}
        self.send_message_dict_tcp(message)

    def send_profile_dict_of_user(self, profile_dict, user):
        json_profile_dict = json.dumps(profile_dict)
        message = {"message_type": "updated_profile_dict", "profile_dict": json_profile_dict, "username": user}
        self.send_message_dict_tcp(message)

    def remove_call_to_user_of_id(self, call_id):
        try:
            message = {"message_type": "call", "call_action_type": "update_calls",
                       "action": "remove_id", "removed_id": call_id}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_stream_of_user_closed(self, user):
        try:
            message = {"message_type": "call", "call_action_type": "in_call_action",
                       "action": "stream_stopped", "user_that_stopped": user}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_confirm_login(self):
        try:
            message = {"message_type": "login", "login_status": "confirm"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_invalid_login(self):
        try:
            message = {"message_type": "login", "login_status": "invalid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_already_logged_in(self):
        try:
            message = {"message_type": "login", "login_status": "already_logged_in"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_2fa_on(self):
        try:
            message = {"message_type": "login", "login_status": "2fa"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_sign_up_confirm(self):
        try:
            message = {"message_type": "sign_up", "sign_up_status": "confirm"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_sign_up_invalid(self):
        try:
            message = {"message_type": "sign_up", "sign_up_status": "invalid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_sign_up_code_invalid(self):
        try:
            message = {"message_type": "sign_up", "action": "code", 'code_status': "invalid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_sign_up_code_valid(self):
        try:
            message = {"message_type": "sign_up", "action": "code", 'code_status': "valid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_all_data_received(self):
        try:
            message = {"message_type": "data", "action": "receive", 'receive_status': "done"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_security_token_to_client(self, security_token):
        try:
            message = {"message_type": "security_token", "security_token": security_token}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_security_token_valid(self):
        try:
            message = {"message_type": "security_token", "security_status": "valid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_security_token_invalid(self):
        try:
            message = {"message_type": "security_token", "security_status": "invalid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_forget_password_info_valid(self):
        try:
            message = {"message_type": "forget_password", "forget_password_status": "valid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_forget_password_info_invalid(self):
        try:
            message = {"message_type": "forget_password", "forget_password_status": "invalid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_forget_password_code_valid(self):
        try:
            message = {"message_type": "forget_password", "action": "code", "code_status": "valid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_2fa_code_valid(self):
        try:
            message = {"message_type": "2fa", "action": "code", "code_status": "valid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_2fa_code_invalid(self):
        try:
            message = {"message_type": "2fa", "action": "code", "code_status": "invalid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def send_forget_password_code_invalid(self):
        try:
            message = {"message_type": "forget_password", "action": "code", "code_status": "invalid"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

    def timeout_receive(self):
        try:
            message = {"message_type": "timeout_receive"}
            self.send_message_dict_tcp(message)
        except socket.error as e:
            print(e)

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
            self.logger.info(f"Started to communicate with client {self.client_tcp_socket_address}, with AES key {aes_key}")
            try:
                encrypted_aes_key = encrypt_with_aes(decrypted_symmetric_key, aes_key)
                self.send_bytes(symmetric_key_byte_sequence + encrypted_aes_key)
                self.aes_key = aes_key
            except Exception as e:
                print(e)
        else:
            print("Error receiving the symmetric key.")