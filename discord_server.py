import socket
import threading
from discord_comms_protocol import server_net
from email_send_code import *
from server_handling_classes import Communication, Call
import database_func
import re
import random
import json
import time
import zlib
import logging
import base64
from multiprocessing import Process


# Set up the logging configuration
logging.basicConfig(level=logging.DEBUG)  # You can adjust the logging level as needed

server = "127.0.0.1"
port = 4444
tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server_socket.bind((server, port))

# ringing_list made by tuples of len = 2 the [0] in the tuple is the caller and the [1] is the one being called
ringing_list = []
# messages_to_clients_list made by tuples of len = 2 the [0] in the tuple is the receiver of the message
# [1] is the message action
messages_to_clients_dict = {}
# current_calls_list made by tuples of len = 2 that represent 2 users that are in call.
current_calls_list = []
online_users = []

# made of tuples where [0] is target and [1] is the vc_Data
list_vc_data_sending = []


def is_json_serialized(file_path):
    try:
        with open(file_path, 'r') as file:
            json.load(file)
        return True
    except json.JSONDecodeError:
        return False
    except FileNotFoundError:
        return False


def is_string(variable):
    return isinstance(variable, str)


def is_dict(variable):
    return isinstance(variable, dict)


def is_zlib_compressed(data):
    try:
        # Attempt to decompress the data using zlib
        zlib.decompress(data)
        return True
    except zlib.error:
        # If an error occurs during decompression, it's not zlib compressed
        return False


def is_client_waits_for_message(client):
    global messages_to_clients_dict
    # Use the 'in' operator to check if the client is in the dictionary keys
    return client in messages_to_clients_dict


def add_message_for_client(client, message):
    global messages_to_clients_dict
    if client in Communication.online_users:
        messages_to_clients_dict[client] = message


def get_and_remove_message_for_client(client):
    global messages_to_clients_dict
    # Use the pop method to retrieve and remove the message for the client
    # If the client is not found, return None
    return messages_to_clients_dict.pop(client, None)


def gets_group_attributes_from_format(group_format):
    parts = group_format.split(")")
    id = parts[0][1]
    name = parts[1]
    return name, id


def parse_group_caller_format(input_format):
    # Define a regular expression pattern to capture the information
    pattern = re.compile(r'\((\d+)\)([^()]+)\(([^()]+)\)')

    # Use the pattern to match the input_format
    match = pattern.match(input_format)

    if match:
        # Extract the matched groups
        group_id = int(match.group(1))
        group_name = match.group(2).strip()
        group_caller = match.group(3).strip()

        return group_id, group_name, group_caller
    else:
        # Return None if no match is found
        return None


def threaded_logged_in_client(n, User):
    global list_vc_data_sending
    flag_is_call_sent = False
    client_current_chat = ""
    logger = logging.getLogger(__name__)
    numbers_of_starter_message = 20
    messages_list_max_index = numbers_of_starter_message
    while True:
        time.sleep(0.05)

        if is_client_waits_for_message(User):
            message = get_and_remove_message_for_client(User)
            if isinstance(message, dict):
                message_type = message.get("message_type")
                if message_type == "current_chat":
                    client_current_chat = message.get("current_chat")
                    logger.info(f"{User} current chat is {client_current_chat}")
                    database_func.mark_messages_as_read(User, client_current_chat)
                    if client_current_chat not in database_func.get_user_chats(User):
                        database_func.add_chat_to_user(User, client_current_chat)
                        n.add_new_chat(client_current_chat)
                        logger.info(f"added new chat to {User}")
                    all_chat_messages = database_func.get_messages(User, client_current_chat)
                    if len(all_chat_messages) < numbers_of_starter_message:
                        messages_list_max_index = len(all_chat_messages)
                    else:
                         messages_list_max_index = numbers_of_starter_message
                    list_dict_of_messages = database_func.get_last_amount_of_messages(User, client_current_chat, 0
                                                                                      , messages_list_max_index)
                    n.send_messages_list(list_dict_of_messages)
                if message_type == "more_messages":
                    list_dict_of_messages = database_func.get_last_amount_of_messages(User, client_current_chat,
                            messages_list_max_index+1, messages_list_max_index+6)
                    messages_list_max_index += 6
                    if len(list_dict_of_messages) > 0:
                        n.send_addition_messages_list(list_dict_of_messages)
            if isinstance(message, list):
                logger.info(f"Sent online users list to {User}")
                friends_list = database_func.get_user_friends(User)
                online_list = message
                message = list(set(friends_list) & set(online_list))
                n.send_online_users_list(message)
            if message == "friends_request:send":
                friend_request_list = database_func.get_friend_requests(User)
                n.send_requests_list(friend_request_list)
                print(f"Sent requests list ({friend_request_list}) to user {User}")
            if message == "friends_list:send":
                friends_list = database_func.get_user_friends(User)
                n.send_friends_list(friends_list)
                logger.info(f"Sent friend list ({friends_list}) to user {User}")
            if isinstance(message, str) and message.startswith("got_new_message:"):
                parts = message.split(":")
                sender = parts[1]
                if sender == client_current_chat:
                    list_messages = database_func.get_messages(User, client_current_chat)
                    n.send_messages_list(list_messages)
                else:
                    n.send_str("new_message")
                    logger.info(f"{User} got a new message")
            if isinstance(message, str) and message.startswith("update_chat_list"):
                list_dict_of_messages = database_func.get_messages(User, client_current_chat)
                n.send_messages_list(list_dict_of_messages)



