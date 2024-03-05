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
from multiprocessing import Process


# Set up the logging configuration
logging.basicConfig(level=logging.DEBUG)  # You can adjust the logging level as needed

server = "127.0.0.1"
port = 4444
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
    while True:
        time.sleep(0.05)

        if is_client_waits_for_message(User):
            message = get_and_remove_message_for_client(User)
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
            if isinstance(message, str) and message.startswith("current_chat"):
                client_current_chat = message.split(":")[1]
                logger.info(f"{User} current chat is {client_current_chat}")
                database_func.mark_messages_as_read(User, client_current_chat)
                if client_current_chat not in database_func.get_user_chats(User):
                    database_func.add_chat_to_user(User, client_current_chat)
                    logger.info(f"added new chat to {User}")
            if isinstance(message, str) and message.startswith("update_chat_list"):
                list_dict_of_messages = database_func.get_messages(User, client_current_chat)
                n.send_messages_list(list_dict_of_messages)



vc_data_sequence = br'\vc_data'
share_screen_sequence = br'\share_screen_data'
share_camera_sequence = br'\share_camera_data'


def thread_recv_messages(n, addr, username):
    global ringing_list, online_users, current_calls_list
    User = ""
    is_logged_in = False
    logger = logging.getLogger(__name__)

    while True:
        if not is_logged_in:
            try:
                username, password, format, email, security_token = n.recv_login_info()
                if format == "login":
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
                if format == "sign up":
                    is_valid = not database_func.username_exists(username)
                    if is_valid:
                        logger.info(f"Server sent code to email for ({addr})")
                        code = random.randint(100000, 999999)
                        send_code_to_client_email(code, email, username)
                        n.sent_code_to_mail()
                        attempts_remaining = 3  # Set the maximum number of attempts
                        while attempts_remaining > 0:
                            data = n.recv_str()
                            if data.startswith("sign_up"):
                                parts = data.split(":")
                                action = parts[1]
                                if action == "verification_code":
                                    code_gotten = parts[2]
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
                                        logger.info(f"Server sent sign up Invalid to ({addr})")
                                        n.send_sign_up_code_invalid()
                                        attempts_remaining -= 1
                    else:
                        logger.info(f"Server sent Invalid to ({addr})")
                        n.send_sign_up_invalid()
                if format == "forget password":
                    is_valid = database_func.user_exists_with_email(username, email)
                    if is_valid:
                        logger.info(f"Server sent code to email for ({addr})")
                        code = random.randint(100000, 999999)
                        send_forget_password_code_to_email(code, email, username)
                        n.send_forget_password_info_valid()
                        attempts_remaining = 3  # Set the maximum number of attempts
                        while attempts_remaining > 0:
                            code_gotten = n.recv_str()
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
                                parts = data.split(":")
                                if len(parts) > 0:
                                    if parts[0] == "password":
                                        if parts[1] == "new":
                                            new_password = parts[2]
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
                if format == "security token":
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
            logger.debug(f"waiting for data...for {User}")
            data = n.recv_str()
            if data is None:
                logger.info(f"lost connection with {User}")
                Communication.user_offline(User)
                break
            if isinstance(data, str):
                if data is None:
                    logger.info(f"lost connection with {User}")
                    Communication.user_offline(User)
                    break
                elif is_string(data):
                    if data.startswith("update_profile_pic"):
                        profile_pic_encoded = data.split(":")[1]
                        if profile_pic_encoded == "None":
                            profile_pic_encoded = None
                            logger.info(f"{User} reset his profile picture")
                        database_func.update_profile_pic(User, profile_pic_encoded)
                        logger.info(f"updated client profile pic of {User}")
                        Communication.update_profiles_list_for_everyone_by_user(User)
                    if data.startswith("security_token"):
                        action = data.split(":")[1]
                        if action == "needed":
                            user_security_token = database_func.get_security_token(User)
                            n.send_security_token_to_client(user_security_token)
                            logger.info(f"Sent security token to - {User} , {user_security_token}")
                    if data.startswith("group:"):
                        parts = data.split(":")
                        if len(parts) == 3:
                            if parts[1] == "create":
                                members_list = json.loads(parts[2])
                                members_list.append(User)
                                database_func.create_group(f"{User}'s Group", User, members_list)
                                logger.info(f"{User} created a new group")
                    if data.startswith("current_chat:"):
                        parts = data.split(":")
                        current_chat = parts[1]
                        add_message_for_client(User, data)
                        time.sleep(0.1)
                        add_message_for_client(User, "update_chat_list")
                        logger.info(f"got {User} current chat")
                    if data.startswith("add_message:"):
                        message = data.split(":", 1)[1]
                        message = json.loads(message)
                        sender = message.get("sender")
                        receiver = message.get("receiver")
                        content = message.get("content")
                        message_type = message.get("type")
                        file_name = message.get("file_name")
                        database_func.add_message(sender, receiver, content, message_type, file_name)
                        if not receiver.startswith("("):
                            add_message_for_client(receiver, f"got_new_message:{sender}")
                        else: # means its a group therefore need to update message for every member of group
                            group_name, group_id = gets_group_attributes_from_format(receiver)
                            group_members = database_func.get_group_members(group_id)
                            group_members.remove(User)
                            for member in group_members:
                                add_message_for_client(member, f"got_new_message:{receiver}")
                        logger.info(f"added new message from {User} to {receiver}")
                    if data.startswith("friend_request:"):
                        num_of_parts = len(data.split(":"))
                        if num_of_parts != 2:
                            parts = data.split(":")
                            user = parts[1]
                            friend_user = parts[2]
                            if not database_func.are_friends(user, friend_user) and database_func.username_exists(friend_user) and not friend_user == user and not database_func.is_active_request(user, friend_user):
                                database_func.send_friend_request(user, friend_user)
                                logger.info(f"{user} sent friend request to {friend_user}")
                                add_message_for_client(friend_user, "friends_request:send")
                                n.send_str("friend_request:worked")
                            else:
                                if database_func.is_active_request(user, friend_user):
                                    logger.info("friend request is active")
                                    n.send_str("friend_request:active")
                                elif not database_func.username_exists(friend_user):
                                    n.send_str("friend_request:not exist")
                                else:
                                    n.send_str("friend_request:already friends")
                        else:
                            parts = data.split(":")
                            user_len = parts[1]
                            friend_request_list = database_func.get_friend_requests(User)
                            if len(friend_request_list) != int(user_len):
                                n.send_requests_list(friend_request_list)
                                logger.info(f"Sent requests list ({friend_request_list}) to user {User}")
                            else:
                                logger.info(f"sent to {User} friend_request_list is updated")
                    if data.startswith("friend_remove:"):
                        friends_to_remove = data.split(":")[1]
                        database_func.remove_friend(User, friends_to_remove)
                        if friends_to_remove in online_users:
                            add_message_for_client(friends_to_remove, "friends_list:send")
                        logger.info(f"{User} removed {friends_to_remove} as friend")
                    if data.startswith("friend_request_status:"):
                        parts = data.split(":")
                        status = parts[1]
                        accepted_or_rejected_user = parts[2]
                        if status == "accept":
                            database_func.handle_friend_request(User, accepted_or_rejected_user, True)
                            logger.info(f"{User} accepted {accepted_or_rejected_user} friend request")
                            add_message_for_client(User, "friends_request:send")
                            add_message_for_client(accepted_or_rejected_user, "friends_request:send")
                            add_message_for_client(User, "friends_list:send")
                            add_message_for_client(accepted_or_rejected_user, "friends_list:send")
                        else:
                            database_func.handle_friend_request(User, accepted_or_rejected_user, False)
                            logger.info(f"{User} rejected {accepted_or_rejected_user} friend request")
                            add_message_for_client(User, "friends_request:send")
                            add_message_for_client(accepted_or_rejected_user, "friends_request:send")
                    if data.startswith("call:"):
                        parts = data.split(":")
                        action = parts[1]
                        if action == "stream":
                            if len(parts) == 4 or len(parts) == 5:
                                stream_type = parts[2]
                                stream_action = parts[3]
                                if stream_action == "start":
                                    Communication.create_video_stream_for_user_call(User, stream_type)
                                elif stream_action == "close":
                                    Communication.close_video_stream_for_user_call(User, stream_type)
                                elif stream_action == "watch":
                                    if len(parts) == 5:
                                        streamer = parts[4]
                                        Communication.add_spectator_to_call_stream(User, streamer, stream_type)
                            elif len(parts) == 3:
                                stream_action = parts[2]
                                if stream_action == "stop_watch":
                                    Communication.remove_spectator_from_call_stream(User)
                        if action == "join":
                            if Communication.is_user_in_a_call(User):
                                Communication.remove_user_from_call(User)
                                group_id = int(parts[2])
                                Communication.add_user_to_group_call_by_id(User, group_id)
                            else:
                                group_id = int(parts[2])
                                Communication.add_user_to_group_call_by_id(User, group_id)
                        if action == "mute":
                            if parts[2] != "myself":
                                person_to_mute = parts[2]
                            else:
                                Communication.mute_or_unmute_self_user(User)
                        if action == "deafen":
                            Communication.deafen_or_undeafen_self_user(User)
                        if action == "calling":
                            if parts[2] != "stop!":
                                user_that_is_getting_called = parts[2]
                                logger.info(f"{User} calling {user_that_is_getting_called}")
                                Communication.create_ring(User, user_that_is_getting_called)
                            else:
                                Communication.cancel_ring_by_the_ringer(User)
                        if action == "accepted":
                            ringer = parts[2]
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
                        if action == "rejected":
                            rejected_caller = parts[2]
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
            elif isinstance(data, bytes):
                if data.startswith(vc_data_sequence):
                    rest_of_bytes = data[len(vc_data_sequence):]
                    vc_data = zlib.decompress(rest_of_bytes)
                    Communication.send_vc_data_to_call(vc_data, User)
                elif data.startswith(share_screen_sequence):
                    shape_bytes = data.split(b":")[-1]
                    rest_of_bytes = data[len(share_screen_sequence):len(data)-len(shape_bytes)-1]
                    share_screen_data = zlib.decompress(rest_of_bytes)
                    Communication.send_share_screen_data_to_call(share_screen_data, shape_bytes, User, "ScreenStream")
                elif data.startswith(share_camera_sequence):
                    shape_bytes = data.split(b":")[-1]
                    rest_of_bytes = data[len(share_camera_sequence):len(data)-len(shape_bytes)-1]
                    share_screen_data = zlib.decompress(rest_of_bytes)
                    Communication.send_share_screen_data_to_call(share_screen_data, shape_bytes, User, "CameraStream")



Communication = Communication()

def main():
    logger = logging.getLogger(__name__)
    try:
        s.bind((server, port))
    except socket.error as e:
        logger.critical(e)

    s.listen(20)
    logger.info("Waiting for a connection , Server started")

    while True:
        username1 = "0000"
        conn, addr = s.accept()
        logger.info(f"connect to: {addr}")
        n = server_net(conn, addr)
        threading.Thread(target=thread_recv_messages, args=(n, addr, username1)).start()
        #Process(target=thread_recv_messages, args=(n, addr, username1)).start()

if __name__ == '__main__':
    main()