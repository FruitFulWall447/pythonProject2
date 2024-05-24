import socket
import threading
from server_net import ServerNet
from email_send_code import *
from server_handling_classes import ServerHandler
import database_func
import re
import random
import json
import time
import zlib
import logging
import base64
from song_search_engine import extract_audio_bytes
import datetime

# Set up the logging configuration
logging.basicConfig(filename="example.log",
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)

# Add the StreamHandler to the root logger
logging.getLogger().addHandler(console_handler)

server = "0.0.0.0"
port = 5555
tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server_socket.bind((server, port))


def is_json_serialized(file_path):
    try:
        with open(file_path, 'r') as file:
            json.load(file)
        return True
    except json.JSONDecodeError:
        return False
    except FileNotFoundError:
        return False


def create_song_info_dict(audio_bytes, title, thumbnail_bytes, audio_duration):
    video_info = {
        "audio_bytes": audio_bytes,
        "title": title,
        "thumbnail_bytes": thumbnail_bytes,
        "audio_duration": audio_duration
    }
    return video_info


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


def handle_code_wait(n, code, logger, addr, code_type, email= None, username=None, password=None):
    attempts_remaining = 3  # Set the maximum number of attempts
    expected_message_type = None
    expected_action = None
    if code_type == "2fa":
        expected_message_type = "login"
        expected_action = "2fa"
    elif code_type == "sign_up":
        expected_message_type = "sign_up"
        expected_action = "verification_code"
    elif code_type == "forget password":
        expected_message_type = "sign_up"
        expected_action = "verification_code"
    while attempts_remaining > 0:
        code_gotten_data = n.recv_str()
        message_type = code_gotten_data.get("message_type")
        if message_type == expected_message_type:
            action = code_gotten_data.get("action")
            if action == expected_action:
                code_gotten = code_gotten_data.get("code")
                logger.info(f"got {code_gotten} from ({addr})")
                if code_gotten is None:
                    logger.info(f"lost connection with ({addr})")
                    break
                code_gotten = int(code_gotten)
                logger.info(f"Server got {code_gotten} from ({addr})")
                if code_gotten == code:
                    if code_type == "2fa":
                        n.send_2fa_code_valid()
                        logger.info(f"got right 2fa code from {username}")
                        logger.info(f"Server sent Confirmed to client {username}")
                        logger.info(f"Client {username} logged in")
                        ServerHandler.user_online(username, n)
                        return True, username
                    elif code_type == "forget password":
                        logger.info(f"code gotten from {username} is correct")
                        n.send_forget_password_code_valid()
                        data = n.recv_str()
                        message_type = data.get("message_type")
                        if message_type == "password":
                            action = data.get("action")
                            if action == "new_password":
                                new_password = data.get("new_password")
                                database_func.change_password(username, new_password)
                                send_changed_password_to_email(email, username)
                                logger.info(f"{username} changed password")
                                break
                    elif code_type == "sign_up":
                        send_confirmation_to_client_email(email, username)
                        logger.info(f"Server sent Confirmed to ({addr})")
                        n.send_sign_up_code_valid()
                        database_func.insert_user(username, password, email)
                        logger.info(f"inserted: {username} to data base")
                        break
                elif code_gotten == "Exit":
                    logger.info(f"({addr}) existed code menu")
                    break
                else:
                    logger.info(f"Server sent Invalid to ({addr}) because code was incorrect")
                    n.send_forget_password_code_invalid()
                    attempts_remaining -= 1