vc_data_sequence = br'\vc_data'
share_screen_sequence = br'\share_screen_data'
share_camera_sequence = br'\share_camera_data'


def thread_recv_messages(n, addr):
    global ringing_list, online_users, current_calls_list
    User = ""
    is_logged_in = False
    logger = logging.getLogger(__name__)

    while True:
        if not is_logged_in:
            try:
                data = n.recv_str()
                message_type = data.get("message_type")
                if message_type == "login":
                    username = data.get("username")
                    password = data.get("password")
                    is_valid = database_func.login(username, password)
                    if is_valid:
                        if not username in Communication.online_users:
                            n.send_confirm_login()
                            logger.info(f"Server sent Confirmed to client {username}")
                            logger.info(f"Client {username} logged in")
                            User = username
                            Communication.user_online(User, n)
                            is_logged_in = True
                            threading.Thread(target=threaded_logged_in_client, args=(n, User)).start()
                        else:
                            n.send_already_logged_in()
                            logger.info(f"{username} already logged in from another device, cannot log in from 2 devices")
                    else:
                        logger.info(f"Server sent Invalid to address ({addr})")
                        n.send_invalid_login()
                if message_type == "sign_up":
                    username = data.get("username")
                    password = data.get("password")
                    email = data.get("email")
                    is_valid = not database_func.username_exists(username)
                    if is_valid:
                        logger.info(f"Server sent code to email for ({addr})")
                        code = random.randint(100000, 999999)
                        send_sing_up_code_to_client_email(code, email, username)
                        n.sent_code_to_mail()
                        attempts_remaining = 3  # Set the maximum number of attempts
                        while attempts_remaining > 0:
                            data = n.recv_str()
                            message_type = data.get("message_type")
                            if message_type == "sign_up":
                                action = data.get("action")
                                if action == "verification_code":
                                    code_gotten = data.get("code")
                                    if code_gotten is None:
                                        logger.info(f"lost connection with ({addr})")
                                        break
                                    code_gotten = int(code_gotten)
                                    logger.info(f"Server got {code_gotten} from ({addr})")
                                    if code_gotten == code:
                                        send_confirmation_to_client_email(email, username)
                                        logger.info(f"Server sent Confirmed to ({addr})")
                                        n.send_sign_up_code_valid()
                                        database_func.insert_user(username, password, email)
                                        logger.info(f"inserted: {username} to data base")
                                        break
                                    elif code_gotten == "sign_up:cancel":
                                        logger.info(f"({addr}) existed code menu")
                                        break
                                    else:
                                        logger.info(f"Server sent sign_up Invalid to ({addr})")
                                        n.send_sign_up_code_invalid()
                                        attempts_remaining -= 1
                    else:
                        logger.info(f"Server sent Invalid to ({addr})")
                        n.send_sign_up_invalid()
                if message_type == "forget password":
                    username = data.get("username")
                    email = data.get("email")
                    is_valid = database_func.user_exists_with_email(username, email)
                    if is_valid:
                        logger.info(f"Server sent code to email for ({addr})")
                        code = random.randint(100000, 999999)
                        send_forget_password_code_to_email(code, email, username)
                        n.send_forget_password_info_valid()
                        attempts_remaining = 3  # Set the maximum number of attempts
                        while attempts_remaining > 0:
                            code_gotten_data = n.recv_str()
                            message_type = code_gotten_data.get("message_type")
                            if message_type == "sign_up":
                                action = code_gotten_data.get("action")
                                if action == "verification_code":
                                    code_gotten_data = code_gotten_data.get("code")
                                    logger.info(f"got {code_gotten} from ({addr})")
                                    if code_gotten is None:
                                        logger.info(f"lost connection with ({addr})")
                                        break
                                    code_gotten = int(code_gotten)
                                    logger.info(f"Server got {code_gotten} from ({addr})")
                                    if code_gotten == code:
                                        logger.info(f"code gotten from {username} is correct")
                                        n.send_forget_password_code_valid()
                                        data = n.recv_str()
                                        message_type = code_gotten_data.get("message_type")
                                        if message_type == "password":
                                            action = data.get("action")
                                            if action == "new_password":
                                                new_password = data.get("new_password")
                                                database_func.change_password(username, new_password)
                                                send_changed_password_to_email(email, username)
                                                logger.info(f"{username} changed password")
                                                break
                                    elif code_gotten == "Exit":
                                        logger.info(f"({addr}) existed code menu")
                                        break
                                    else:
                                        logger.info(f"Server sent Invalid to ({addr}) because code was incorrect")
                                        n.send_forget_password_code_invalid()
                                        attempts_remaining -= 1
                    else:
                        logger.info("Server sent Invalid (Username with email don't exist")
                        n.send_forget_password_info_invalid()
                if message_type == "security_token":
                    security_token = data.get("security_token")
                    username = database_func.check_security_token(security_token)
                    if not username:
                        logger.info(f"security token from ({addr}) isn't valid")
                        n.send_security_token_invalid()
                    else:
                        if username not in online_users:
                            n.send_security_token_valid()
                            User = username
                            n.send_username_to_client(username)
                            logger.info(f"{User} logged in")
                            Communication.user_online(User, n)
                            is_logged_in = True
                            threading.Thread(target=threaded_logged_in_client, args=(n, User)).start()
                        else:
                            n.send_username_to_client_login_invalid(username)
                            logger.info(f"{username} already logged in from another device, cannot log in from 2 devices")
                            logger.info(f"Blocked User from logging in from 2 devices")

            except Exception as e:
                print(e)
        else:
            #logger.debug(f"waiting for data...for {User}")
            data = n.recv_str()
            if data is None:
                logger.info(f"lost connection with {User}")
                Communication.user_offline(User)
                break
            message_type = data.get("message_type")
            if message_type == "current_chat":
                user_current_chat = data.get("current_chat")
                add_message_for_client(User, data)
            if message_type == "more_messages":
                add_message_for_client(User, data)
            if message_type == "messages_list_index":
                messages_list_index = data.get("messages_list_index")
                add_message_for_client(User, data)
            if message_type == "call":
                call_action_type = data.get("call_action_type")
                if call_action_type == "stream":
                    stream_type = data.get("stream_type")
                    stream_action = data.get("action")
                    if stream_action == "start":
                        Communication.create_video_stream_for_user_call(User, stream_type)
                    if stream_action == "close":
                        Communication.close_video_stream_for_user_call(User, stream_type)
                    if stream_action == "watch":
                        streamer = data.get("user_to_watch")
                        Communication.add_spectator_to_call_stream(User, streamer, stream_type)
                    if stream_action == "stop_watch":
                        Communication.remove_spectator_from_call_stream(User)
                if call_action_type == "in_call_action":
                    action = data.get("action")
                    if action == "join":
                        group_id = data.get("group_id")
                        if Communication.is_user_in_a_call(User):
                            Communication.remove_user_from_call(User)
                            Communication.add_user_to_group_call_by_id(User, group_id)
                        else:
                            Communication.add_user_to_group_call_by_id(User, group_id)
                    if action == "mute_myself":
                        Communication.mute_or_unmute_self_user(User)
                    if action == "deafen_myself":
                        Communication.deafen_or_undeafen_self_user(User)
                    if action == "calling":
                        user_that_is_getting_called = data.get("calling_to")
                        logger.info(f"{User} calling {user_that_is_getting_called}")
                        Communication.create_ring(User, user_that_is_getting_called)
                    if action == "accepted_call":
                        ringer = data.get("accepted_caller")
                        logger.info(f"{User} accepted {ringer} call")
                        # if a call already created no need to create just need to append the user to the call
                        if ringer.startswith("("):
                            group_id, group_name, caller = parse_group_caller_format(ringer)
                            if Communication.is_group_call_exist_by_id(group_id):
                                Communication.add_user_to_group_call_by_id(User, group_id)
                            else:
                                Communication.create_call_and_add(group_id, [User, caller])
                        else:
                            Communication.create_call_and_add(None, [User, ringer])
                            Communication.accept_ring_by_ringer(ringer, User)
                    if action == "rejected_call":
                        rejected_caller = data.get("rejected_caller")
                        if rejected_caller.startswith("("):
                            group_id, group_name, caller = parse_group_caller_format(rejected_caller)
                            logger.info(f"{User} rejected {caller} Group call, Group: {group_name}")
                            Communication.reject_ring_by_ringer(caller, User)
                        else:
                            rejected_caller = rejected_caller
                            logger.info(f"{User} rejected {rejected_caller} call")
                            Communication.reject_ring_by_ringer(rejected_caller, User)
                    if action == "ended":
                        Communication.remove_user_from_call(User)
                if call_action_type == "change_calling_status":
                    action = data.get("action")
                    if action == "stop!":
                        Communication.cancel_ring_by_the_ringer(User)
            if message_type == "add_message":
                sender = data.get("sender")
                receiver = data.get("receiver")
                content = data.get("content")
                type_of_message = data.get("type")
                file_name = data.get("file_name")
                database_func.add_message(sender, receiver, content, type_of_message, file_name)
                if not receiver.startswith("("):
                    add_message_for_client(receiver, f"got_new_message:{sender}")
                else:
                    # means its a group therefore need to update message for every member of group
                    group_name, group_id = gets_group_attributes_from_format(receiver)
                    group_members = database_func.get_group_members(group_id)
                    group_members.remove(User)
                    for member in group_members:
                        add_message_for_client(member, f"got_new_message:{receiver}")
                logger.info(f"added new message from {User} to {receiver}")
            if message_type == "update_profile_pic":
                b64_encoded_profile_pic = data.get("b64_encoded_profile_pic")
                if b64_encoded_profile_pic == "None":
                    b64_encoded_profile_pic = None
                    logger.info(f"{User} reset his profile picture")
                database_func.update_profile_pic(User, b64_encoded_profile_pic)
                logger.info(f"updated client profile pic of {User}")
                Communication.update_profiles_list_for_everyone_by_user(User, b64_encoded_profile_pic)
            if message_type == "security_token":
                action = data.get("action")
                if action == "needed":
                    user_security_token = database_func.get_security_token(User)
                    n.send_security_token_to_client(user_security_token)
                    logger.info(f"Sent security token to - {User} , {user_security_token}")
            if message_type == "vc_data":
                compressed_vc_data = data.get("compressed_vc_data")
                if compressed_vc_data is not None:
                    vc_data = zlib.decompress(compressed_vc_data)
                    Communication.send_vc_data_to_call(vc_data, User)
            if message_type == "share_screen_data":
                compressed_share_screen_data = data.get("compressed_share_screen_data")
                shape_of_frame = data.get("shape_of_frame")
                if compressed_share_screen_data is not None:
                    share_screen_data = zlib.decompress(compressed_share_screen_data)
                    Communication.send_share_screen_data_to_call(share_screen_data, shape_of_frame, User, "ScreenStream")
            if message_type == "share_camera_data":
                compressed_share_camera_data = data.get("compressed_share_camera_data")
                shape_of_frame = data.get("shape_of_frame")
                if compressed_share_camera_data is not None:
                    share_screen_data = zlib.decompress(compressed_share_camera_data)
                    Communication.send_share_screen_data_to_call(share_screen_data, shape_of_frame, User, "CameraStream")
            if message_type == "friend_request":
                username_for_request = data.get("username_for_request")
                user = User
                friend_user = username_for_request
                if not database_func.are_friends(user, friend_user) and database_func.username_exists(
                        friend_user) and not friend_user == user and not database_func.is_active_request(user,
                                                                                                         friend_user):
                    database_func.send_friend_request(user, friend_user)
                    logger.info(f"{user} sent friend request to {friend_user}")
                    add_message_for_client(friend_user, "friends_request:send")
                    n.sent_friend_request_status("worked")
                else:
                    if database_func.is_active_request(user, friend_user):
                        logger.info("friend request is active")
                        n.sent_friend_request_status("active")
                    elif not database_func.username_exists(friend_user):
                        n.sent_friend_request_status("not exist")
                    else:
                        n.sent_friend_request_status("already friends")
            if message_type == "friend_request_status":
                status = data.get("action")
                if status == "accept":
                    accepted_or_rejected_user = data.get("accepted_user")
                    database_func.handle_friend_request(User, accepted_or_rejected_user, True)
                    logger.info(f"{User} accepted {accepted_or_rejected_user} friend request")
                    add_message_for_client(User, "friends_request:send")
                    add_message_for_client(accepted_or_rejected_user, "friends_request:send")
                    add_message_for_client(User, "friends_list:send")
                    add_message_for_client(accepted_or_rejected_user, "friends_list:send")
                else:
                    accepted_or_rejected_user = data.get("rejected_user")
                    database_func.handle_friend_request(User, accepted_or_rejected_user, False)
                    logger.info(f"{User} rejected {accepted_or_rejected_user} friend request")
                    add_message_for_client(User, "friends_request:send")
                    add_message_for_client(accepted_or_rejected_user, "friends_request:send")
            if message_type == "friend_remove":
                friends_to_remove = data.get("username_to_remove")
                database_func.remove_friend(User, friends_to_remove)
                if friends_to_remove in online_users:
                    add_message_for_client(friends_to_remove, "friends_list:send")
                logger.info(f"{User} removed {friends_to_remove} as friend")
            if message_type == "block":
                user_to_block = data.get("user_to_block")
                database_func.block_user(User, user_to_block)
                logger.info(f"{User} blocked {user_to_block}")
            if message_type == "unblock":
                user_to_unblock = data.get("user_to_unblock")
                database_func.unblock_user(User, user_to_unblock)
                logger.info(f"{User} unblocked {user_to_unblock}")
            if message_type == "group":
                action = data.get("action")
                if action == "create":
                    members_list = json.loads(data.get("group_members_list"))
                    members_list.append(User)
                    group_chat_name, new_group_id = database_func.create_group(f"{User}'s Group", User, members_list)
                    Communication.send_new_group_to_members(new_group_id)
                    n.add_new_chat(group_chat_name)
                    logger.info(f"{User} created a new group")
                if action == "update_image":
                    group_id = data.get("group_id")
                    encoded_b64_image = data.get("encoded_b64_image")
                    image_bytes = base64.b64decode(encoded_b64_image)
                    database_func.update_group_image(int(group_id), image_bytes)
                    Communication.update_group_dict_for_members(group_id)
                    logger.info(f"Update group image of id: {group_id} was updated by {User}")
                if action == "add_user":
                    group_id = data.get("group_id")
                    users_to_add = json.loads(data.get("users_to_add"))
                    group_dict = database_func.get_group_by_id(group_id)
                    group_manager = group_dict.get("group_manager")
                    if group_manager == User:
                        for user in users_to_add:
                            database_func.append_group_member(group_id, user)
                        logger.info(f"Added {users_to_add} to group of id {group_id} by {User}")
                    else:
                        logger.critical(f"{User} tried to add user to group where he has no permissions")

Communication = Communication()


def tcp_server():
    logger = logging.getLogger(__name__)
    try:
       tcp_server_socket.bind((server, port))
    except socket.error as e:
        logger.critical(e)

    tcp_server_socket.listen(20)
    logger.info("Waiting for a connection , Server started")

    while True:
        conn, addr = tcp_server_socket.accept()
        logger.info(f"connect to: {addr}")
        n = server_net(conn, addr)
        threading.Thread(target=thread_recv_messages, args=(n, addr)).start()

def handle_udp_message(data, address):
    print(f"UDP message from {address}: {data.decode()}")


def listen_udp():
    Communication.udp_socket = udp_server_socket
    while True:
        try:
            len_data, address = udp_server_socket.recvfrom(1024)
            data, address = udp_server_socket.recvfrom(1024)
            threading.Thread(target=handle_udp_message, args=(data, address)).start()
        except OSError as os_err:
            print(f"OS error: {os_err}")
        except Exception as e:
            print(f"Exception: {e}")

def main():
    tcp_thread = threading.Thread(target=tcp_server)
    tcp_thread.start()
    udp_thread = threading.Thread(target=listen_udp)
    udp_thread.start()

if __name__ == '__main__':
    main()