def thread_recv_messages(n, addr):
    User = ""
    is_logged_in = False
    logger = logging.getLogger(__name__)
    while True:
        if not is_logged_in:
            try:
                data = n.recv_str()
                if data is None:
                    break
                message_type = data.get("message_type")
                if message_type == "login":
                    username = data.get("username")
                    password = data.get("password")
                    is_valid = database_func.login(username, password)
                    if is_valid:
                        user_settings = database_func.get_user_settings(username)
                        if user_settings:
                            is_2fa_for_user = user_settings.get("two_factor_auth")
                        else:
                            is_2fa_for_user = False
                        if username not in ServerHandler.online_users:
                            if not is_2fa_for_user:
                                n.send_confirm_login()
                                logger.info(f"Server sent Confirmed to client {username}")
                                logger.info(f"Client {username} logged in")
                                User = username
                                ServerHandler.user_online(User, n)
                                is_logged_in = True
                            else:
                                user_mail = database_func.get_email_by_username(username)
                                logger.info(f"{username} has 2fa On")
                                code = random.randint(100000, 999999)
                                send_login_code_to_client_email(code, user_mail, username)
                                n.send_2fa_on()
                                status, username_from_waiting = handle_code_wait(n, code, logger, addr, "2fa", user_mail, username)
                                if status:
                                    is_logged_in = True
                                    User = username_from_waiting
                                    print(1)
                                # attempts_remaining = 3  # Set the maximum number of attempts
                                # while attempts_remaining > 0:
                                #     data = n.recv_str()
                                #     message_type = data.get("message_type")
                                #     if message_type == "login":
                                #         action = data.get("action")
                                #         if action == "2fa":
                                #             code_gotten = data.get("code")
                                #             code_gotten = int(code_gotten)
                                #             if code_gotten == code:
                                #                 n.send_2fa_code_valid()
                                #                 logger.info(f"got right 2fa code from {username}")
                                #                 logger.info(f"Server sent Confirmed to client {username}")
                                #                 logger.info(f"Client {username} logged in")
                                #                 User = username
                                #                 ServerHandler.user_online(User, n)
                                #                 is_logged_in = True
                                #                 break
                                #             else:
                                #                 attempts_remaining -= 1
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
                                    code_gotten = code_gotten_data.get("code")
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
                                        message_type = data.get("message_type")
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
                        if username not in ServerHandler.online_users:
                            n.send_security_token_valid()
                            User = username
                            n.send_username_to_client(username)
                            logger.info(f"{User} logged in")
                            ServerHandler.user_online(User, n)
                            is_logged_in = True
                        else:
                            n.send_username_to_client_login_invalid(username)
                            logger.info(f"{username} already logged in from another device, cannot log in from 2 devices")
                            logger.info(f"Blocked User from logging in from 2 devices")
            except Exception as e:
                print(e)
        else:
            # logger.debug(f"waiting for data...for {User}")
            data = n.recv_str()
            if data is None:
                logger.info(f"lost connection with {User}")
                ServerHandler.user_offline(User)
                break
            message_type = data.get("message_type")
            if message_type == "connect_udp_port":
                udp_address = data.get("udp_address")
                tcp_address = data.get("tcp_address")
                if ServerHandler.server_mtu is None:
                    ServerHandler.check_max_packet_size_udp(udp_address)
                ServerHandler.create_and_add_udp_handler_object(User, udp_address, tcp_address)
            elif message_type == "logout":
                logger.info(f"logged out {User}")
                ServerHandler.user_offline(User)
                is_logged_in = False
                User = ""
                n.timeout_receive()
            elif message_type == "playlist_song_bytes_by_index":
                index = data.get("index")
                song_dict = database_func.get_song_by_index_and_owner(User, index)
                audio_bytes = song_dict.get('audio_bytes')
                title = song_dict.get('title')
                n.send_played_song_bytes(audio_bytes, title)
            elif message_type == "exit_group":
                group_to_exit_id = data.get("group_to_exit_id")
                database_func.remove_group_member(group_to_exit_id, User)
                group_name = database_func.get_group_name_by_id(group_to_exit_id)
                group_name_plus_id = f"({group_to_exit_id}){group_name}"
                database_func.remove_chat_from_user(User, group_name_plus_id)
            elif message_type == "remove_user_from_group":
                user_to_remove = data.get("user_to_remove")
                group_id = data.get("group_id")
                database_func.remove_group_member(group_id, user_to_remove)
                group_name = database_func.get_group_name_by_id(group_id)
                group_name_plus_id = f"({group_id}){group_name}"
                database_func.remove_chat_from_user(user_to_remove, group_name_plus_id)
            elif message_type == "remove_chat":
                chat_to_remove = data.get("chat_to_remove")
                database_func.remove_chat_from_user(User, chat_to_remove)
                logger.info(f"remove chat {chat_to_remove} for {User}")
            elif message_type == "settings_dict":
                settings_dict = data.get("settings_dict")
                database_func.update_settings_by_dict(User, settings_dict)
                logger.info(f"updated {User} settings")
            elif message_type == "current_chat":
                user_current_chat = data.get("current_chat")
                ServerHandler.update_chat_for_user(User, user_current_chat)
            elif message_type == "song_search":
                search_str = data.get("search_str")
                logger.info(f"searching for {search_str} for {User}")
                try:
                    audio_bytes, video_title, thumbnail_bytes, duration_min_sec = extract_audio_bytes(search_str)
                    info_dict = create_song_info_dict(audio_bytes, video_title, thumbnail_bytes, duration_min_sec)
                    n.send_searched_song_info(info_dict)
                except Exception as e:
                    logger.error(f"error with search engine: {e}")
            elif message_type == "remove_song":
                song_title = data.get("song_title")
                database_func.remove_song(song_title, User)
            elif message_type == "save_song":
                song_dict = data.get("song_dict")
                audio_bytes = song_dict.get("audio_bytes")
                title = song_dict.get("title")
                thumbnail_bytes = song_dict.get("thumbnail_bytes")
                audio_duration = song_dict.get("audio_duration")
                database_func.add_song(title, audio_bytes, User, audio_duration, thumbnail_bytes)
                logger.info(f"Added song {title} to {User} playlist")
            elif message_type == "more_messages":
                ServerHandler.more_messages_for_chat(User)
            elif message_type == "call":
                call_action_type = data.get("call_action_type")
                if call_action_type == "stream":
                    stream_type = data.get("stream_type")
                    stream_action = data.get("action")
                    if stream_action == "start":
                        ServerHandler.create_video_stream_for_user_call(User, stream_type)
                    if stream_action == "close":
                        ServerHandler.close_video_stream_for_user_call(User, stream_type)
                    if stream_action == "watch":
                        streamer = data.get("user_to_watch")
                        ServerHandler.add_spectator_to_call_stream(User, streamer, stream_type)
                    if stream_action == "stop_watch":
                        ServerHandler.remove_spectator_from_call_stream(User)
                if call_action_type == "in_call_action":
                    action = data.get("action")
                    if action == "join":
                        group_id = data.get("group_id")
                        if ServerHandler.is_user_in_a_call(User):
                            ServerHandler.remove_user_from_call(User)
                            ServerHandler.add_user_to_group_call_by_id(User, group_id)
                        else:
                            ServerHandler.add_user_to_group_call_by_id(User, group_id)
                    if action == "mute_myself":
                        ServerHandler.mute_or_unmute_self_user(User)
                    if action == "deafen_myself":
                        ServerHandler.deafen_or_undeafen_self_user(User)
                    if action == "calling":
                        user_that_is_getting_called = data.get("calling_to")
                        logger.info(f"{User} calling {user_that_is_getting_called}")
                        ServerHandler.create_ring(User, user_that_is_getting_called)
                    if action == "accepted_call":
                        ringer = data.get("accepted_caller")
                        logger.info(f"{User} accepted {ringer} call")
                        # if a call already created no need to create just need to append the user to the call
                        if ringer.startswith("("):
                            group_id, group_name, caller = parse_group_caller_format(ringer)
                            if ServerHandler.is_group_call_exist_by_id(group_id):
                                ServerHandler.add_user_to_group_call_by_id(User, group_id)
                            else:
                                ServerHandler.create_call_and_add(group_id, [User, caller])
                        else:
                            ServerHandler.create_call_and_add(None, [User, ringer])
                            ServerHandler.accept_ring_by_ringer(ringer, User)
                    if action == "rejected_call":
                        rejected_caller = data.get("rejected_caller")
                        if rejected_caller.startswith("("):
                            group_id, group_name, caller = parse_group_caller_format(rejected_caller)
                            logger.info(f"{User} rejected {caller} Group call, Group: {group_name}")
                            ServerHandler.reject_ring_by_ringer(caller, User)
                        else:
                            rejected_caller = rejected_caller
                            logger.info(f"{User} rejected {rejected_caller} call")
                            ServerHandler.reject_ring_by_ringer(rejected_caller, User)
                    if action == "ended":
                        ServerHandler.remove_user_from_call(User)
                if call_action_type == "change_calling_status":
                    action = data.get("action")
                    if action == "stop!":
                        ServerHandler.cancel_ring_by_the_ringer(User)
            elif message_type == "add_message":
                sender = data.get("sender")
                receiver = data.get("receiver")
                content = data.get("content")
                type_of_message = data.get("type")
                file_name = data.get("file_name")
                database_func.add_message(sender, receiver, content, type_of_message, file_name)
                # fix it...
                if not receiver.startswith("("):
                    ServerHandler.update_message_for_users([receiver], data, User)
                else:
                    group_name, group_id = gets_group_attributes_from_format(receiver)
                    group_members = database_func.get_group_members(group_id)
                    group_members.remove(User)
                    ServerHandler.update_message_for_users(group_members, data, receiver)
                logger.info(f"added new message from {User} to {receiver}")
            elif message_type == "update_profile_pic":
                b64_encoded_profile_pic = data.get("b64_encoded_profile_pic")
                if b64_encoded_profile_pic == "None":
                    b64_encoded_profile_pic = None
                    logger.info(f"{User} reset his profile picture")
                database_func.update_profile_pic(User, b64_encoded_profile_pic)
                logger.info(f"updated client profile pic of {User}")
                ServerHandler.update_profiles_list_for_everyone_by_user(User, b64_encoded_profile_pic)
            elif message_type == "security_token":
                action = data.get("action")
                if action == "needed":
                    user_security_token = database_func.get_security_token(User)
                    n.send_security_token_to_client(user_security_token)
                    logger.info(f"Sent security token to - {User} , {user_security_token}")
            elif message_type == "vc_data":
                compressed_vc_data = data.get("compressed_vc_data")
                if compressed_vc_data is not None:
                    vc_data = zlib.decompress(compressed_vc_data)
                    ServerHandler.send_vc_data_to_call(vc_data, User)
            elif message_type == "share_screen_data":
                compressed_share_screen_data = data.get("compressed_share_screen_data")
                shape_of_frame = data.get("shape_of_frame")
                if compressed_share_screen_data is not None:
                    share_screen_data = zlib.decompress(compressed_share_screen_data)
                    ServerHandler.send_share_screen_data_to_call(share_screen_data, shape_of_frame, User, "ScreenStream")
            elif message_type == "share_camera_data":
                compressed_share_camera_data = data.get("compressed_share_camera_data")
                shape_of_frame = data.get("shape_of_frame")
                if compressed_share_camera_data is not None:
                    share_screen_data = zlib.decompress(compressed_share_camera_data)
                    ServerHandler.send_share_screen_data_to_call(share_screen_data, shape_of_frame, User, "CameraStream")
            elif message_type == "friend_request":
                username_for_request = data.get("username_for_request")
                user = User
                friend_user = username_for_request
                if not database_func.are_friends(user, friend_user) and database_func.username_exists(
                        friend_user) and not friend_user == user and not database_func.is_active_request(user,
                                                                                                         friend_user):
                    database_func.send_friend_request(user, friend_user)
                    logger.info(f"{user} sent friend request to {friend_user}")
                    ServerHandler.send_friend_request(friend_user)
                    n.sent_friend_request_status("worked")
                else:
                    if database_func.is_active_request(user, friend_user):
                        logger.info("friend request is active")
                        n.sent_friend_request_status("active")
                    elif not database_func.username_exists(friend_user):
                        n.sent_friend_request_status("not exist")
                    else:
                        n.sent_friend_request_status("already friends")
            elif message_type == "friend_request_status":
                status = data.get("action")
                if status == "accept":
                    accepted_or_rejected_user = data.get("accepted_user")
                    database_func.handle_friend_request(User, accepted_or_rejected_user, True)
                    logger.info(f"{User} accepted {accepted_or_rejected_user} friend request")
                    ServerHandler.send_friend_request(User)
                    ServerHandler.send_friend_request(accepted_or_rejected_user)
                    ServerHandler.send_friends_list(User)
                    ServerHandler.send_friends_list(accepted_or_rejected_user)
                else:
                    accepted_or_rejected_user = data.get("rejected_user")
                    database_func.handle_friend_request(User, accepted_or_rejected_user, False)
                    logger.info(f"{User} rejected {accepted_or_rejected_user} friend request")
                    ServerHandler.send_friend_request(User)
                    ServerHandler.send_friend_request(accepted_or_rejected_user)
            elif message_type == "friend_remove":
                friends_to_remove = data.get("username_to_remove")
                database_func.remove_friend(User, friends_to_remove)
                if friends_to_remove in ServerHandler.online_users:
                    ServerHandler.send_friends_list(friends_to_remove)
                logger.info(f"{User} removed {friends_to_remove} as friend")
            elif message_type == "block":
                user_to_block = data.get("user_to_block")
                database_func.block_user(User, user_to_block)
                logger.info(f"{User} blocked {user_to_block}")
            elif message_type == "unblock":
                user_to_unblock = data.get("user_to_unblock")
                database_func.unblock_user(User, user_to_unblock)
                logger.info(f"{User} unblocked {user_to_unblock}")
            elif message_type == "group":
                action = data.get("action")
                if action == "create":
                    members_list = json.loads(data.get("group_members_list"))
                    members_list.append(User)
                    group_chat_name, new_group_id = database_func.create_group(f"{User}'s Group", User, members_list)
                    ServerHandler.send_new_group_to_members(new_group_id)
                    n.add_new_chat(group_chat_name)
                    logger.info(f"{User} created a new group")
                elif action == "update_image":
                    group_id = data.get("group_id")
                    encoded_b64_image = data.get("encoded_b64_image")
                    image_bytes = base64.b64decode(encoded_b64_image)
                    database_func.update_group_image(int(group_id), image_bytes)
                    ServerHandler.update_group_dict_for_members(group_id)
                elif action == "add_user":
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
                    ServerHandler.update_group_dict_for_members(group_id)


ServerHandler = ServerHandler()


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
        n = ServerNet(conn, addr)
        threading.Thread(target=thread_recv_messages, args=(n, addr)).start()


def handle_udp_message(data, address):
    print(f"got message from {address} of size {len(data)}")


def listen_udp():
    ServerHandler.udp_socket = udp_server_socket
    while True:
        try:
            fragment_data, address = udp_server_socket.recvfrom(100000)
            ServerHandler.handle_udp_fragment(fragment_data, address)
        except OSError as os_err:
            print(f"OS error: {os_err}")
        except Exception as e:
            print(f"Exception: {e}")


def main():
    # database_func.create_tables_if_not_exist()
    tcp_thread = threading.Thread(target=tcp_server)
    tcp_thread.start()
    udp_thread = threading.Thread(target=listen_udp)
    udp_thread.start()


if __name__ == '__main__':
    main()