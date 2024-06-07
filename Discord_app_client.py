import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QIntValidator, QIcon, QImage
from PyQt5.QtCore import QSize, QPoint, QTimer, QMetaObject, pyqtSignal, \
    QSettings, Qt, QUrl, QTime
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from client_net import ClientNet
from social_page_widgets import FriendsBox
from settings_page_widgets import SettingsBox
from messages_page_widgets import ChatBox, play_mp3_from_bytes, make_q_object_clear
from chat_file import VideoPlayer, PlaylistWidget, get_camera_names, \
    make_circular_image, find_output_device_index, find_input_device_index, \
    get_default_output_device_name, get_default_input_device_name
import pyaudio
import random
import json
import threading
import time
import zlib
import base64
import datetime
import pickle
import cv2
import numpy as np
import pyautogui
import re
from PIL import ImageGrab
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy

email_providers = ["gmail", "outlook", "yahoo", "aol", "protonmail", "zoho", "mail", "fastmail", "gmx", "yandex",
                   "mail.ru",
                   "tutanota", "icloud", "rackspace", "mailchimp"]

CAMERA_FPS = 60
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 4096
p = pyaudio.PyAudio()
SCREEN_FPS = 30


def is_valid_password(password):
    # Check if the password is at least 8 characters long
    if len(password) < 8:
        return False

    # Check if the password contains both letters and numbers
    contains_letter = any(char.isalpha() for char in password)
    contains_digit = any(char.isdigit() for char in password)

    if not (contains_letter and contains_digit):
        return False

    # Check if the password contains only letters, numbers, and special characters
    if not re.match(r'^[A-Za-z0-9!@#$%^&*(),.?":{}|<>]+$', password):
        return False

    return True


def too_many_request(status):
    try:
        SlowDown(status)
    except Exception as e:
        print(e)


def is_valid_username(username):
    # Check if the username is non-empty
    if len(username) == 0 or len(username) > 15:
        return False

    # Check if the username contains at least one letter
    contains_letter = any(char.isalpha() for char in username)
    if not contains_letter:
        return False

    # Check if the username contains only letters, numbers, and allowed special characters
    allowed_characters = re.compile(r'^[A-Za-z0-9!@#$%^&*(),.?":{}|<>]+$')
    if not allowed_characters.match(username):
        return False

    return True


def find_difference(list1, list2):
    return list(set(list1) - set(list2))


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


def duration_to_milliseconds(duration_str):
    # Split the duration string into minutes and seconds
    minutes, seconds = map(int, duration_str.split(':'))

    # Calculate the total duration in milliseconds
    total_duration_ms = (minutes * 60 + seconds) * 1000

    return total_duration_ms


def save_token(token):
    delete_saved_token()
    settings = QSettings("Connectify_App", "Connectify")
    settings.setValue("saved_security_token", token)


def are_token_saved():
    settings = QSettings("Connectify_App", "Connectify")
    return settings.value("saved_security_token") is not None


def get_saved_token():
    settings = QSettings("Connectify_App", "Connectify")
    token = settings.value("saved_security_token")
    return token


def delete_saved_token():
    settings = QSettings("Connectify_App", "Connectify")
    settings.remove("saved_security_token")


def is_email_provider_in_list(email):
    global email_providers
    for i in email_providers:
        if i in email:
            return True
    return False


def create_message_dict(content, sender_id, timestamp, message_type, file_name):
    message_dict = {
        "content": content,
        "sender_id": sender_id,
        "timestamp": str(timestamp),
        "message_type": message_type,
        "file_name": file_name
    }
    return message_dict


def is_email_valid(email):
    email = email.lower()
    if not is_email_provider_in_list(email) or "." not in email:
        return False
    if " " in email:
        return False
    elif '@' not in email:
        return False
    elif len(email) < 4:
        return False
    parts = email.split('@')
    if len(parts) < 2 or parts[1] == "":
        return False
    return True


def is_string(variable):
    return isinstance(variable, str)


def audio_data_list_set_volume(datalist, volume):
    """ Change value of list of audio chunks """
    sound_level = volume / 100.0

    modified_datalist = []
    for chunk_bytes in datalist:
        # Convert bytes to NumPy array of int16
        chunk_array = np.frombuffer(chunk_bytes, dtype=np.int16)

        # Scale audio data to adjust volume
        scaled_chunk = (chunk_array * sound_level).astype(np.int16)

        # Convert back to bytes and append to modified_datalist
        modified_datalist.append(scaled_chunk.tobytes())

    return modified_datalist


def set_camera_properties(cap):
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set frame width to 1280 pixels
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set frame height to 720 pixels
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus
    cap.set(cv2.CAP_PROP_FOCUS, 0)  # Set focus to minimum (if supported)
    cap.set(cv2.CAP_PROP_ZOOM, 1)  # Set zoom to minimum (if supported)
    cap.set(cv2.CAP_PROP_EXPOSURE, -7)  # Set exposure to minimum (if supported)


class SplashScreen(QWidget):
    stop_loading_signal = pyqtSignal()

    def __init__(self, page_controller_object):
        super().__init__()
        self.page_controller_object = page_controller_object
        if self.page_controller_object.screen_width == 0 and self.page_controller_object.screen_height == 0:
            screen = QDesktopWidget().screenGeometry()
            self.page_controller_object.screen_height = screen.height()
            self.page_controller_object.screen_width = screen.width()
        self.init_ui()

    def init_ui(self):
        # Set window properties
        self.stop_loading_signal.connect(self.close_page_open_main_page)
        self.setWindowTitle('Splash Screen')
        self.setStyleSheet("""
            QWidget {
                background-color: #141c4b;  /* Set your desired background color */
            }
            QLabel {
                color: white;
                font-size: 18px;  /* Set your desired font size */
            }
        """)
        # Create logo label
        logo_label = QLabel(self)
        logo_label.setPixmap(
            QPixmap('discord_app_assets/connectify_icon.png'))  # Replace with the actual path to your PNG file
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.move(1690 // 2, 300)

        # Create loading label
        loading_label = QLabel('Loading...', self)
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setObjectName('loading_label')
        loading_label.move(1690 // 2 + 55, 460)

        # Set up dot counter
        self.dot_count = 0

        # Create timer to update loading dots
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.update_loading_dots)

        # Set up elapsed time variable
        self.elapsed_time = 0
        self.start_timer()

        # Show the splash screen
        self.show()

    def start_timer(self):
        self.loading_timer.start(400)  # Update every 500 milliseconds

    def close_page_open_main_page(self):
        try:
            self.page_controller_object.change_to_main_page()
            self.page_controller_object.is_logged_in = True
            self.close()
        except Exception as e:
            print(e)

    def update_loading_dots(self):
        n = self.page_controller_object.n
        wait_time_sec = 5
        self.dot_count = (self.dot_count + 1) % 5
        loading_label = self.findChild(QLabel, 'loading_label')
        loading_label.setText('Loading' + '.' * self.dot_count)
        loading_label.adjustSize()

        # Increment elapsed time
        self.elapsed_time += 500  # Timer interval is 500 milliseconds

        if self.elapsed_time >= wait_time_sec * 1000:  # 5 seconds
            # Transition to the login page after 5 seconds
            if self.page_controller_object.main_page.username == "":
                if not are_token_saved():
                    self.loading_timer.stop()
                    self.page_controller_object.change_to_login_page()
                    self.close()
                else:
                    security_token = get_saved_token()
                    n.send_security_token(security_token)
                    data = n.recv_str()
                    message_type = data.get("message_type")
                    if message_type == "security_token":
                        server_answer = data.get("security_status")
                        if server_answer == "valid":
                            data = n.recv_str()
                            message_type = data.get("message_type")
                            if message_type == "login_action":
                                username, action_state = data.get("username"), data.get("login_status")
                                if action_state is True:
                                    self.loading_timer.stop()
                                    print("logged in successfully")
                                    try:
                                        self.page_controller_object.change_to_main_page()
                                        self.page_controller_object.is_logged_in = True
                                        self.page_controller_object.start_receive_thread_after_login()
                                        self.close()
                                    except Exception as e:
                                        print(e)
                                elif action_state == "2fa":
                                    self.page_controller_object.login_page.username_entry.setText(username)
                                    self.page_controller_object.is_waiting_for_2fa_code = True
                                    self.page_controller_object.main_page.username = username
                                    self.page_controller_object.change_to_verification_code_page()
                                    self.close()
                                else:
                                    print("username already logged in")
                        elif server_answer == "invalid":
                            print("security token isn't valid")
                            self.loading_timer.stop()
                            self.page_controller_object.change_to_login_page()
                            self.close()


class MainPage(QWidget):  # main page doesnt know when chat is changed...
    updated_chat_signal = pyqtSignal()
    too_many_request_signal = pyqtSignal(str)
    update_chat_page_without_messages_signal = pyqtSignal()
    updated_social_page_signal = pyqtSignal()
    quit_application_signal = pyqtSignal()
    getting_call_signal = pyqtSignal()
    stop_sound_signal = pyqtSignal()
    initiating_call_signal = pyqtSignal()
    reset_call_var_signal = pyqtSignal()
    new_message_play_audio_signal = pyqtSignal()
    disconnect_signal = pyqtSignal()
    stop_watching_stream_signal = pyqtSignal()
    updated_settings_signal = pyqtSignal()
    caching_circular_images_of_users_signal = pyqtSignal()
    caching_circular_images_of_groups_signal = pyqtSignal()
    updating_profile_dict_signal = pyqtSignal(str, dict)
    update_group_lists_by_group = pyqtSignal(dict)
    insert_messages_into_message_box_signal = pyqtSignal(list)
    insert_new_message_in_chat_signal = pyqtSignal(dict)
    scroll_back_to_index_before_update_signal = pyqtSignal(int)
    insert_search_result_signal = pyqtSignal(dict, bool)
    update_settings_from_dict_signal = pyqtSignal(dict)
    update_message_box_signal = pyqtSignal()
    close_call_threads_signal = pyqtSignal()
    start_call_threads_signal = pyqtSignal()
    insert_playlist_to_table_signal = pyqtSignal()
    lost_connection_with_server_signal = pyqtSignal()

    def __init__(self, Network, page_controller_object):
        super().__init__()
        self.page_controller_object = page_controller_object
        self.vc_data_list = []
        self.muted_users = []

        self.vc_thread_flag = False
        self.send_vc_data_thread = threading.Thread(target=self.thread_send_voice_chat_data, args=())

        self.vc_play_flag = False
        self.audio_data_lock = threading.Lock()
        self.play_vc_data_thread = threading.Thread(target=self.thread_play_vc_data, args=())

        self.vc_data_fragments_list = []
        self.share_screen_data_fragments_list = []
        self.share_camera_data_fragments_list = []
        self.listen_udp = True
        self.listen_udp_thread = threading.Thread(target=self.listen_udp_socket_thread, args=())

        self.is_watching_screen = False
        self.watching_user = ""
        self.watching_type = None

        self.is_screen_shared = False
        self.send_share_screen_thread = threading.Thread(target=self.thread_send_share_screen_data, args=())

        self.is_camera_shared = False
        self.send_camera_data_thread = threading.Thread(target=self.thread_send_share_camera_data, args=())

        self.regular_profile_image_path = "discord_app_assets/regular_profile.png"

        self.blueish_background_color = "#141c4b"
        self.blackish_background_color = "#000000"
        self.reddish_background_color = "#5c1114"
        self.grayish_background_color = "#363131"
        self.special_design_color = "#2b2d31"

        self.blueish_style_hover_color = "#2980b9"
        self.blackish_style_hover_color = "#FFFFFF"
        self.reddish_style_hover_color = "#7d1d21"
        self.grayish_style_hover_color = "#5c4a4b"
        self.special_design_hover_color = "#36373d"

        self.hex_hover_colors = [self.reddish_style_hover_color, self.blueish_style_hover_color,
                                 self.blackish_style_hover_color, self.grayish_style_hover_color,
                                 self.special_design_hover_color]

        self.hex_colors = [self.reddish_background_color, self.blueish_background_color, self.blackish_background_color,
                           self.grayish_background_color, self.special_design_color]
        self.color_design_options = ["Red", "Blue", "Black and White", "Gray", "Connectify Special"]
        self.color_design_mapping = {
            self.color_design_options[0]: self.hex_colors[0],
            self.color_design_options[1]: self.hex_colors[1],
            self.color_design_options[2]: self.hex_colors[2],
            self.color_design_options[3]: self.hex_colors[3],
            self.color_design_options[4]: self.hex_colors[4]
        }

        self.style_color_hover_mapping = {
            self.color_design_options[0]: self.hex_hover_colors[0],
            self.color_design_options[1]: self.hex_hover_colors[1],
            self.color_design_options[2]: self.hex_hover_colors[2],
            self.color_design_options[3]: self.hex_hover_colors[3],
            self.color_design_options[4]: self.hex_hover_colors[4]
        }
        self.special_keys_mapping = {
            Qt.Key_Return: "Return",
            Qt.Key_Enter: "Enter",
            Qt.Key_Escape: "Escape",
            Qt.Key_Tab: "Tab",
            Qt.Key_Backspace: "Backspace",
            Qt.Key_Delete: "Delete",
            Qt.Key_Insert: "Insert",
            Qt.Key_Home: "Home",
            Qt.Key_End: "End",
            Qt.Key_PageUp: "Page Up",
            Qt.Key_PageDown: "Page Down",
            Qt.Key_Left: "Left Arrow",
            Qt.Key_Right: "Right Arrow",
            Qt.Key_Up: "Up Arrow",
            Qt.Key_Down: "Down Arrow",
            Qt.Key_F1: "F1",
            Qt.Key_F2: "F2",
            Qt.Key_F3: "F3",
            Qt.Key_F4: "F4",
            Qt.Key_F5: "F5",
            Qt.Key_F6: "F6",
            Qt.Key_F7: "F7",
            Qt.Key_F8: "F8",
            Qt.Key_F9: "F9",
            Qt.Key_F10: "F10",
            Qt.Key_F11: "F11",
            Qt.Key_F12: "F12",
            Qt.Key_Shift: "Shift",
            Qt.Key_Control: "Control",
            Qt.Key_Alt: "Alt",
            Qt.Key_Meta: "Meta/Windows",
            Qt.Key_CapsLock: "Caps Lock",
            Qt.Key_NumLock: "Num Lock",
            Qt.Key_ScrollLock: "Scroll Lock",
            # Add more key mappings as needed
        }
        self.reversed_keys_mapping = {value: key for key, value in self.special_keys_mapping.items()}


        self.standard_hover_color = "#2980b9"
        self.background_color_hex = "#141c4b"
        self.font_options = ["Ariel", "Times New Roman", "Helvetica"]

        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(90)  # Adjust the blur radius as needed
        screen = QDesktopWidget().screenGeometry()
        # Extract the screen width and height
        self.screen_width = screen.width()
        self.screen_height = screen.height()

        self.is_create_group_pressed = False
        self.is_create_group_inside_chat_pressed = False

        self.is_rename_group_pressed = False
        self.is_add_users_to_group_pressed = False

        self.current_search_song_dict = None
        self.phone_number = None
        self.email = None
        self.messages_font_size = 12

        self.volume = 50
        self.output_device_name = ""
        self.input_device_name = ""
        self.camera_index = 0
        self.font_size = 12
        self.font_text = self.font_options[0]
        self.background_color = "Blue"
        self.censor_data_from_strangers = True
        self.is_private_account = True
        self.push_to_talk_key = None
        self.two_factor_authentication = False

        self.playlist_volume = self.volume
        self.playlist_songs = []
        self.playlist_index = 0
        self.playlist_last_index = 0
        self.shuffle = False
        self.replay_song = False

        self.size_error_label = False
        self.is_chat_box_full = False
        self.is_friends_box_full = False
        self.is_last_message_on_screen = False

        self.list_messages = []
        self.is_user_have_current_chat_all_messages = False

        self.request_list = []
        self.is_in_a_call = False
        self.is_calling = False
        self.calling_to = ""
        self.in_call_with = ""
        self.is_getting_called = False
        self.getting_called_by = ""
        self.is_joining_call = False
        self.joining_to = ""
        self.call_dicts = []

        self.username = ""

        self.selected_chat = ""
        self.is_current_chat_a_group = False

        self.camera_devices_names = get_camera_names()

        self.mute = False
        self.deafen = False

        self.selected_settings = "My Account"
        self.is_push_to_talk = False
        self.is_push_to_talk_pressed = False
        self.is_editing_push_to_talk_button = False
        self.profile_pic = None
        self.list_user_profile_dicts = []
        self.circular_images_dicts_list_of_users = []
        self.circular_images_dicts_list_of_groups = []

        self.is_watching_video = False
        # the scroll widget that contain all of the messages
        self.messages_content_saver = None
        self.is_messages_need_update = True

        self.online_users_list = []
        self.friends_list = []
        # friend_box_page could be online, add friend, blocked, all, pending
        self.friends_box_page = "online"
        self.chats_list = []
        self.file_to_send = None
        self.file_name = ""
        self.chat_start_index = None
        self.Network = Network
        self.chat_box_chats_index = 0
        self.chat_box_index_y_start = 100

        self.friends_box_index = None
        self.current_friends_box_search = False

        self.chat_index = None

        self.selected_group_members = []
        self.create_group_index = 0
        self.add_users_to_group_index = 0
        self.group_max_members = 10

        self.blocked_list = []
        self.groups_list = []

        self.chat_clicked_var = True
        self.social_clicked_var = False
        self.setting_clicked = False
        self.music_clicked = False

        self.is_new_chat_clicked = True

        self.current_chat_box_search = False
        self.temp_search_list = []
        self.spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updated_chat_signal.connect(self.updated_chat)
        self.updated_social_page_signal.connect(self.updated_social_page)
        self.updated_settings_signal.connect(self.updated_settings_page)
        self.getting_call_signal.connect(self.getting_a_call)
        self.stop_sound_signal.connect(self.stop_sound)
        self.initiating_call_signal.connect(self.initiate_call)
        self.reset_call_var_signal.connect(self.reset_call_var)
        self.new_message_play_audio_signal.connect(self.new_message_play_audio)
        self.stop_watching_stream_signal.connect(self.stop_watching_video_stream)
        self.caching_circular_images_of_users_signal.connect(self.caching_circular_images_of_users)
        self.caching_circular_images_of_groups_signal.connect(self.caching_circular_images_of_groups)
        self.disconnect_signal.connect(self.page_controller_object.quit_application)
        self.updating_profile_dict_signal.connect(self.update_profile_dict_of_user)
        self.update_group_lists_by_group.connect(self.update_groups_list_by_dict)
        self.update_message_box_signal.connect(self.update_message_box)
        self.scroll_back_to_index_before_update_signal.connect(self.scroll_back_to_index_before_update)
        self.insert_messages_into_message_box_signal.connect(self.insert_messages_into_message_box)
        self.insert_new_message_in_chat_signal.connect(self.insert_new_message_in_chat)
        self.insert_search_result_signal.connect(self.insert_search_result)
        self.close_call_threads_signal.connect(self.close_call_threads)
        self.start_call_threads_signal.connect(self.start_call_threads)
        self.insert_playlist_to_table_signal.connect(self.insert_playlist_to_table)
        self.update_settings_from_dict_signal.connect(self.update_settings_from_dict)
        self.update_chat_page_without_messages_signal.connect(self.update_chat_page_without_messages)
        self.lost_connection_with_server_signal.connect(self.lost_connection_with_server)
        self.too_many_request_signal.connect(too_many_request)
        self.quit_application_signal.connect(self.page_controller_object.quit_application)

        self.sound_effect_media_player = QMediaPlayer()
        self.sound_effect_media_player.setVolume(50)

        self.mp3_message_media_player = QMediaPlayer()
        self.mp3_message_media_player.setVolume(50)

        self.calling_media_player = QMediaPlayer()
        self.calling_media_player.setVolume(50)

        self.playlist_media_player = QMediaPlayer()
        self.playlist_media_player.setVolume(50)
        self.playlist_media_player.mediaStatusChanged.connect(self.handle_playlist_song_state_change)
        self.playlist_media_player.positionChanged.connect(self.update_slider_position)

        self.ringtone_media_player = QMediaPlayer()
        self.ringtone_media_player.stateChanged.connect(self.handle_state_changed_sound_effect)
        self.ringtone_media_player.setVolume(50)

        self.ringtone = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Getting_called_sound_effect.mp3'))
        self.ding_sound_effect = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Ding Sound Effect.mp3'))
        self.new_message_audio = QMediaContent(QUrl.fromLocalFile('discord_app_assets/new_message_sound_effect.mp3'))
        self.sound_effect_media_player.setMedia(self.ringtone)
        x, y = (int(self.page_controller_object.screen_width * 0.052),
                int(self.page_controller_object.screen_height * 0.092))
        width, height = (int(self.page_controller_object.screen_width * 0.3125),
                         int(self.page_controller_object.screen_height * 0.37))

        self.setGeometry(x, y, width, height)
        self.setWindowTitle('Main Page')
        self.setStyleSheet(f'''
            QWidget {{
                background-color: {self.background_color_hex};
            }}
        ''')
        # Create an instance of ChatBox
        if self.chat_clicked_var:
            self.chat_box = ChatBox(self.list_messages, parent=self, Network=self.Network)

        buttons_layout = QHBoxLayout()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addSpacing(30)
        self.main_layout.addLayout(buttons_layout)
        self.friends_box = FriendsBox(friends_list=self.friends_list,
                                      requests_list=self.request_list, Network=self.Network, username=self.username,
                                      parent=self)
        self.friends_box.hide()
        self.settings_box = SettingsBox(parent=self)
        self.settings_box.hide()
        self.music_box = PlaylistWidget(main_page_widget=self)
        self.music_box.hide()
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.addWidget(self.chat_box)
        self.stacked_widget.addWidget(self.settings_box)  # Placeholder for the Settings page
        self.stacked_widget.addWidget(self.friends_box)
        self.stacked_widget.addWidget(self.music_box)
        self.main_layout.addWidget(self.stacked_widget)

        self.setLayout(self.main_layout)

    def close_all_threads(self):
        # turns every thread flag to False
        try:
            self.vc_thread_flag = False
            self.vc_play_flag = False
            self.listen_udp = False
            self.is_screen_shared = False
            self.is_camera_shared = False
        except Exception as e:
            print(f"error in closing threads {e}")

    def thread_play_vc_data(self):
        try:
            print("started play voice data thread....")
            output_device_name = self.output_device_name  # Get the output device name from main_page

            if output_device_name == "Default":
                def_device_name = get_default_output_device_name()
                output_device_index = find_output_device_index(def_device_name)
            else:
                output_device_index = find_output_device_index(output_device_name)

            if output_device_index is None:
                print(f"Output device '{output_device_name}' not found.")
            else:
                print(f"Output index is {output_device_name}")

            output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK,
                                   output_device_index=output_device_index)
            while self.vc_play_flag:
                try:
                    if len(self.vc_data_list) > 0:
                        self.audio_data_lock.acquire()
                        all_audio_data = [np.frombuffer(vc_data, dtype=np.int16) for vc_data, _ in self.vc_data_list]

                        mixed_data = np.vstack(all_audio_data).mean(axis=0).astype(np.int16)
                        mixed_data_audio_bytes = mixed_data.tobytes()
                        self.vc_data_list = []  # Clear the vc_data_list after processing

                        modified_audio_data_list = audio_data_list_set_volume([mixed_data_audio_bytes], volume=self.volume)
                        modified_data = b''.join(modified_audio_data_list)
                        # Play the modified audio data
                        output_stream.write(modified_data)
                        self.audio_data_lock.release()
                except Exception as e:
                    pass  # Handle the case where the queue is empty
                time.sleep(0.02)
            output_stream.stop_stream()
            output_stream.close()
        except Exception as e:
            print(f"error in thread_play_vc_data {e}")

    def thread_send_voice_chat_data(self):
        n = self.Network
        try:
            accumulated_data = []
            print("started voice chat thread....")
            input_device_name = self.input_device_name  # Get the output device name from main_page

            if input_device_name == "Default" or input_device_name == "default":
                def_device_name = get_default_input_device_name()
                input_device_index = find_input_device_index(def_device_name)
            else:
                input_device_index = find_input_device_index(input_device_name)

            if input_device_index is None:
                print(f"Input device '{input_device_name}' not found.")
            print(f"input index is {input_device_index}")

            input_stream = p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK,
                                  input_device_index=input_device_index)

            while self.vc_thread_flag:
                if not self.mute and not self.deafen:
                    if self.is_push_to_talk:
                        if self.is_push_to_talk_pressed:
                            input_data = input_stream.read(CHUNK)
                            n.send_vc_data(input_data)
                        else:
                            time.sleep(0.1)
                    else:
                        input_data = input_stream.read(CHUNK)
                        n.send_vc_data(input_data)
                else:
                    time.sleep(0.1)
            input_stream.stop_stream()
            input_stream.close()
            print("stopped voice chat thread....")
        except Exception as e:
            print(f"error in thread_send_voice_chat_data {e}")

    def thread_send_share_screen_data(self):
        time_between_frame = 1 / SCREEN_FPS
        try:
            while self.is_screen_shared:
                # Capture the screen using PyAutoGUI
                screen = ImageGrab.grab()
                # Convert the screenshot to a NumPy array
                frame = np.array(screen)
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                frame_bytes = frame_bgr.tobytes()
                # Send the frame to the server
                self.Network.send_share_screen_data(frame_bytes, frame.shape)

                time.sleep(time_between_frame)  # Adjust the sleep time based on your needs
            print("send share screen data thread closed")
        except Exception as e:
            print(f"Screen sharing error: {e}")

    def thread_send_share_camera_data(self):
        time_between_frame = 1 / CAMERA_FPS
        network = self.Network
        try:
            # Initialize the camera
            cap = cv2.VideoCapture(self.camera_index)  # Use 0 for default camera, change as needed
            set_camera_properties(cap)
            while self.is_camera_shared:
                # Capture frame-by-frame
                ret, frame = cap.read()
                if not ret:
                    print("Error: Couldn't capture frame from camera.")
                    break

                # Convert the frame to a NumPy array
                frame_np = np.asarray(frame)

                # Convert the NumPy array to bytes
                frame_bytes = frame_np.tobytes()

                # Send the frame to the server
                network.send_share_camera_data(frame_bytes, frame_np.shape)

                time.sleep(time_between_frame)  # Adjust the sleep time based on your needs
            # Release the camera and close thread
            cap.release()
            print("send share camera data thread closed")
        except Exception as e:
            print(f"Camera sharing error: {e}")

    def listen_udp_socket_thread(self):
        print("started listen_udp thread")
        network = self.Network
        while self.listen_udp:
            try:
                fragment_data, address = network.recv_udp()
                if isinstance(fragment_data, int):
                    pass
                elif fragment_data:
                    data = pickle.loads(fragment_data)
                    self.handle_udp_data(data)
            except Exception as e:
                print(f"Exception in listening to udp socket: {e}")

    def handle_udp_data(self, data):
        message_type = data.get("message_type")
        try:
            if message_type == "vc_data":
                self.handle_vc_data(data)
            elif message_type in ["share_screen_data", "share_camera_data"]:
                self.handle_stream_data(data)
        except Exception as e:
            print(f"Error in rebuilding UDP packets: {e}")

    def handle_vc_data(self, data):
        is_last = data.get("is_last")
        is_first = data.get("is_first")
        data_list = self.vc_data_fragments_list

        self.handle_data_fragment(data_list, data, is_first, is_last, "vc_data")

    def handle_stream_data(self, data):
        is_last = data.get("is_last")
        is_first = data.get("is_first")
        data_list = self.share_screen_data_fragments_list if data.get(
            "message_type") == "share_screen_data" else self.share_camera_data_fragments_list

        self.handle_data_fragment(data_list, data, is_first, is_last, "stream_data")

    def handle_data_fragment(self, data_list, data, is_first, is_last, data_type):
        if is_first:
            data_list.clear()

        data_list.append(data.get("sliced_data"))

        if is_last:
            compressed_data = b''.join(data_list)
            speaker = data.get("speaker")
            shape_of_frame = data.get("shape_of_frame") if data_type == "stream_data" else None

            decompressed_data = zlib.decompress(compressed_data)
            if data_type == "stream_data":
                decompressed_frame = np.frombuffer(decompressed_data, dtype=np.uint8).reshape(shape_of_frame)
                self.update_stream_screen_frame(decompressed_frame)
            elif data_type == "vc_data":
                self.audio_data_lock.acquire()
                if speaker not in self.muted_users:
                    self.vc_data_list.append((decompressed_data, speaker))
                self.audio_data_lock.release()

            data_list.clear()

    def exit_group(self, group_id):
        try:
            group_name = self.get_group_name_by_id(group_id)
            group_name_plus_id = f"({group_id}){group_name}"
            self.chats_list.remove(group_name_plus_id)
            if self.selected_chat == group_name_plus_id:
                self.selected_chat = ""
                self.list_messages = []
            self.Network.send_exit_group(group_id)
            self.updated_chat()
        except Exception as e:
            print(f"error in existing group {e}")

    def remove_friend(self, friend):
        self.friends_list.remove(friend)
        self.updated_social_page()
        self.update_chat_page_without_messages()
        self.Network.send_remove_friend(friend)

    def send_friend_request_for_user(self, user):
        self.Network.send_friend_request(user)

    def remove_user_from_group(self, user, group_id):
        self.Network.send_remove_user_from_group(user, group_id)

    def toggle_mute_of_user(self, user):
        if user in self.muted_users:
            print(f"unmuted {user}")
            self.muted_users.remove(user)
            self.update_chat_page_without_messages()
        else:
            print(f"muted {user}")
            self.muted_users.append(user)
            self.update_chat_page_without_messages()

    def remove_chat(self, chat_to_remove):
        try:
            self.chats_list.remove(chat_to_remove)
            self.update_chat_page_without_messages()
            self.Network.send_remove_chat(chat_to_remove)
        except Exception as e:
            print(e)

    def call_user_from_right_click(self, chat_name):
        if not self.is_in_a_call and not self.is_getting_called and not self.is_calling:
            self.chat_box.selected_chat_changed(chat_name)
            self.chat_box.call_user()

    def right_click_object_func(self, pos, parent, button, actions_list, chat_name=None, group_id=None):
        try:
            menu = QMenu(parent)
            menu.setStyleSheet(f"""
                QMenu {{
                    color: white; /* Text color of menu items */
                    border: 1px solid gray; /* Border style */
                }}
                QMenu::item:selected {{
                    background-color: {self.standard_hover_color}; /* Hover color when item is selected */
                }}
            """)
            for item1 in actions_list:
                if item1 == "remove_chat":
                    action_text = f"remove {chat_name} from chats"
                    action = menu.addAction(action_text)
                    action.triggered.connect(lambda: self.remove_chat(chat_name))
                elif item1 == "exit_group":
                    action_text = f"exit {self.get_group_name_by_id(group_id)}"
                    action = menu.addAction(action_text)
                    action.triggered.connect(lambda: self.exit_group(group_id))
                elif item1 == "remove_user_from_group":
                    action_text = f"remove {chat_name} from {self.get_group_name_by_id(group_id)}"
                    action = menu.addAction(action_text)
                    action.triggered.connect(lambda: self.remove_user_from_group(chat_name, group_id))
                elif item1 == "message_user":
                    action_text = f"message {chat_name}"
                    action = menu.addAction(action_text)
                    action.triggered.connect(lambda: self.chat_box.selected_chat_changed(chat_name))
                elif "mute" in item1:
                    action_text = item1
                    action = menu.addAction(action_text)
                    action.triggered.connect(lambda: self.toggle_mute_of_user(chat_name))
            if chat_name is not None:
                listens_to = self.get_listened_song_by_user(chat_name)
                if listens_to is not None:
                    str_for_listen = f"listen to {listens_to}"
                    action = menu.addAction(str_for_listen)
                    action.triggered.connect(lambda: self.ask_for_listen_by_name(listens_to))
                if chat_name not in self.friends_list:
                    action_text = f"add {chat_name} as friend"
                    action = menu.addAction(action_text)
                    action.triggered.connect(lambda: self.send_friend_request_for_user(chat_name))
                action_text = f"call {chat_name}"
                action = menu.addAction(action_text)
                action.triggered.connect(lambda: self.call_user_from_right_click(chat_name))
            elif chat_name is None and group_id is not None:
                group_manager = self.get_group_manager_by_group_id(group_id)
                if group_manager == self.username:
                    group_image = self.get_circular_image_bytes_by_group_id(group_id)
                    if group_image is not None:
                        action = menu.addAction("Remove group icon")
                        action.triggered.connect(lambda: self.update_group_image(None, group_id))
                full_group_name = f"({group_id}){self.get_group_name_by_id(group_id)}"
                action_text = f"call {full_group_name}"
                action = menu.addAction(action_text)
                action.triggered.connect(lambda: self.call_user_from_right_click(full_group_name))

            # Use the position of the button as the reference for menu placement
            global_pos = button.mapToGlobal(pos)

            # Show the context menu at the adjusted position
            menu.exec_(global_pos)
        except Exception as e:
            print(f"error in right click func {e}")

    def update_group_image(self, image_bytes, group_id):
        try:
            self.Network.send_new_group_image_to_server(image_bytes, group_id)
        except Exception as e:
            print(e)

    def ask_for_listen_by_name(self, title):
        self.Network.ask_for_song_by_title(title)
        print(f"asked song bytes of {title}")

    def update_slider_position(self, new_position):
        self.music_box.playlist_duration_slider.setValue(new_position)
        current_time = QTime(0, 0).addMSecs(new_position)
        current_time_str = current_time.toString("mm:ss")
        self.music_box.update_current_duration_text(current_time_str)

    def toggle_shuffle(self):
        if self.shuffle:
            self.shuffle = False
        else:
            self.shuffle = True

    def remove_song_from_playlist(self):
        try:
            index = self.playlist_index
            song_dict = self.playlist_songs[index]
            del self.playlist_songs[index]
            song_title = song_dict.get("title")
            self.Network.send_remove_song_from_playlist(song_title)
            if not self.playlist_media_player.state() == QMediaPlayer.PausedState:
                self.play_playlist_by_index()
            else:
                self.play_playlist_by_index()
                self.playlist_media_player.pause()
            print(f"deleted song of index {index}")
        except Exception as e:
            print(f"Couldn't remove song {e}")

    def music_button_clicked(self):
        if not self.music_clicked:
            self.current_friends_box_search = False
            self.current_chat_box_search = False
            self.temp_search_list = []
            self.stacked_widget.setCurrentIndex(3)
            self.chat_clicked_var = False
            self.setting_clicked = False
            self.social_clicked_var = False
            self.music_clicked = True

    def insert_search_result(self, result_dict, is_play):
        self.play_ding_sound_effect()
        self.current_search_song_dict = result_dict
        self.music_box.insert_search_data(result_dict)
        if is_play:
            self.play_search_result()

    def play_search_result(self):
        if self.current_search_song_dict is not None:
            current_search_audio_bytes = self.current_search_song_dict.get("audio_bytes")
            self.music_box.playlist_duration_slider.setMinimum(0)
            duration_str = self.current_search_song_dict.get("audio_duration")
            self.music_box.update_duration_tex(duration_str)
            total_duration = duration_to_milliseconds(duration_str)
            self.music_box.playlist_duration_slider.setMaximum(total_duration)
            play_mp3_from_bytes(current_search_audio_bytes, self.playlist_media_player)
            current_search_title = self.current_search_song_dict.get("title")
            self.Network.new_listen(current_search_title)

    def save_searched_song_to_playlist(self):
        try:
            if self.current_search_song_dict is not None:
                if not self.is_song_exist_in_playlist(self.current_search_song_dict):
                    self.Network.save_song_in_playlist(self.current_search_song_dict)
                    temp_dict = self.current_search_song_dict.copy()
                    if "audio_bytes" in temp_dict:
                        del temp_dict["audio_bytes"]
                    self.playlist_songs.append(temp_dict)
                    self.music_box.insert_new_song_to_playlist(self.current_search_song_dict)
                    print("send song to server")
                else:
                    print("song already exist in playlist")
        except Exception as e:
            print(f"error in adding song to playlist {e}")

    def is_song_exist_in_playlist(self, added_dict):
        try:
            added_dict_title = added_dict.get("title")
            for song in self.playlist_songs:
                song_title = song.get("title")
                if song_title == added_dict_title:
                    return True
            return False
        except Exception as e:
            print(f"error in finding duplicates {e}")

    def insert_playlist_to_table(self):
        self.music_box.insert_playlist_songs(self.playlist_songs)

    def pause_and_unpause_playlist(self):
        if self.playlist_media_player.state() == QMediaPlayer.PlayingState:
            self.playlist_media_player.pause()
        elif self.playlist_media_player.state() == QMediaPlayer.PausedState:
            self.playlist_media_player.play()
        elif self.playlist_media_player.state() == QMediaPlayer.StoppedState:
            # Handle the case where there is no media loaded
            print("No media loaded in the playlist media player.")
            if len(self.playlist_songs) > 0:
                self.play_playlist_by_index()

    def go_to_last_song(self):
        if not self.shuffle:
            if self.playlist_index - 1 < 0:
                pass
            else:
                self.set_new_playlist_index_and_listen(self.playlist_index - 1)
        else:
            self.set_new_playlist_index_and_listen(self.playlist_last_index)

    def go_to_next_song(self):
        try:
            len_songs_list = len(self.playlist_songs)
            if not self.shuffle:
                if self.playlist_index + 1 < len_songs_list:
                    self.set_new_playlist_index_and_listen(self.playlist_index + 1)
                else:
                    self.set_new_playlist_index_and_listen(0)
            else:
                random_index = random.randint(0, len(self.playlist_songs) - 1)
                while random_index == self.playlist_index:
                    random_index = random.randint(0, len(self.playlist_songs) - 1)
                self.set_new_playlist_index_and_listen(random_index)
        except Exception as e:
            print(f"error in going to next song {e}")

    def handle_playlist_song_state_change(self, status):
        if status == QMediaPlayer.EndOfMedia:
            if not self.replay_song:
                if not self.shuffle:
                    len_songs_list = len(self.playlist_songs)
                    if self.playlist_index + 1 < len_songs_list:
                        self.set_new_playlist_index_and_listen(self.playlist_index + 1)
                    else:
                        self.set_new_playlist_index_and_listen(0)
                else:
                    random_index = random.randint(0, len(self.playlist_songs) - 1)
                    while random_index == self.playlist_index:
                        random_index = random.randint(0, len(self.playlist_songs) - 1)
                    self.set_new_playlist_index_and_listen(random_index)
            else:
                self.set_new_playlist_index_and_listen(self.playlist_index)

    def set_new_playlist_index_and_listen(self, index):
        self.playlist_last_index = self.playlist_index
        self.playlist_index = index
        self.play_playlist_by_index()

    def play_playlist_by_index(self):
        len_songs_list = len(self.playlist_songs)
        if self.playlist_index < len_songs_list:
            print(f"trying to listen to song of index {self.playlist_index}")
            self.music_box.select_row(self.playlist_index)
            self.Network.ask_for_song_bytes_by_playlist_index(self.playlist_index)
        else:
            self.playlist_index = 0
            print(f"trying to listen to song of index {self.playlist_index}")
            self.music_box.select_row(self.playlist_index)
            self.Network.ask_for_song_bytes_by_playlist_index(self.playlist_index)
        self.music_box.playlist_duration_slider.setMinimum(0)
        song_dict = self.playlist_songs[self.playlist_index]
        duration_str = song_dict.get("audio_duration")
        self.music_box.update_duration_tex(duration_str)
        total_duration = duration_to_milliseconds(duration_str)
        self.music_box.playlist_duration_slider.setMaximum(total_duration)

    def get_setting_dict(self):
        settings_dict = {
            "volume": self.volume,
            "output_device": self.output_device_name,
            "input_device": self.input_device_name,
            "camera_device_index": self.camera_index,
            "font_size": self.font_size,
            "font": self.font_text,
            "theme_color": self.background_color,
            "censor_data": self.censor_data_from_strangers,
            "private_account": self.is_private_account,
            "push_to_talk_bind": self.push_to_talk_key,
            "two_factor_auth": self.two_factor_authentication
        }
        return settings_dict

    def update_settings_from_dict(self, settings_dict):
        # Update settings from the provided dictionary
        self.volume = settings_dict.get("volume")
        self.playlist_volume = self.volume
        self.output_device_name = settings_dict.get("output_device")
        self.input_device_name = settings_dict.get("input_device")
        self.camera_index = settings_dict.get("camera_device_index")
        self.font_size = settings_dict.get("font_size")
        self.font_text = settings_dict.get("font")
        self.update_background_color(settings_dict.get("theme_color"))
        self.censor_data_from_strangers = settings_dict.get("censor_data")
        self.is_private_account = settings_dict.get("private_account")
        self.push_to_talk_key = settings_dict.get("push_to_talk_bind")
        self.two_factor_authentication = settings_dict.get("two_factor_auth")
        self.updated_settings_page()
        self.updated_chat()

    def update_settings_dict(self):
        settings_dict = self.get_setting_dict()
        self.Network.send_settings_dict_to_server(settings_dict)

    def start_listen_udp_thread(self):
        self.listen_udp_thread.start()

    def start_call_threads(self):
        self.vc_data_list = []
        self.start_send_vc_thread()
        self.start_listen_thread()

    def close_call_threads(self):
        self.vc_data_list = []
        self.close_listen_thread()
        self.close_send_vc_thread()

    def close_listen_thread(self):
        self.vc_play_flag = False
        self.play_vc_data_thread.join()
        self.play_vc_data_thread = threading.Thread(target=self.thread_play_vc_data, args=())

    def close_send_vc_thread(self):
        self.vc_thread_flag = False
        self.send_vc_data_thread.join()
        self.send_vc_data_thread = threading.Thread(target=self.thread_send_voice_chat_data, args=())

    def rename_group_pressed(self):
        group_id_to_change = self.chat_box.current_group_id
        title = 'Input Dialog'
        label = 'Select a new name for this group'
        dialog = QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setTextEchoMode(QLineEdit.Normal)

        # Apply the stylesheet to set the text color to white
        dialog.setStyleSheet("""
            QLabel { color: white; }
            QLineEdit { color: white; }
            QPushButton { color: white; }
        """)

        # Execute the dialog and get the result
        ok = dialog.exec_()
        text = dialog.textValue()

        if ok and text:
            if len(text) < 20:
                self.Network.rename_group_by_id(text, group_id_to_change)
                print(f"changed group name to {text}")
        else:
            print("No group name entered")

    def rename_user_pressed(self):
        group_id_to_change = self.chat_box.current_group_id
        title = 'Input Dialog'
        label = 'Select a new name for your account'
        dialog = QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setTextEchoMode(QLineEdit.Normal)

        # Apply the stylesheet to set the text color to white
        dialog.setStyleSheet("""
            QLabel { color: white; }
            QLineEdit { color: white; }
            QPushButton { color: white; }
        """)

        # Execute the dialog and get the result
        ok = dialog.exec_()
        text = dialog.textValue()

        if ok and text:
            if is_valid_username(text):
                self.Network.rename_group_by_id(text, group_id_to_change)
                print(f"changed username to {text}")
                self.username = text
        else:
            print("No group name entered")

    def start_listen_thread(self):
        self.vc_play_flag = True
        self.play_vc_data_thread.start()

    def start_send_vc_thread(self):
        self.vc_thread_flag = True
        self.send_vc_data_thread.start()

    def scroll_back_to_index_before_update(self, n_last_widgets):
        self.messages_content_saver.scroll_up_by_n_widgets(n_last_widgets)
        print(f"scrolled back down by {n_last_widgets} widgets")

    def insert_messages_into_message_box(self, messages_list):
        self.messages_content_saver.insert_messages_list_to_layout(messages_list)

    def insert_new_message_in_chat(self, message_dict):
        self.messages_content_saver.add_new_message_at_start(message_dict)

    def insert_message_that_client_send(self, message_dict):
        self.insert_new_message_in_chat(message_dict)
        self.scroll_maximum_down()

    def scroll_maximum_down(self):
        self.messages_content_saver.scroll_maximum()

    def update_message_box(self):
        self.messages_content_saver.update_messages_layout()

    def update_groups_list_by_dict(self, updated_group_dict):
        index = 0
        for group_dict in self.groups_list:
            if group_dict.get("group_id") == updated_group_dict.get("group_id"):
                self.groups_list[index] = updated_group_dict
                print(f"updated group dict of id {updated_group_dict.get('group_id')}")
                encoded_image = updated_group_dict.get('group_b64_encoded_image')
                if encoded_image is not None:
                    new_image = base64.b64decode(encoded_image)
                else:
                    new_image = None
                self.update_circular_photo_of_group(updated_group_dict.get('group_id'), new_image)
                if group_dict.get("group_name") != updated_group_dict.get("group_name"):
                    print("names are not equal")
                    for index, chat in enumerate(self.chats_list):
                        new_group_full_name = f"({updated_group_dict.get('group_id')}){updated_group_dict.get('group_name')}"
                        chat_first_half = chat.split(")")[0]
                        if chat_first_half == f"({updated_group_dict.get('group_id')}":
                            self.chats_list[index] = new_group_full_name
                            print(f"changed name to {new_group_full_name}")
                            if self.in_call_with == chat:
                                self.in_call_with = new_group_full_name
                            elif self.calling_to == chat:
                                self.calling_to = new_group_full_name
                            elif self.getting_called_by == chat:
                                self.getting_called_by = new_group_full_name
                            elif self.selected_chat == chat:
                                self.selected_chat = new_group_full_name
                            break
                self.update_chat_page_without_messages()
                return
            index += 1

    def update_media_players_volume(self, value):
        self.mp3_message_media_player.setVolume(value)
        self.sound_effect_media_player.setVolume(value)
        # self.playlist_media_player.setVolume(value)
        self.ringtone_media_player.setVolume(value)
        self.calling_media_player.setVolume(value)

    def pause_or_unpause_mp3_files_player(self):
        if self.mp3_message_media_player.state() == QMediaPlayer.PlayingState:
            self.mp3_message_media_player.pause()
        elif self.mp3_message_media_player.state() == QMediaPlayer.PausedState:
            self.mp3_message_media_player.play()

    def update_every_screen(self):
        try:
            self.updated_chat()
            self.updated_social_page()
            self.updated_settings_page()
        except Exception as e:
            print(f"error in updating screens: {e}")

    def update_background_color(self, new_background_color_str):
        background_color_hex = self.color_design_mapping.get(new_background_color_str)
        self.background_color = new_background_color_str
        self.background_color_hex = background_color_hex
        get_new_hover_color = self.style_color_hover_mapping.get(new_background_color_str)
        self.standard_hover_color = get_new_hover_color
        self.setStyleSheet(f'''
            QWidget {{
                background-color: {background_color_hex};
            }}
        ''')
        self.music_box.update_music_page_style_sheet()
        print("updated background color")
        try:
            self.update_every_screen()
        except Exception as e:
            print(f"error in changing background color: {e}")

    def get_circular_image_bytes_by_name(self, name):
        for circular_image_dictionary in self.circular_images_dicts_list_of_users:
            username = circular_image_dictionary.get("username")
            if username == name:
                return circular_image_dictionary.get("circular_image_bytes")
        return None

    def get_circular_image_bytes_by_group_id(self, group_id):
        try:
            for circular_image_dictionary in self.circular_images_dicts_list_of_groups:
                current_group_id = circular_image_dictionary.get("group_id")
                if current_group_id == group_id:
                    return circular_image_dictionary.get("circular_image_bytes")
        except Exception as e:
            print(e)

    def caching_circular_images_of_users(self):
        self.circular_images_dicts_list_of_users = []
        for profile_dictionary in self.list_user_profile_dicts:
            username = profile_dictionary.get("username")
            image_bytes_encoded = profile_dictionary.get("encoded_image_bytes")
            if image_bytes_encoded is None:
                circular_image_bytes = None
            else:
                image_bytes = base64.b64decode(image_bytes_encoded)
                circular_image_bytes = make_circular_image(image_bytes)
            circular_images_dict = {
                "username": username,
                "circular_image_bytes": circular_image_bytes

            }
            self.circular_images_dicts_list_of_users.append(circular_images_dict)
        self.update_chat_page_without_messages()
        self.updated_settings_page()

    def caching_circular_images_of_groups(self):
        self.circular_images_dicts_list_of_groups = []
        for group in self.groups_list:
            group_id = group.get("group_id")
            image_bytes_encoded = group.get("group_b64_encoded_image")
            if image_bytes_encoded is None:
                circular_image_bytes = None
            else:
                image_bytes = base64.b64decode(image_bytes_encoded)
                circular_image_bytes = make_circular_image(image_bytes)
            circular_images_dict = {
                "group_id": group_id,
                "circular_image_bytes": circular_image_bytes

            }
            self.circular_images_dicts_list_of_groups.append(circular_images_dict)
        self.update_chat_page_without_messages()

    def update_profile_dict_of_user(self, name, new_profile_dict):
        try:
            index = 0
            for profile_dict in self.list_user_profile_dicts:
                if profile_dict.get("username") == name:
                    self.list_user_profile_dicts[index] = new_profile_dict
                    encoded_image = new_profile_dict.get("encoded_image_bytes")
                    if encoded_image is not None:
                        self.update_circular_photo_of_user(name, base64.b64decode(encoded_image))
                    else:
                        self.update_circular_photo_of_user(name, encoded_image)
                    break
                index += 1
        except Exception as e:
            print(f"error in updating profile dict of user: {e}")

    def update_profile_pic_dicts_list(self, name, new_image_bytes, circular_pic_bytes=None):
        for profile_dict in self.list_user_profile_dicts:
            if profile_dict.get("username") == name:
                if new_image_bytes is not None:
                    profile_dict["encoded_image_bytes"] = base64.b64encode(new_image_bytes).decode()
                else:
                    profile_dict["encoded_image_bytes"] = None
                print(f"updated the profile pic in dictionary list of username {name}")
                self.update_circular_photo_of_user(name, new_image_bytes, circular_pic_bytes)
                break

    def get_listened_song_by_user(self, name):
        for profile_dict in self.list_user_profile_dicts:
            if profile_dict.get("username") == name:
                return profile_dict.get("listening_to")

    def update_circular_photo_of_user(self, username, new_photo, circular_pic_bytes=None):
        if new_photo is None:
            circular_image = None
        else:
            if circular_pic_bytes is None:
                circular_image = make_circular_image(new_photo)
            else:
                circular_image = circular_pic_bytes
        # Iterate through the list of circular image dictionaries
        for user_dict in self.circular_images_dicts_list_of_users:
            # Check if the username matches
            if user_dict["username"] == username:
                # Update the circular photo for the user
                user_dict["circular_image_bytes"] = circular_image
                # Exit the loop since the update is done
                print(f"update_circular_photo_of_user of {username}")
                break
        # After updating, call the method to notify any listeners about the update
        self.update_chat_page_without_messages()

    def update_circular_photo_of_group(self, group_id, new_photo, circular_pic_bytes=None):
        if new_photo is None:
            circular_image = None
        else:
            if circular_pic_bytes is None:
                circular_image = make_circular_image(new_photo)
            else:
                circular_image = circular_pic_bytes
        # Iterate through the list of circular image dictionaries
        for group_dict in self.circular_images_dicts_list_of_groups:
            # Check if the username matches
            if group_dict["group_id"] == group_id:
                # Update the circular photo for the user
                group_dict["circular_image_bytes"] = circular_image
                # Exit the loop since the update is done
                print(f"update_circular_photo_of_user of group id :{group_id}")
                break
        # After updating, call the method to notify any listeners about the update
        self.update_chat_page_without_messages()

    def get_profile_pic_by_username(self, username):
        if self.list_user_profile_dicts is not None:
            for profile_dict in self.list_user_profile_dicts:
                if profile_dict.get("username") == username:
                    image_bytes_encoded = profile_dict.get("encoded_image_bytes")
                    if image_bytes_encoded is not None:
                        return base64.b64decode(image_bytes_encoded)
                    else:
                        return None

    def set_page_index_by_clicked(self):
        if self.chat_clicked_var:
            self.stacked_widget.setCurrentIndex(0)
        elif self.social_clicked_var:
            self.stacked_widget.setCurrentIndex(2)
        elif self.setting_clicked:
            self.stacked_widget.setCurrentIndex(1)
        elif self.music_clicked:
            self.stacked_widget.setCurrentIndex(3)

    def stop_watching_video(self):
        try:
            self.is_watching_video = False
            widget_to_remove = self.stacked_widget.currentWidget()  # Get the currently displayed widget
            self.stacked_widget.removeWidget(widget_to_remove)
            self.set_page_index_by_clicked()
            print("exited video")
            self.setFocus()
        except Exception as e:
            print(f"error in stopping video: {e}")

    def start_watching_video(self, video_bytes):
        try:
            self.is_watching_video = True
            video_player = VideoPlayer(video_bytes, self)
            number_of_widgets = self.stacked_widget.count()
            self.stacked_widget.addWidget(video_player)
            self.stacked_widget.setCurrentIndex(number_of_widgets)
            video_player.play_video()
        except Exception as e:
            print(f"had error trying to show video: {e}")

    def start_share_screen_send_thread(self):
        self.send_share_screen_thread.start()
        print("Started Share screen thread")

    def start_camera_data_thread(self):
        self.is_camera_shared = True
        self.send_camera_data_thread.start()
        print("Started Share camera thread")

    def update_share_screen_thread(self):
        self.send_share_screen_thread = threading.Thread(target=self.thread_send_share_screen_data, args=())

    def update_share_camera_thread(self):
        self.send_camera_data_thread = threading.Thread(target=self.thread_send_share_camera_data, args=())

    def end_share_camera_thread(self):
        self.is_camera_shared = False
        self.send_camera_data_thread.join()
        self.send_camera_data_thread = threading.Thread(target=self.thread_send_share_camera_data, args=())

    def update_stream_screen_frame(self, frame):
        try:
            self.stream_screen.display_frame(frame)
        except Exception as e:
            print(f"update_stream_screen_frame: {e}")

    def stop_watching_video_stream(self):
        self.is_watching_screen = False
        self.watching_user = ""
        self.watching_type = None
        self.stream_screen.close()
        self.showMaximized()

    def start_watching_video_stream(self):
        self.stream_screen = VideoClient(self)
        self.hide()
        self.stream_screen.showMaximized()

    def get_group_manager_by_group_id(self, id):
        for group_dict in self.groups_list:
            if group_dict["group_id"] == id:
                return group_dict.get("group_manager")
        else:
            return None

    def get_group_name_by_id(self, id):
        for group_dict in self.groups_list:
            if group_dict["group_id"] == id:
                return group_dict.get("group_name")
        else:
            return None

    def is_call_dict_exist_by_group_id(self, group_id):
        for call_dict in self.call_dicts:
            if call_dict.get("is_group_call"):
                if call_dict.get("group_id") == group_id:
                    return True
        return False

    def get_number_of_members_by_group_id(self, group_id):
        return len(self.get_group_members_by_group_id(group_id))

    def get_group_members_by_group_id(self, group_id):
        group_id = int(group_id)
        for group in self.groups_list:
            if group["group_id"] == group_id:
                return group["group_members"]
        return None  # Return 0 if the group ID is not found

    def remove_call_dict_by_id(self, id_to_remove):
        for call_dict in self.call_dicts:
            if call_dict.get("call_id") == id_to_remove:
                self.call_dicts.remove(call_dict)
                print("removed call dict, because call isn't available anymore")

    def get_call_dict_by_group_id(self, group_id):
        for call_dict in self.call_dicts:
            if call_dict.get("is_group_call"):
                if call_dict.get("group_id") == group_id:
                    return call_dict
        print("could not find the call dict")

    def get_call_dict_by_user(self, user):
        for call_dict in self.call_dicts:
            if user in call_dict.get("participants"):
                return call_dict
        print("could not find the call dict")

    def is_call_dict_exists_by_id(self, call_id):
        for call_dict in self.call_dicts:
            if call_dict.get("call_id") == call_id:
                return True
        return False

    def find_difference(self, list1, list2):
        return list(set(list1) - set(list2))

    def update_call_dict_by_id(self, updated_call_dict):
        updated_participants = updated_call_dict.get("participants")
        for call_dict in self.call_dicts:
            participants_before = call_dict.get("participants")
            if call_dict.get("call_id") == updated_call_dict.get("call_id"):
                self.call_dicts.remove(call_dict)
                if len(updated_participants) > len(participants_before) and self.username in updated_participants:
                    different_users = self.find_difference(updated_participants, participants_before)
                    if len(different_users) == 1 and self.username not in different_users:
                        join_sound = QMediaContent(QUrl.fromLocalFile('discord_app_assets/join_call_sound_effect.mp3'))
                        self.play_sound_effect(join_sound)
                elif len(updated_participants) < len(participants_before) and self.username in updated_participants:
                    user_left_sound = QMediaContent(
                        QUrl.fromLocalFile('discord_app_assets/leave_call_sound_effect.mp3'))
                    self.play_sound_effect(user_left_sound)
        self.call_dicts.append(updated_call_dict)

    def reset_call_var(self):
        try:
            self.is_joining_call = False
            self.joining_to = ""
            self.is_in_a_call = False
            self.is_calling = False
            self.calling_to = ""
            self.in_call_with = ""
            self.is_getting_called = False
            self.getting_called_by = ""
            self.mute = False
            self.deafen = False
            self.stop_sound()
            self.updated_chat()
            self.is_screen_shared = False
            self.is_camera_shared = False
            self.watching_user = ""
            if self.is_watching_screen:
                self.stop_watching_video_stream()

            self.is_watching_screen = False
        except Exception as e:
            print(f"reset_call_var error: {e}")

    def end_current_call(self):
        try:
            self.Network.leave_call()
            print(f"client hang up call123...")
        except Exception as e:
            print(f"end_current_call error: {e}")

    def initiate_call(self):
        self.is_in_a_call = True
        self.is_calling = False
        self.is_getting_called = False
        self.is_joining_call = False
        self.stop_sound()
        try:
            if self.calling_to != "":
                if "(" in self.calling_to:
                    self.in_call_with = self.calling_to
                    print(f"in call with {self.in_call_with}")
                    self.calling_to = ""
                else:
                    self.in_call_with = self.calling_to
                    print(f"in call with {self.in_call_with}")
                    self.calling_to = ""
            elif self.getting_called_by != "":
                if "(" in self.getting_called_by:
                    group_id, group_name, group_caller = parse_group_caller_format(self.getting_called_by)
                    self.in_call_with = "(" + str(group_id) + ")" + group_name
                    print(f"in call with {self.in_call_with}")
                    self.getting_called_by = ""
                else:
                    self.in_call_with = self.getting_called_by
                    print(f"in call with {self.in_call_with}")
                    self.getting_called_by = ""
            elif self.joining_to != "":
                self.in_call_with = self.joining_to
                print(f"in call with {self.in_call_with}")
                self.joining_to = ""
        except Exception as e:
            print(f"error in initiating call is {e}")

    def handle_state_changed_sound_effect(self, state):
        if state == QMediaPlayer.StoppedState:
            if self.is_getting_called:
                self.ringtone_media_player.setMedia(self.ringtone)
                self.ringtone_media_player.play()

    def play_ding_sound_effect(self):
        try:
            self.play_sound_effect(self.ding_sound_effect)
        except Exception as e:
            print(f"::{e}")

    def getting_a_call(self):
        try:
            self.ringtone_media_player.setMedia(self.ringtone)
            self.ringtone_media_player.play()
        except Exception as e:
            print(f"::{e}")

    def new_message_play_audio(self):
        try:
            self.sound_effect_media_player.setMedia(self.new_message_audio)
            self.sound_effect_media_player.play()
        except Exception as e:
            print(f"::{e}")

    def play_sound_effect(self, sound):
        try:
            self.sound_effect_media_player.setMedia(sound)
            self.sound_effect_media_player.play()
        except Exception as e:
            print(f"::{e}")

    def play_calling_sound_effect(self, sound):
        try:
            self.calling_media_player.setMedia(sound)
            self.calling_media_player.play()
        except Exception as e:
            print(f"::{e}")

    def stop_sound(self):
        try:
            self.sound_effect_media_player.stop()
            self.ringtone_media_player.stop()
            self.calling_media_player.stop()
        except Exception as e:
            print(f"Error stopping sound: {e}")

    def chat_clicked(self):
        if not self.chat_clicked_var:
            self.current_friends_box_search = False
            self.current_chat_box_search = False
            self.temp_search_list = []
            self.chat_clicked_var = True
            self.stacked_widget.setCurrentIndex(0)
            if self.setting_clicked:
                self.update_settings_dict()
            self.setting_clicked = False
            self.social_clicked_var = False
            self.music_clicked = False

    def settings_clicked(self):
        try:
            if not self.setting_clicked:
                self.current_friends_box_search = False
                self.current_chat_box_search = False
                self.stacked_widget.setCurrentIndex(1)
                self.chat_clicked_var = False
                self.setting_clicked = True
                self.social_clicked_var = False
                self.music_clicked = False
        except Exception as e:
            print(e)

    def social_clicked(self):
        if not self.social_clicked_var:
            self.current_friends_box_search = False
            self.current_chat_box_search = False
            self.temp_search_list = []
            self.stacked_widget.setCurrentIndex(2)
            self.chat_clicked_var = False
            self.setting_clicked = False
            self.social_clicked_var = True
            self.music_clicked = False

    def updated_social_page(self):
        try:
            if self.friends_box_page == "add friend":
                self.stacked_widget.removeWidget(self.friends_box)
                self.friends_box = FriendsBox(friends_list=self.friends_list,
                                              requests_list=self.request_list, Network=self.Network,
                                              username=self.username,
                                              parent=self)
                self.stacked_widget.insertWidget(2, self.friends_box)
                if self.social_clicked_var:
                    self.stacked_widget.setCurrentIndex(2)
            else:
                search_bar_text = self.friends_box.search.text()
                has_had_focus_of_search_bar = self.friends_box.search.hasFocus()
                self.stacked_widget.removeWidget(self.friends_box)
                self.friends_box = FriendsBox(friends_list=self.friends_list,
                                              requests_list=self.request_list, Network=self.Network,
                                              username=self.username,
                                              parent=self)
                self.stacked_widget.insertWidget(2, self.friends_box)

                if len(search_bar_text) > 0:
                    self.friends_box.search.setText(search_bar_text)
                    self.friends_box.search.setFocus(True)
                    self.friends_box.search.deselect()
                else:
                    if has_had_focus_of_search_bar:
                        self.friends_box.search.setFocus(True)
                        self.friends_box.search.deselect()

                if self.social_clicked_var:
                    self.stacked_widget.setCurrentIndex(2)
        except Exception as e:
            print(f"error in updating social page{e}")

    def updated_settings_page(self):
        try:
            self.stacked_widget.removeWidget(self.settings_box)
            self.settings_box = SettingsBox(parent=self)
            self.stacked_widget.insertWidget(1, self.settings_box)

            self.set_page_index_by_clicked()
        except Exception as e:
            print(f"error in updated_settings_page error:{e}")

    def keyReleaseEvent(self, event):
        if self.push_to_talk_key is not None:
            key = event.key()
            key_string = chr(key) if 32 <= key <= 126 else self.special_keys_mapping.get(key)
            if key_string == self.push_to_talk_key:
                if self.is_push_to_talk:
                    self.is_push_to_talk_pressed = False
                    print("push to talk released")

    def keyPressEvent(self, event):
        n = self.Network
        if self.push_to_talk_key is not None:
            key = event.key()
            key_string = chr(key) if 32 <= key <= 126 else self.special_keys_mapping.get(key)
            if key_string == self.push_to_talk_key:
                if self.is_push_to_talk:
                    self.is_push_to_talk_pressed = True
                    print("push to talk button toggled")
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            try:
                if self.chat_clicked_var and self.chat_box.chat_name_label.text() != "" or self.setting_clicked:
                    if self.chat_box.check_editing_status():
                        if len(self.chat_box.text_entry.text()) > 0:
                            current_time = datetime.datetime.now()
                            formatted_time = current_time.strftime('%Y-%m-%d %H:%M')
                            message_dict = create_message_dict(self.chat_box.text_entry.text(), self.username,
                                                               str(formatted_time), "string", None)
                            self.list_messages.insert(0, message_dict)
                            n.send_message(self.username, self.selected_chat, message_dict.get("content"), "string",
                                           None)
                            print("Sent message to server")
                            self.chat_box.text_entry.setText("")
                            if self.selected_chat != self.chats_list[0]:
                                self.chats_list.remove(self.selected_chat)
                                self.chats_list.insert(0, self.selected_chat)
                            self.chat_box.text_entry.setFocus()
                            self.insert_message_that_client_send(message_dict)
                            self.is_new_chat_clicked = True
                            self.updated_chat()
                            self.chat_box.text_entry.setFocus(True)
                if self.file_to_send:
                    # Compresses the byte representation of an image using zlib,
                    # encodes the compressed data as base64, and then decodes
                    # it into a UTF-8 string for transmission or storage.
                    base64_file = base64.b64encode(self.file_to_send).decode()
                    current_time = datetime.datetime.now()
                    formatted_time = current_time.strftime('%Y-%m-%d %H:%M')
                    file_type = ""
                    if self.file_name.endswith(("png", "jpg")):
                        file_type = "image"
                    elif self.file_name.endswith(("mp4", "mov")):
                        file_type = "video"
                    elif self.file_name.endswith("mp3"):
                        file_type = "audio"
                    elif self.file_name.endswith("txt"):
                        file_type = "txt"
                    elif self.file_name.endswith("pdf"):
                        file_type = "pdf"
                    elif self.file_name.endswith("pptx"):
                        file_type = "pptx"
                    elif self.file_name.endswith("docx"):
                        file_type = "docx"
                    elif self.file_name.endswith("py"):
                        file_type = "py"
                    elif self.file_name.endswith("xlsx"):
                        file_type = "xlsx"
                    message_dict = create_message_dict(base64_file, self.username,
                                                       str(formatted_time), file_type, self.file_name)
                    self.list_messages.insert(0, message_dict)
                    # add here that the type of the message is sent as well
                    try:
                        n.send_message(self.username, self.selected_chat, base64_file, file_type,
                                       self.file_name)
                    except Exception as e:
                        print(f"error in sending message")
                    self.file_to_send = None
                    self.file_name = ""
                    if self.selected_chat != self.chats_list[0]:
                        self.chats_list.remove(self.selected_chat)
                        self.chats_list.insert(0, self.selected_chat)
                    self.insert_message_that_client_send(message_dict)
                    self.is_new_chat_clicked = True
                    self.updated_chat()
                    self.chat_box.text_entry.setFocus(True)
                elif self.social_clicked_var:
                    self.friends_box.send_friend_request()
                elif self.music_clicked:
                    search_str = self.music_box.search_song_entry.text()
                    if len(search_str) > 0:
                        n.send_song_search(search_str)
                    self.music_box.search_song_entry.setText("")
            except Exception as e:
                print(f"expection in key press event:{e}")
        elif event.key() == Qt.Key_Escape:
            if not self.chat_clicked_var:
                if not self.music_clicked:
                    self.chat_clicked()
                    self.updated_chat()
                else:
                    self.chat_clicked()
                    self.update_chat_page_without_messages()
            else:
                if self.is_create_group_pressed:
                    self.is_create_group_pressed = False
                    self.selected_group_members.clear()
                    self.updated_chat()
        else:
            if self.setting_clicked and self.is_editing_push_to_talk_button:
                key = event.key()
                key_string = chr(key) if 32 <= key <= 126 else self.special_keys_mapping.get(key)
                self.push_to_talk_key = key_string
                self.is_editing_push_to_talk_button = False
                self.updated_settings_page()

    def hide_chat(self):
        self.main_layout.addSpacerItem(self.spacer)
        self.chat_box.hide()

    def show_chat(self):
        self.main_layout.removeItem(self.spacer)
        self.chat_box.setVisible(True)

    def updated_chat(self):
        self.update_chat_page(True)

    def update_chat_page_without_messages(self):
        self.update_chat_page(False)

    def update_chat_page(self, is_update_messages_box):
        try:
            if is_update_messages_box:
                self.is_messages_need_update = True
            text = ""
            try:
                text = self.chat_box.text_entry.text()
            except Exception as e:
                print(f"error in updated chat1 {e}")
            has_had_focus_of_search_bar = self.chat_box.find_contact_text_entry.hasFocus()
            self.stacked_widget.removeWidget(self.chat_box)
            self.chat_box.deleteLater()  # Schedule deletion of the old ChatBox widget
            search_bar_text = self.chat_box.find_contact_text_entry.text()
            try:
                self.chat_box = ChatBox(self.list_messages, parent=self, Network=self.Network)
            except Exception as e:
                self.chat_box = ChatBox(self.list_messages, parent=self, Network=self.Network)
                print(f"error in creating chat_box on updated_chat_func : {e}")

            self.stacked_widget.insertWidget(0, self.chat_box)
            self.chat_box.text_entry.setText(text)
            if len(search_bar_text) > 0:
                self.chat_box.find_contact_text_entry.setText(search_bar_text)
                self.chat_box.find_contact_text_entry.setFocus(True)
                self.chat_box.find_contact_text_entry.deselect()
            else:
                if has_had_focus_of_search_bar:
                    self.chat_box.find_contact_text_entry.setFocus(True)
                    self.chat_box.find_contact_text_entry.deselect()
            if self.chat_clicked_var:
                self.stacked_widget.setCurrentIndex(0)
        except Exception as e:
            self.chat_box = ChatBox(self.list_messages, parent=self, Network=self.Network)
            print(f"error in updated chat2 {e}")

    def update_values(self):
        self.friends_box.username = self.username

    def stop_all_media_player(self):
        self.mp3_message_media_player.stop()
        self.ringtone_media_player.stop()
        self.calling_media_player.stop()
        self.sound_effect_media_player.stop()
        self.playlist_media_player.stop()

    def closeEvent(self, event):
        # This function is called when the window is closed
        try:
            self.stop_all_media_player()
            self.close_all_threads()
            self.page_controller_object.quit_application()
        except Exception as e:
            print(f"error in closing mainpage {e}")

    def lost_connection_with_server(self):
        self.page_controller_object.lost_connection_with_server()


class SignUpPage(QWidget):
    def __init__(self, page_controller_object):

        super().__init__()
        self.page_controller_object = page_controller_object
        self.init_ui()
        self.password_not_match_label = QLabel('Password does not match', self)
        self.password_not_match_label.setStyleSheet("color: red; font-size: 12px;")

        password_not_match_label_x, password_not_match_label_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.382))
        self.password_not_match_label.move(password_not_match_label_x, password_not_match_label_y)
        self.password_not_match_label.hide()

        x = int(self.page_controller_object.screen_width * 0.453)
        email_required_field_y = int(self.page_controller_object.screen_height * 0.529)
        username_required_field_y = int(self.page_controller_object.screen_height * 0.307)
        password_required_field_y = int(self.page_controller_object.screen_height * 0.381)
        confirm_password_required_field_y = int(self.page_controller_object.screen_height * 0.4555)
        invalid_email_y = int(self.page_controller_object.screen_height * 0.529)
        password_too_short_y = int(self.page_controller_object.screen_height * 0.382)
        username_already_used_y = int(self.page_controller_object.screen_height * 0.307)

        self.email_required_field = self.create_label("Required field", (x, email_required_field_y))
        self.username_required_field = self.create_label("Required field", (x, username_required_field_y))
        self.password_required_field = self.create_label("Required field", (x, password_required_field_y))
        self.confirm_password_required_field = self.create_label("Required field",
                                                                 (x, confirm_password_required_field_y))
        self.invalid_email = self.create_label("Invalid Email", (x, invalid_email_y))
        self.password_too_short = self.create_label("Password too short", (x, password_too_short_y))
        self.username_already_used = self.create_label("Username is taken/invalid", (x, username_already_used_y))
        self.hide_every_error_label()

    def hide_every_error_label(self):
        self.password_too_short.hide()
        self.email_required_field.hide()
        self.username_required_field.hide()
        self.password_required_field.hide()
        self.confirm_password_required_field.hide()
        self.invalid_email.hide()
        self.password_not_match_label.hide()
        self.username_already_used.hide()

    def create_label(self, text, position):
        label = QLabel(text, self)
        label.setStyleSheet("color: red; font-size: 12px;")
        label.move(position[0], position[1])
        label.hide()
        return label

    def init_ui(self):
        try:
            label = QLabel("Create Account", self)
            username = QLineEdit(self)
            password = QLineEdit(self)
            password_confirm = QLineEdit(self)
            email = QLineEdit(self)
            password.setEchoMode(QLineEdit.Password)
            password_confirm.setEchoMode(QLineEdit.Password)
            image_button = QPushButton(self)

            # Load an image and set it as the button's icon
            icon = QIcon("discord_app_assets/right-arrow-icon-27.png")
            image_button.setIcon(icon)

            width, height = int(self.page_controller_object.screen_width * 0.01), int(
                self.page_controller_object.screen_height * 0.018)

            icon_size = QSize(width, height)  # Set your desired size
            icon_actual_size = icon.actualSize(icon.availableSizes()[0])
            scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

            image_button.setIconSize(scaled_size)

            image_button_x, image_button_y = (int(self.page_controller_object.screen_width * 0.471),
                                              int(self.page_controller_object.screen_height * 0.217))

            image_button.move(image_button_x, image_button_y)

            image_button.clicked.connect(self.return_button_pressed)

            # Set placeholder text and color
            username.setPlaceholderText("Username")
            username.setStyleSheet("color: white;")

            password.setPlaceholderText("Password")
            password.setStyleSheet("color: white;")

            password_confirm.setPlaceholderText("Confirm Password")
            password_confirm.setStyleSheet("color: white;")

            email.setPlaceholderText("Email")
            email.setStyleSheet("color: white;")

            label_x, label_y = (int(self.page_controller_object.screen_width * 0.44),
                                int(self.page_controller_object.screen_height * 0.177))
            username_x = label_x
            username_y = int(self.page_controller_object.screen_height * 0.259)
            password_x = label_x
            password_y = int(self.page_controller_object.screen_height * 0.333)
            password_confirm_x = label_x
            password_confirm_y = int(self.page_controller_object.screen_height * 0.407)
            email_y = int(self.page_controller_object.screen_height * 0.481)
            email_x = label_x
            label.move(label_x, label_y)
            username.move(username_x, username_y)
            password.move(password_x, password_y)
            password_confirm.move(password_confirm_x, password_confirm_y)
            email.move(email_x, email_y)

            # Create button
            submit_button = QPushButton('Submit', self)
            submit_button.clicked.connect(
                lambda: self.submit_form(username.text(), password.text(), password_confirm.text(), email.text()))

            submit_button_x, submit_button_y = (int(self.page_controller_object.screen_width * 0.427),
                                                int(self.page_controller_object.screen_height * 0.555))

            submit_button.move(submit_button_x, submit_button_y)

            submit_button.setStyleSheet('''
                QPushButton {
                    background-color: #6fa8b6;
                    color: #f0f1f1;
                    padding: 10px;  /* Adjust the padding to make the button smaller */
                    border: 1px solid #2980b9;
                    border-radius: 5px;
                    min-width: 200px;  /* Adjust the min-width to set the minimum width of the button */
                    max-width: 300px;  /* Adjust the max-width to set the maximum width of the button */
                    min-height: 30px;  /* Adjust the min-height to set the minimum height of the button */
                    max-height: 60px;  /* Adjust the max-height to set the maximum height of the button */
                    font-size: 16px;  /* Set your desired font size */
                    margin-top: 10px;  /* Adjust the margin-top to set the top margin of the button */
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1f618d;
                }
            ''')
            # Set styles
            self.setStyleSheet("""
                QWidget {
                    background-color: #141c4b;  /* Set your desired background color */
                }
                QLabel {
                    color: #f0f1f1;
                    font-size: 20px;
                    margin-bottom: 20px;
                }
                QLineEdit {
                    background-color: #6fa8b6;
                    color: #f0f1f1;
                    padding: 10px;
                    border: 1px solid #2980b9;
                    border-radius: 5px;
                    font-size: 16px;
                    margin-bottom: 10px;
                }

            """)
        except Exception as e:
            print(f"error in Sign_up_page {e}")

    def submit_form(self, username, password, password_confirm, email):
        n = self.page_controller_object.n
        self.hide_every_error_label()
        is_info_valid = True
        if username == "" or password == "" or password_confirm == "" or email == "":
            is_info_valid = False
            if email == "":
                self.email_Required_field.show()
            if password == "":
                self.password_Required_field.show()
            if password_confirm == "":
                self.confirm_password_Required_field.show()
            if username == "":
                self.username_Required_field.show()

        if password != password_confirm and password != "" and password_confirm != "":
            is_info_valid = False
            self.password_not_match_label.show()
        elif password == password_confirm and len(password) < 8:
            is_info_valid = False
            self.password_too_short.show()
        if not is_email_valid(email) and email != "":
            is_info_valid = False
            self.invalid_email.show()
        if not is_valid_username(username):
            is_info_valid = False
        if not is_valid_password(password):
            is_info_valid = False

        if is_info_valid:
            n.send_sign_up_info(username, password, email)
            data = n.recv_str()
            message_type = data.get("message_type")
            if message_type == "code":
                action, destination = data.get("action"), data.get("sent_to")
                if action == "sent" and destination == "email":
                    self.page_controller_object.change_to_verification_code_page()
            elif message_type == "sign_up":
                result = data.get("sign_up_status")
                if result == "invalid":
                    self.username_already_used.show()

    def return_button_pressed(self):
        self.page_controller_object.change_to_login_page()


class LoginPage(QWidget):
    def __init__(self, page_controller_object):
        super().__init__()
        self.page_controller_object = page_controller_object

        self.init_ui()
        self.visibility_password_button = QPushButton(self)
        # Load an image and set it as the button's icon
        self.show_password_icon = QIcon("discord_app_assets/show_password_icon.png")
        self.hide_password_icon = QIcon("discord_app_assets/hide_password_icon1.png")
        self.visibility_password_button.setIcon(self.show_password_icon)
        self.current_icon = "discord_app_assets/show_password_icon.png"

        width, height = int(self.page_controller_object.screen_width * 0.02), int(
            self.page_controller_object.screen_height * 0.036)

        icon_size = QSize(width, height)  # Set your desired size
        icon_actual_size = self.show_password_icon.actualSize(self.show_password_icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
        self.visibility_password_button.setIconSize(scaled_size)

        visibility_password_button_x, visibility_password_button_y = (
        int(self.page_controller_object.screen_width * 0.528), int(self.page_controller_object.screen_height * 0.333))

        self.visibility_password_button.move(visibility_password_button_x, visibility_password_button_y)
        self.visibility_password_button.clicked.connect(self.show_password_button_pressed)

        self.visibility_password_button.setStyleSheet("""
            QPushButton {
                background-color: #6fa8b6;
                background-repeat: no-repeat;
                background-position: center;
            }
        """)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Password")
        self.password.setStyleSheet("color: white;")

        password_x, password_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.333))

        self.password.move(password_x, password_y)

        self.username_entry = QLineEdit(self)
        self.remember_me_status = False
        self.username_entry.setPlaceholderText("Username")
        self.username_entry.setStyleSheet("color: white;")

        username_entry_x, username_entry_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.259))

        self.username_entry.move(username_entry_x, username_entry_y)
        self.incorrect_label = QLabel('Username or Password incorrect', self)
        self.incorrect_label.setStyleSheet(
            "color: red; font-size: 12px;")  # Set the text color to blue and font size to 12px

        incorrect_label_x, incorrect_label_y = (
        int(self.page_controller_object.screen_width * 0.445), int(self.page_controller_object.screen_height * 0.308))

        self.incorrect_label.move(incorrect_label_x, incorrect_label_y)
        self.incorrect_label.hide()

        self.user_is_logged_in = QLabel('Username already logged in', self)
        self.user_is_logged_in.setStyleSheet(
            "color: red; font-size: 12px;")  # Set the text color to blue and font size to 12px

        user_is_logged_in_x, user_is_logged_in_y = (
        int(self.page_controller_object.screen_width * 0.445), int(self.page_controller_object.screen_height * 0.308))

        self.user_is_logged_in.move(user_is_logged_in_x, user_is_logged_in_y)
        self.user_is_logged_in.hide()

    def init_ui(self):

        label = QLabel("Welcome Back", self)
        image_button = QPushButton(self)

        # Load an image and set it as the button's icon
        icon = QIcon("discord_app_assets/right-arrow-icon-27.png")
        image_button.setIcon(icon)
        width, height = int(self.page_controller_object.screen_width * 0.01), int(
            self.page_controller_object.screen_height * 0.018)

        icon_size = QSize(width, height)  # Set your desired size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

        image_button.setIconSize(scaled_size)

        image_button_x, image_button_y = (
        int(self.page_controller_object.screen_width * 0.471), int(self.page_controller_object.screen_height * 0.217))

        image_button.move(image_button_x, image_button_y)

        # Create "Forgot your password?" label
        forgot_password_label = QPushButton('Forgot your password?', self)
        make_q_object_clear(forgot_password_label)
        forgot_password_label.setStyleSheet(
            "color: white; font-size: 12px;")  # Set the text color to blue and font size to 12px

        sign_up_label = QPushButton("Don't have a user yet? sign up here", self)
        make_q_object_clear(sign_up_label)
        sign_up_label.setStyleSheet(
            "color: white; font-size: 12px;")  # Set the text color to blue and font size to 12px
        sign_up_label.clicked.connect(self.move_to_sign_up_page)

        sign_up_label_x, sign_up_label_y = (
        int(self.page_controller_object.screen_width * 0.4244), int(self.page_controller_object.screen_height * 0.495))

        sign_up_label.move(sign_up_label_x, sign_up_label_y)

        checkbox = QCheckBox('Keep me signed in', self)

        checkbox.setStyleSheet("QCheckBox { color: white; font-size: 12px}")
        checkbox.stateChanged.connect(self.on_checkbox_change)

        checkbox_x, checkbox_y = (
        int(self.page_controller_object.screen_width * 0.445), int(self.page_controller_object.screen_height * 0.3842))

        checkbox.move(checkbox_x, checkbox_y)
        # Connect the linkActivated signal to a custom slot
        forgot_password_label.clicked.connect(self.forgot_password_clicked)

        forgot_password_label_x, forgot_password_label_y = (
        int(self.page_controller_object.screen_width * 0.445), int(self.page_controller_object.screen_height * 0.412))

        forgot_password_label.move(forgot_password_label_x, forgot_password_label_y)

        label_x, label_y = (
        int(self.page_controller_object.screen_width * 0.445), int(self.page_controller_object.screen_height * 0.177))

        label.move(label_x, label_y)

        # Create button
        submit_button = QPushButton('Login', self)
        submit_button.clicked.connect(self.submit_form)

        submit_button_x, submit_button_y = (
        int(self.page_controller_object.screen_width * 0.424), int(self.page_controller_object.screen_height * 0.43))

        submit_button.move(submit_button_x, submit_button_y)
        submit_button.setStyleSheet('''
            QPushButton {
                background-color: #6fa8b6;
                color: #f0f1f1;
                padding: 10px;  /* Adjust the padding to make the button smaller */
                border: 1px solid #2980b9;
                border-radius: 5px;
                min-width: 200px;  /* Adjust the min-width to set the minimum width of the button */
                max-width: 300px;  /* Adjust the max-width to set the maximum width of the button */
                min-height: 30px;  /* Adjust the min-height to set the minimum height of the button */
                max-height: 60px;  /* Adjust the max-height to set the maximum height of the button */
                font-size: 16px;  /* Set your desired font size */
                margin-top: 10px;  /* Adjust the margin-top to set the top margin of the button */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
        ''')

        # Set styles
        self.setStyleSheet("""
            QWidget {
                background-color: #141c4b;  /* Set your desired background color */
            }
            QLabel {
                color: #f0f1f1;
                font-size: 20px;
                margin-bottom: 20px;
            }
            QLineEdit {
                background-color: #6fa8b6;
                color: #f0f1f1;
                padding: 10px;
                border: 1px solid #2980b9;
                border-radius: 5px;
                font-size: 16px;
                margin-bottom: 10px;
            }
        """)

    def on_checkbox_change(self, state):
        # This function is called when the checkbox state changes
        if state == 2:  # 2 corresponds to checked state
            self.remember_me_status = True
        else:
            self.remember_me_status = False

    def submit_form(self):
        try:
            n = self.page_controller_object.n
            self.incorrect_label.hide()
            self.user_is_logged_in.hide()
            self.username = self.username_entry.text()
            password = self.password.text()
            n.send_login_info(self.username, password)
            data = n.recv_str()
            message_type = data.get("message_type")
            if message_type == "login":
                login_status = data.get("login_status")
                if login_status == "confirm":
                    print("logged in successfully")
                    n.connect_between_udp_port_address_to_username()
                    self.hide()
                    if self.remember_me_status:
                        n.ask_for_security_token()
                        print("You will be remembered")
                    self.page_controller_object.main_page.username = self.username
                    self.page_controller_object.main_page.update_values()
                    self.page_controller_object.is_logged_in = True
                    self.page_controller_object.start_receive_thread_after_login()
                    self.page_controller_object.main_page.start_listen_udp_thread()
                    self.page_controller_object.change_to_splash_page()
                elif login_status == "already_logged_in":
                    print("User logged in from another device")
                    self.user_is_logged_in.show()
                elif login_status == "2fa":
                    print("You have 2fa On")
                    self.page_controller_object.is_waiting_for_2fa_code = True
                    self.page_controller_object.change_to_verification_code_page()
                else:
                    print("login info isn't correct")
                    self.incorrect_label.show()
        except Exception as e:
            print(f"error in trying to login {e}")

    def forgot_password_clicked(self):
        self.page_controller_object.change_to_forget_password_page()

    def move_to_sign_up_page(self):
        try:
            self.page_controller_object.change_to_sign_up_page()
        except Exception as e:
            print(e)

    def show_password_button_pressed(self):
        if self.current_icon == "discord_app_assets/show_password_icon.png":
            self.password.setEchoMode(QLineEdit.Normal)
            self.current_icon = "discord_app_assets/hide_password_icon.png"
            self.visibility_password_button.setIcon(self.hide_password_icon)
        else:
            self.password.setEchoMode(QLineEdit.Password)
            self.current_icon = "discord_app_assets/show_password_icon.png"
            self.visibility_password_button.setIcon(self.show_password_icon)


class VideoClient(QMainWindow):
    def __init__(self, main_page):
        super().__init__()
        self.main_page = main_page
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.image_label = QLabel(self)
        self.image_label.move(0, 0)

        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.image_label)

        x, y = (int(self.main_page.screen_width * 0.052), int(self.main_page.screen_height * 0.092))
        width, height = (int(self.main_page.screen_width * 0.416), int(self.main_page.screen_height * 0.555))
        self.setGeometry(x, y, width, height)
        self.setWindowTitle('Video Client')

    def display_frame(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        screen_size = QApplication.primaryScreen().size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()

        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_image).scaled(screen_width, screen_height)

        # Clear the existing pixmap
        self.image_label.clear()

        # Set the new pixmap
        self.image_label.setPixmap(pixmap)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.main_page.showMaximized()
            self.main_page.Network.stop_watching_current_stream()
            print(f"stopped watching {self.main_page.watching_user} share screen")
            self.main_page.is_watching_screen = False
            self.main_page.watching_user = ""
            self.main_page.watching_type = None
            self.close()


class ForgetPasswordPage(QWidget):
    def __init__(self, page_controller_object):
        super().__init__()
        self.page_controller_object = page_controller_object
        self.init_ui()
        self.username = QLineEdit(self)
        username_x, username_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.26))

        self.username.move(username_x, username_y)
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet("color: white;")
        self.email = QLineEdit(self)
        self.email.setPlaceholderText("Email")
        self.email.setStyleSheet("color: white;")
        email_x, email_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.33))

        self.email.move(email_x, email_y)

    def create_label(self, text, position):
        label = QLabel(text, self)
        label.setStyleSheet("color: red; font-size: 12px;")
        label.move(position[0], position[1])
        label.hide()
        return label

    def init_ui(self):
        label = QLabel("Forget password", self)

        image_button = QPushButton(self)
        # Load an image and set it as the button's icon
        icon = QIcon("discord_app_assets/right-arrow-icon-27.png")
        image_button.setIcon(icon)
        width, height = int(self.page_controller_object.screen_width * 0.01), int(
            self.page_controller_object.screen_height * 0.018)

        icon_size = QSize(width, height)  # Set your desired size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
        image_button.setIconSize(scaled_size)
        code_label_x, code_label_y = (
        int(self.page_controller_object.screen_width * 0.471), int(self.page_controller_object.screen_height * 0.2175))

        image_button.move(code_label_x, code_label_y)
        image_button.clicked.connect(self.return_button_pressed)

        # Set placeholder text and color

        # Create "Forgot your password?" label
        code_label = QLabel('<a href="forgot">Resend code</a>', self)
        code_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        code_label.setOpenExternalLinks(False)  # Disable external links to capture linkActivated signal
        code_label.setStyleSheet("color: blue; font-size: 15px;")  # Set the text color to blue and font size to 12px

        # Connect the linkActivated signal to a custom slot
        code_label.linkActivated.connect(self.resend_code_clicked)
        code_label_x, code_label_y = (
        int(self.page_controller_object.screen_width * 0.45), int(self.page_controller_object.screen_height * 0.388))

        code_label.move(code_label_x, code_label_y)
        label_x, label_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.177))

        label.move(label_x, label_y)

        # Create button
        submit_button = QPushButton('Submit info', self)
        submit_button.clicked.connect(self.submit_form)
        submit_button_x, submit_button_y = (
        int(self.page_controller_object.screen_width * 0.424), int(self.page_controller_object.screen_height * 0.416))

        submit_button.move(submit_button_x, submit_button_y)
        submit_button.setStyleSheet('''
            QPushButton {
                background-color: #6fa8b6;
                color: #f0f1f1;
                padding: 10px;  /* Adjust the padding to make the button smaller */
                border: 1px solid #2980b9;
                border-radius: 5px;
                min-width: 200px;  /* Adjust the min-width to set the minimum width of the button */
                max-width: 300px;  /* Adjust the max-width to set the maximum width of the button */
                min-height: 30px;  /* Adjust the min-height to set the minimum height of the button */
                max-height: 60px;  /* Adjust the max-height to set the maximum height of the button */
                font-size: 16px;  /* Set your desired font size */
                margin-top: 10px;  /* Adjust the margin-top to set the top margin of the button */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
        ''')

        # Set styles
        self.setStyleSheet("""
            QWidget {
                background-color: #141c4b;  /* Set your desired background color */
            }
            QLabel {
                color: #f0f1f1;
                font-size: 20px;
                margin-bottom: 20px;
            }
            QLineEdit {
                background-color: #6fa8b6;
                color: #f0f1f1;
                padding: 10px;
                border: 1px solid #2980b9;
                border-radius: 5px;
                font-size: 16px;
                margin-bottom: 10px;
            }
        """)

    def return_button_pressed(self):
        if not self.page_controller_object.is_logged_in:
            self.page_controller_object.n.cancel_current_process()
            self.page_controller_object.change_to_login_page()
        else:
            self.page_controller_object.n.cancel_current_process()
            self.page_controller_object.change_to_main_page()

    def submit_form(self):
        n = self.page_controller_object.n
        username = self.username.text()
        email = self.email.text()
        if is_email_valid(email) and len(username) > 0:
            n.send_username_and_email_froget_password(username, None, email)
            data = n.recv_str()
            message_type = data.get("message_type")
            if message_type == "forget_password":
                result = data.get("forget_password_status")
                if result == "valid":
                    print("Server send code to email")
                    self.page_controller_object.change_to_verification_code_page()
                elif result == "invalid":
                    pass

    def resend_code_clicked(self):
        print(4)


class VerificationCodePage(QWidget):
    def __init__(self, page_controller_object):
        super().__init__()
        self.page_controller_object = page_controller_object
        self.init_ui()
        self.info_label = QLabel(self)
        pixmap = QPixmap('discord_app_assets/info_icon.png')  # Replace with the path to your 'i' icon
        width, height = (
        int(self.page_controller_object.screen_width * 0.02), int(self.page_controller_object.screen_height * 0.037))
        scaled_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio)
        self.info_label.setPixmap(scaled_pixmap)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("background-color: #141c4b; border-radius: 25px;")
        self.info_label.setToolTip('A mail will be sent to your chosen email address')
        info_label_x, info_label_y = (
        int(self.page_controller_object.screen_width * 0.468), int(self.page_controller_object.screen_height * 0.245))

        self.info_label.move(info_label_x, info_label_y)
        self.info_label.setMouseTracking(True)
        self.info_label.installEventFilter(self)
        self.code = QLineEdit(self)
        self.code.setMaxLength(6)
        self.code.setValidator(QIntValidator())

        # Set placeholder text and color

        self.code.setPlaceholderText("code")
        self.code.setStyleSheet("color: white;")
        code_x, code_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.296))

        self.code.move(code_x, code_y)

        successfully_signed_up_x, successfully_signed_up_y = (
        int(self.page_controller_object.screen_width * 0.4427), int(self.page_controller_object.screen_height * 0.5))

        self.successfully_signed_up = self.create_label("successfully signed up",
                                                        (successfully_signed_up_x, successfully_signed_up_y))
        self.successfully_signed_up.hide()

        image_button = QPushButton(self)
        # Load an image and set it as the button's icon
        icon = QIcon("discord_app_assets/right-arrow-icon-27.png")
        image_button.setIcon(icon)
        width, height = int(self.page_controller_object.screen_width * 0.01), int(
            self.page_controller_object.screen_height * 0.018)

        icon_size = QSize(width, height)  # Set your desired size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
        image_button.setIconSize(scaled_size)
        image_button_x, image_button_y = (
        int(self.page_controller_object.screen_width * 0.471), int(self.page_controller_object.screen_height * 0.217))

        image_button.move(image_button_x, image_button_y)
        image_button.clicked.connect(self.return_button_pressed)

        self.label = QLabel("5:00", self)
        label_x, label_y = (
        int(self.page_controller_object.screen_width * 0.46875), int(self.page_controller_object.screen_height * 0.1851))
        self.label.move(label_x, label_y)
        self.label.setStyleSheet("font-size: 20px;")
        self.start_timer()

    def start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.time_left = QTime(0, 5, 0)  # 5 minutes

        self.timer.start(1000)  # Update every second

    def update_timer(self):
        self.time_left = self.time_left.addSecs(-1)
        self.label.setText(self.time_left.toString("m:ss"))

        if self.time_left == QTime(0, 0, 0):
            self.timer.stop()

    def return_button_pressed(self):
        if not self.page_controller_object.is_logged_in:
            self.page_controller_object.n.cancel_current_process()
            self.page_controller_object.change_to_login_page()
        else:
            self.page_controller_object.n.cancel_current_process()
            self.page_controller_object.change_to_main_page()

    def eventFilter(self, obj, event):
        try:
            if obj == self.info_label and event.type() == event.Enter:
                # Set a fixed position for the tooltip
                xpos = int(self.page_controller_object.screen_width * 0.416)
                ypos = int(self.page_controller_object.screen_height * 0.277)
                fixed_position = QPoint(xpos, ypos)
                QToolTip.showText(fixed_position, self.info_label.toolTip())
                return True  # Consume the event to prevent further processing
            return super().eventFilter(obj, event)
        except Exception as e:
            print(f"error in eventFilter {e}")

    def create_label(self, text, position):
        label = QLabel(text, self)
        label.setStyleSheet("color: green; font-size: 12px;")
        label.move(position[0], position[1])
        label.hide()
        return label

    def init_ui(self):
        label = QLabel("Verification code", self)
        code_label = QLabel('<a href="resend">Resend code</a>', self)
        code_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        code_label.setOpenExternalLinks(False)  # Disable external links to capture linkActivated signal
        code_label.setStyleSheet("color: blue; font-size: 15px;")  # Set the text color to blue and font size to 12px

        # Connect the linkActivated signal to a custom slot
        code_label.linkActivated.connect(self.resend_code_clicked)
        code_label_x, code_label_y = (
        int(self.page_controller_object.screen_width * 0.46), int(self.page_controller_object.screen_height * 0.3496))

        code_label.move(code_label_x, code_label_y)

        label_x, label_y = (
        int(self.page_controller_object.screen_width * 0.438), int(self.page_controller_object.screen_height * 0.146))

        label.move(label_x, label_y)

        # Create button
        submit_button = QPushButton('Submit code', self)
        submit_button.clicked.connect(self.submit_form)
        submit_button_x, submit_button_y = (
        int(self.page_controller_object.screen_width * 0.43), int(self.page_controller_object.screen_height * 0.376))


        width, height = (
        int(self.page_controller_object.screen_width * 0.1041667), int(self.page_controller_object.screen_height * 0.05555))
        submit_button.setGeometry(submit_button_x, submit_button_y, width, height)
        # Set styles
        self.setStyleSheet("""
            QWidget {
                background-color: #141c4b;  /* Set your desired background color */
            }
            QLabel {
                color: #f0f1f1;
                font-size: 20px;
                margin-bottom: 20px;
            }
            QLineEdit {
                background-color: #6fa8b6;
                color: #f0f1f1;
                padding: 10px;
                border: 1px solid #2980b9;
                border-radius: 5px;
                font-size: 16px;
                margin-bottom: 10px;
            }
        """)

        submit_button.setStyleSheet('''
            QPushButton {
                background-color: #6fa8b6;
                color: #f0f1f1;
                border: 1px solid #2980b9;
                border-radius: 5px;
                font-size: 16px;  /* Set your desired font size */
                margin-top: 10px;  /* Adjust the margin-top to set the top margin of the button */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
        ''')

    def submit_form(self):
        expected_types_list = ["sign_up", "forget_password", "2fa"]
        n = self.page_controller_object.n
        code = self.code.text()
        try:
            if self.time_left != QTime(0, 0, 0):
                if len(code) == 6:
                    if not self.page_controller_object.is_waiting_for_2fa_code:
                        n.send_sign_up_verification_code(code)
                    else:
                        n.send_login_2fa_code(code)
                    print("Sent verification code to server")
                    while True:
                        data = n.recv_str()
                        message_type = data.get("message_type")
                        if message_type in expected_types_list:
                            self.handle_data(data, n)
                            break
                        else:
                            self.page_controller_object.handle_tcp_data(data)
        except Exception as e:
            print(f"error in submit_form verification code {e}")

    def handle_data(self, data, n):
        message_type = data.get("message_type")
        if message_type == "sign_up":
            kind = data.get("action")
            if kind == "code":
                result = data.get("code_status")
                if result == "valid":
                    print("Server got the code")
                    self.successfully_signed_up.show()
                    self.image_button.show()
                elif result == "invalid":
                    pass
        elif message_type == "forget_password":
            kind = data.get("action")
            result = data.get("code_status")
            if kind == "code":
                if result == "valid":
                    self.page_controller_object.change_to_change_password_page()
                elif result == "invalid":
                    pass
        elif message_type == "2fa":
            try:
                kind = data.get("action")
                result = data.get("code_status")
                if kind == "code":
                    if result == "valid":
                        print("logged in successfully")
                        n.connect_between_udp_port_address_to_username()
                        if self.page_controller_object.login_page.remember_me_status:
                            n.ask_for_security_token()
                            print("You will be remembered")
                        try:
                            self.page_controller_object.main_page.username = self.page_controller_object.login_page.username_entry.text()
                            self.page_controller_object.main_page.update_values()
                            self.page_controller_object.is_logged_in = True
                            self.page_controller_object.start_receive_thread_after_login()
                            self.page_controller_object.main_page.start_listen_udp_thread()
                            self.page_controller_object.change_to_splash_page()
                        except Exception as e:
                            print(f"error in 2fa {e}")
                    elif result == "invalid":
                        pass
            except Exception as e:
                print(f"error in 2fa {e}")

    def resend_code_clicked(self, link):
        if self.time_left != QTime(0, 0, 0):
            if link == "resend":
                self.page_controller_object.n.ask_for_resend_code_to_email()
                print("asked for a resend of the code")


class ChangePasswordPage(QWidget):
    def __init__(self, page_controller_object):
        super().__init__()
        self.page_controller_object = page_controller_object
        self.init_ui()
        self.change_password_label = QLabel("Change password:", self)
        change_password_label_x, change_password_label_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.185))
        self.change_password_label.move(change_password_label_x, change_password_label_y)
        self.new_password = QLineEdit(self)
        new_password_x, new_password_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.26))

        self.new_password.move(new_password_x, new_password_y)
        self.new_password.setPlaceholderText("New password")
        self.new_password.setStyleSheet("color: white;")
        self.status = False
        self.image_button = QPushButton(self)
        # Load an image and set it as the button's icon
        icon = QIcon("discord_app_assets/right-arrow-icon-27.png")
        self.image_button.setIcon(icon)
        width, height = int(self.page_controller_object.screen_width * 0.01), int(
            self.page_controller_object.screen_height * 0.018)

        icon_size = QSize(width, height)  # Set your desired size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
        self.image_button.setIconSize(scaled_size)
        image_button_x, image_button_y = (
        int(self.page_controller_object.screen_width * 0.471), int(self.page_controller_object.screen_height * 0.217))

        self.image_button.move(image_button_x, image_button_y)

        self.image_button.clicked.connect(self.return_button_pressed)
        self.setStyleSheet("""
                QWidget {
                    background-color: #141c4b;  /* Set your desired background color */
                }
                QLabel {
                    color: #f0f1f1;
                    font-size: 20px;
                    margin-bottom: 20px;
                }
                QLineEdit {
                    background-color: #6fa8b6;
                    color: #f0f1f1;
                    padding: 10px;
                    border: 1px solid #2980b9;
                    border-radius: 5px;
                    font-size: 16px;
                    margin-bottom: 10px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1f618d;
                }
            """)

    def return_button_pressed(self):
        if not self.page_controller_object.is_logged_in:
            self.page_controller_object.n.cancel_current_process()
            self.page_controller_object.change_to_login_page()
        else:
            self.page_controller_object.n.cancel_current_process()
            self.page_controller_object.change_to_main_page()

    def create_label(self, text, position):
        label = QLabel(text, self)
        label.setStyleSheet("color: red; font-size: 12px;")
        label.move(position[0], position[1])
        label.hide()
        return label

    def init_ui(self):
        self.too_short = QLabel("Password too short", self)
        self.was_password_changed = False
        too_short_x, too_short_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.315))
        self.too_short.move(too_short_x, too_short_y)
        self.too_short.hide()
        self.too_short.setStyleSheet(
            "color: red; font-size: 14px;")  # Set the text color to blue and font size to 12px

        self.password_already_changed = QLabel("Password already changed", self)
        password_already_changed_x, password_already_changed_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.314))

        self.password_already_changed.move(password_already_changed_x, password_already_changed_y)
        self.password_already_changed.hide()
        self.password_already_changed.setStyleSheet(
            "color: red; font-size: 14px;")  # Set the text color to blue and font size to 12px

        self.changed_password_label = QLabel("Password changed", self)
        changed_password_label_x, changed_password_label_y = (
        int(self.page_controller_object.screen_width * 0.44), int(self.page_controller_object.screen_height * 0.315))
        self.changed_password_label.move(changed_password_label_x, changed_password_label_y)
        self.changed_password_label.hide()
        # Create button
        submit_button = QPushButton('Submit info', self)
        submit_button.clicked.connect(self.submit_form)
        submit_button_x, submit_button_y = (
        int(self.page_controller_object.screen_width * 0.42), int(self.page_controller_object.screen_height * 0.315))
        submit_button.move(submit_button_x, submit_button_y)
        submit_button.setStyleSheet('''
            QPushButton {
                background-color: #6fa8b6;
                color: #f0f1f1;
                padding: 10px;  /* Adjust the padding to make the button smaller */
                border: 1px solid #2980b9;
                border-radius: 5px;
                min-width: 200px;  /* Adjust the min-width to set the minimum width of the button */
                max-width: 300px;  /* Adjust the max-width to set the maximum width of the button */
                min-height: 30px;  /* Adjust the min-height to set the minimum height of the button */
                max-height: 60px;  /* Adjust the max-height to set the maximum height of the button */
                font-size: 16px;  /* Set your desired font size */
                margin-top: 10px;  /* Adjust the margin-top to set the top margin of the button */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
               QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
        ''')

        # Set styles
        self.setStyleSheet("""
            QWidget {
                background-color: #141c4b;  /* Set your desired background color */
            }
            QLabel {
                color: #f0f1f1;
                font-size: 20px;
                margin-bottom: 20px;
            }
            QLineEdit {
                background-color: #6fa8b6;
                color: #f0f1f1;
                padding: 10px;
                border: 1px solid #2980b9;
                border-radius: 5px;
                font-size: 16px;
                margin-bottom: 10px;
            }
        """)

    def submit_form(self):
        n = self.page_controller_object.n
        self.too_short.hide()
        self.password_already_changed.hide()
        self.changed_password_label.hide()
        if len(self.new_password.text()) >= 8 and not self.was_password_changed and is_valid_password(self.new_password.text()):
            n.send_new_password(self.new_password.text())
            print("Password changed")
            self.changed_password_label.show()
            self.status = True
            self.was_password_changed = True
            if self.page_controller_object.is_tcp_receive_thread_paused:
                self.page_controller_object.is_tcp_receive_thread_paused = False
                self.page_controller_object.update_receive_thread_after_login()
                self.page_controller_object.start_receive_thread_after_login()
        elif self.was_password_changed:
            self.password_already_changed.show()
        else:
            self.too_short.show()


class ServerIsDownPage(QWidget):
    def __init__(self, page_controller_object):
        try:
            super().__init__()
            self.page_controller_object = page_controller_object

            server_is_offline_x, server_is_offline_y = (int(self.page_controller_object.screen_width * 0.44),
                                                        int(self.page_controller_object.screen_height * 0.185))
            self.server_is_offline = QLabel("Failed to connect Server...", self)

            self.server_is_offline.move(server_is_offline_x, server_is_offline_y)
            self.server_is_offline.setStyleSheet("color: white; font-size:20px")
            self.setStyleSheet("""
                QWidget {
                    background-color: #141c4b;  /* Set your desired background color */
                }
            """)

            reconnect_button_x, reconnect_button_y = (int(self.page_controller_object.screen_width * 0.44),
                                                        int(self.page_controller_object.screen_height * 0.285))
            reconnect_button = QPushButton("reconnect to server", self)
            reconnect_button.clicked.connect(self.page_controller_object.try_reconnect_to_server)
            reconnect_button.move(reconnect_button_x, reconnect_button_y)
            reconnect_button.setStyleSheet('''
                QPushButton {
                    background-color: #6fa8b6;
                    color: #f0f1f1;
                    border: 1px solid #2980b9;
                    border-radius: 5px;
                    font-size: 16px;  /* Set your desired font size */
                    margin-top: 10px;  /* Adjust the margin-top to set the top margin of the button */
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1f618d;
            ''')
        except Exception as e:
            print("error in server id down page")


class SlowDown(QWidget):
    def __init__(self, status):
        super().__init__()
        self.status = status
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Popup Example')
        self.show_slow_down()

    def show_slow_down(self):
        if self.status == "invalid":
            QMessageBox.information(self, 'Slow Down Your Requests',
                                    "Your requests are being delayed. Press OK to continue.", QMessageBox.Ok)
        else:
            QMessageBox.warning(self, 'Warned By Server',
                                    "By keeping overflowing the server you will be kicked", QMessageBox.Ok)


class PageController:
    def __init__(self):
        self.n = ClientNet(self)
        self.is_tcp_receive_thread_paused = False
        self.is_closing_app = False
        self.is_changing_password = False
        is_connected = self.n.connect_tcp()
        self.screen_width, self.screen_height = pyautogui.size()
        self.app = QApplication(sys.argv)
        self.current_page = None
        if is_connected:
            try:
                self.receive_thread_after_login = threading.Thread(target=self.thread_recv_messages, args=())
                self.is_logged_in = False
                self.is_waiting_for_2fa_code = False
                self.splash_page = SplashScreen(self)
                self.splash_page.showMaximized()
                self.sign_up_page = SignUpPage(self)
                self.forget_password_page = ForgetPasswordPage(self)
                self.login_page = LoginPage(self)
                self.main_page = MainPage(self.n, self)
                self.change_password_page = ChangePasswordPage(self)
                self.verification_code_page = VerificationCodePage(self)
                self.main_page.showMaximized()
                self.main_page.hide()
                self.sign_up_page.showMaximized()
                self.forget_password_page.showMaximized()
                self.login_page.showMaximized()
                self.login_page.hide()
                self.verification_code_page.showMaximized()
                self.sign_up_page.hide()
                self.forget_password_page.hide()
                self.verification_code_page.hide()
                self.change_password_page.showMaximized()
                self.change_password_page.hide()
                self.current_page = self.login_page
            except Exception as e:
                print(e)
        else:
            self.main_page = MainPage(self.n, self)
            self.server_is_down_page = ServerIsDownPage(self)
            self.current_page = self.server_is_down_page
            self.server_is_down_page.showMaximized()
        self.app.exec_()

    def try_reconnect_to_server(self):
        try:
            self.n.close()
            is_connected = self.n.connect_tcp()
            if is_connected:
                self.main_page = MainPage(self.n, self)
                self.receive_thread_after_login = threading.Thread(target=self.thread_recv_messages, args=())
                self.is_logged_in = False
                self.is_waiting_for_2fa_code = False
                self.change_to_login_page()
            else:
                print("tried reconnecting but server still offline")
        except Exception as e:
            print(e)

    def lost_connection_with_server(self):
        try:
            self.n.reset_vars()
            self.receive_thread_after_login = threading.Thread(target=self.thread_recv_messages, args=())
            self.is_logged_in = False
            self.is_waiting_for_2fa_code = False
            self.change_to_server_is_down()
        except Exception as e:
            print(f"error in lost connection {e}")

    def update_receive_thread_after_login(self):
        self.receive_thread_after_login = threading.Thread(target=self.thread_recv_messages, args=())

    def start_receive_thread_after_login(self):
        self.receive_thread_after_login.start()

    def quit_application(self):
        try:
            if self.is_logged_in and not self.is_changing_password:
                self.is_closing_app = True
                print("closing app...")
                self.is_logged_in = False
                self.n.close()
                self.current_page.close()
                self.main_page.close_all_threads()
                del self.app
                sys.exit()
            else:
                self.is_changing_password = False
        except Exception as e:
            print(e)

    def log_out(self):
        try:
            print("logging out")
            self.is_logged_in = False
            self.n.send_logout_message()
            self.main_page.close_all_threads()
            self.current_page.close()
            self.current_page = None
            self.receive_thread_after_login.join()
            self.receive_thread_after_login = threading.Thread(target=self.thread_recv_messages, args=())
            self.main_page = MainPage(self.n, self)
            self.change_to_login_page()
        except Exception as e:
            print(f"error in log out {e}")

    def clear_all_pages(self):
        try:
            self.splash_page = SplashScreen(self)
            self.sign_up_page = SignUpPage(self)
            self.forget_password_page = ForgetPasswordPage(self)
            self.login_page = LoginPage(self)
            self.main_page = MainPage(self.n, self)
            self.change_password_page = ChangePasswordPage(self)
            self.verification_code_page = VerificationCodePage(self)
        except Exception as e:
            print(f"error in clearing pages {e}")

    def close_all_pages(self):
        try:
            self.main_page.close()
            self.change_password_page.close()
            self.verification_code_page.close()
            self.login_page.close()
            self.forget_password_page.close()
            self.sign_up_page.close()
            self.splash_page.close()
        except Exception as e:
            print(f"error in closing pages {e}")

    def hide_all_pages(self):
        try:
            self.splash_page.hide()
            self.sign_up_page.hide()
            self.forget_password_page.hide()
            self.login_page.hide()
            self.main_page.hide()
            self.change_password_page.hide()
            self.verification_code_page.hide()
        except Exception as e:
            print(f"error in hiding pages {e}")

    def change_to_login_page(self):
        self.change_page("login_page")

    def change_to_sign_up_page(self):
        self.change_page("sign_up_page")

    def change_to_change_password_page(self):
        self.change_page("change_password_page")

    def change_to_verification_code_page(self):
        self.change_page("verification_code_page")

    def change_to_main_page(self):
        self.change_page("main_page")

    def change_to_forget_password_page(self):
        self.change_page("forget_password_page")

    def change_to_splash_page(self):
        self.change_page("splash_page")

    def change_to_server_is_down(self):
        self.change_page("server_is_down")

    def change_page(self, page_name):
        try:
            if self.current_page is not None:
                self.current_page.close()
            if page_name == "main_page":
                self.main_page.showMaximized()
                self.current_page = self.main_page
            elif page_name == "server_is_down":
                self.server_is_down_page = ServerIsDownPage(self)
                self.server_is_down_page.showMaximized()
                self.current_page = self.server_is_down_page
            elif page_name == "sign_up_page":
                self.sign_up_page = SignUpPage(self)
                self.sign_up_page.showMaximized()
                self.current_page = self.sign_up_page
            elif page_name == "change_password_page":
                self.change_password_page = ChangePasswordPage(self)
                self.change_password_page.showMaximized()
                self.current_page = self.change_password_page
            elif page_name == "verification_code_page":
                self.verification_code_page = VerificationCodePage(self)
                self.verification_code_page.showMaximized()
                self.current_page = self.verification_code_page
            elif page_name == "login_page":
                self.login_page = LoginPage(self)
                self.login_page.showMaximized()
                self.current_page = self.login_page
            elif page_name == "forget_password_page":
                self.forget_password_page = ForgetPasswordPage(self)
                self.forget_password_page.showMaximized()
                self.current_page = self.forget_password_page
            elif page_name == "splash_page":
                self.splash_page = SplashScreen(self)
                self.splash_page.showMaximized()
                self.current_page = self.splash_page
        except Exception as e:
            print(f"error in changing pages {e}")

    def thread_recv_messages(self):
        n = self.n
        print("receiving thread started running")
        while self.is_logged_in and not self.is_tcp_receive_thread_paused:
            data = n.recv_str()
            try:
                if data is not None:
                    self.handle_tcp_data(data)
                else:
                    print(f"got data {data}")
                    if not self.is_closing_app:
                        print("lost connection with server")
                        self.is_logged_in = False
                        # QMetaObject.invokeMethod(self.main_page, "lost_connection_with_server_signal",
                        #                          Qt.QueuedConnection)
                        break
            except Exception as e:
                print(f"error in receiving thread {e}")
        print("thread receive messages ended")

    def handle_tcp_data(self, data):
        message_type = data.get("message_type")
        if message_type == "messages_list":
            message_list = json.loads(data.get("messages_list"))
            self.main_page.list_messages = message_list
            self.main_page.is_new_chat_clicked = True
            self.main_page.is_messages_need_update = True
            QMetaObject.invokeMethod(self.main_page, "updated_chat_signal",
                                     Qt.QueuedConnection)
            print("Updated the messages list")
        elif message_type == "tcp_thread":
            action = data.get("action")
            if action == "pause":
                self.is_tcp_receive_thread_paused = True
            elif action == "unpause":
                self.is_tcp_receive_thread_paused = False
        elif message_type == "users_email":
            self.main_page.email = data.get("email")
            QMetaObject.invokeMethod(self.main_page, "updated_settings_signal",
                                     Qt.QueuedConnection)
        elif message_type == "settings_dict":
            settings_dict = data.get("settings_dict")
            self.main_page.update_settings_from_dict_signal.emit(settings_dict)
            print("got settings")
        elif message_type == "update_user_in_list":
            list_type = data.get("list_type")
            user_to_update = data.get("user_to_update")
            is_remove = data.get("is_remove")
            if list_type == "friends_list":
                if is_remove:
                    self.main_page.friends_list.remove(user_to_update)
                else:
                    if user_to_update not in self.main_page.friends_list:
                        self.main_page.friends_list.append(user_to_update)
            elif list_type == "requests_list":
                if is_remove:
                    self.main_page.request_list.remove(user_to_update)
                else:
                    if user_to_update not in self.main_page.request_list:
                        self.main_page.request_list.append(user_to_update)
            elif list_type == "blocked_list":
                if is_remove:
                    self.main_page.blocked_list.remove(user_to_update)
                else:
                    if user_to_update not in self.main_page.blocked_list:
                        self.main_page.blocked_list.append(user_to_update)
            QMetaObject.invokeMethod(self.main_page, "updated_social_page_signal",
                                     Qt.QueuedConnection)
            QMetaObject.invokeMethod(self.main_page, "update_chat_page_without_messages_signal",
                                     Qt.QueuedConnection)
        elif message_type == "playlist_current_song_bytes":
            audio_bytes = data.get("audio_bytes")
            title = data.get("title")
            play_mp3_from_bytes(audio_bytes, self.main_page.playlist_media_player)
            print(f"got song {title} bytes from server")
        elif message_type == "searched_song_result":
            info_dict = data.get("searched_song_dict")
            is_play = data.get("is_play")
            self.main_page.insert_search_result_signal.emit(info_dict, is_play)
            print("got song search info")
        elif message_type == "playlist_songs":
            playlist_songs_list = pickle.loads(data.get("playlist_songs_list"))
            self.main_page.playlist_songs = playlist_songs_list
            QMetaObject.invokeMethod(self.main_page, "insert_playlist_to_table_signal",
                                     Qt.QueuedConnection)
            print("got playlists songs")
        elif message_type == "message_list_addition":
            message_list_addition = json.loads(data.get("message_list_addition"))
            self.main_page.list_messages = self.main_page.list_messages + message_list_addition
            self.main_page.insert_messages_into_message_box_signal.emit(
                message_list_addition)
            self.main_page.scroll_back_to_index_before_update_signal.emit(
                len(message_list_addition))
        elif message_type == "new_message":
            chat = data.get("chat_name")
            if self.main_page.selected_chat == chat:
                message_dict = json.loads(data.get("message_dict"))
                self.main_page.list_messages.insert(0, message_dict)
                self.main_page.insert_new_message_in_chat_signal.emit(message_dict)
                self.main_page.chats_list.remove(chat)
                self.main_page.chats_list.insert(0, chat)
                print("got new message from current chat from {}")
            else:
                QMetaObject.invokeMethod(self.main_page, "new_message_play_audio_signal",
                                         Qt.QueuedConnection)
                print("got new message")
        elif message_type == "requests_list":
            requests_list = json.loads(data.get("requests_list"))
            self.main_page.request_list = requests_list
            QMetaObject.invokeMethod(self.main_page, "updated_social_page_signal",
                                     Qt.QueuedConnection)
            print("Updated the requests list")
        elif message_type == "vc_data":
            compressed_vc_data = data.get("compressed_vc_data")
            speaker = data.get("speaker")
            vc_data = zlib.decompress(compressed_vc_data)
            self.main_page.vc_data_list.append((vc_data, speaker))
        elif message_type == "share_screen_data":
            compressed_share_screen_data = data.get("compressed_share_screen_data")
            speaker = data.get("speaker")
            frame_shape = data.get("frame_shape")
            share_screen_data = zlib.decompress(compressed_share_screen_data)
            decompressed_frame = np.frombuffer(share_screen_data, dtype=np.uint8).reshape(frame_shape)
            self.main_page.update_stream_screen_frame(decompressed_frame)
        elif message_type == "share_camera_data":
            compressed_share_camera_data = data.get("compressed_share_camera_data")
            speaker = data.get("speaker")
            frame_shape = data.get("frame_shape")
            share_screen_data = zlib.decompress(compressed_share_camera_data)
            decompressed_frame = np.frombuffer(share_screen_data, dtype=np.uint8).reshape(frame_shape)
            self.main_page.update_stream_screen_frame(decompressed_frame)
        elif message_type == "friends_list":
            json_friends_list = data.get("friends_list")
            friends_list = json.loads(json_friends_list)
            self.main_page.friends_list = friends_list
            QMetaObject.invokeMethod(self.main_page, "updated_social_page_signal",
                                     Qt.QueuedConnection)
            QMetaObject.invokeMethod(self.main_page, "update_chat_page_without_messages_signal",
                                     Qt.QueuedConnection)
            print(f"Got friends list: {self.main_page.friends_list}")
            print("Updated friends_list list")
        elif message_type == "online_users_list":
            online_users_list = json.loads(data.get("online_users_list"))
            self.main_page.online_users_list = online_users_list
            QMetaObject.invokeMethod(self.main_page, "updated_social_page_signal",
                                     Qt.QueuedConnection)
            QMetaObject.invokeMethod(self.main_page, "update_chat_page_without_messages_signal",
                                     Qt.QueuedConnection)
            print(f"Got online users list: {online_users_list}")
        elif message_type == "blocked_list":
            blocked_list = json.loads(data.get("blocked_list"))
            self.main_page.blocked_list = blocked_list
            QMetaObject.invokeMethod(self.main_page, "updated_social_page_signal",
                                     Qt.QueuedConnection)
            print("Updated the requests list")
        elif message_type == "groups_list":
            groups_list = json.loads(data.get("groups_list"))
            self.main_page.groups_list = groups_list
            QMetaObject.invokeMethod(self.main_page, "update_chat_page_without_messages_signal",
                                     Qt.QueuedConnection)
            QMetaObject.invokeMethod(self.main_page,
                                     "caching_circular_images_of_groups_signal", Qt.QueuedConnection)
            print("Updated the Groups list")
        elif message_type == "chats_list":
            chats_list = json.loads(data.get("chats_list"))
            self.main_page.chats_list = chats_list
            QMetaObject.invokeMethod(self.main_page, "update_chat_page_without_messages_signal",
                                     Qt.QueuedConnection)
            print("Updated the chats list")
            print(f"chats list is: {self.main_page.chats_list}")
        elif message_type == "add_chat":
            new_chat = data.get("chat_to_add")
            self.main_page.chats_list.insert(0, new_chat)
            QMetaObject.invokeMethod(self.main_page, "update_chat_page_without_messages_signal",
                                     Qt.QueuedConnection)
            print("Updated the chats list")
            print(f"chats list is: {self.main_page.chats_list}")
        elif message_type == "new_group_dict":
            new_group_dict = json.loads(data.get("group_dict"))
            self.main_page.groups_list.append(new_group_dict)
            QMetaObject.invokeMethod(self.main_page, "update_chat_page_without_messages_signal",
                                     Qt.QueuedConnection)
            print("Added new group to group_list")
        elif message_type == "call":
            call_action_type = data.get("call_action_type")
            if call_action_type == "in_call_action":
                action = data.get("action")
                if action == "calling":
                    user_that_called = data.get("user_that_called")
                    if self.main_page.is_in_a_call or self.main_page.is_calling or self.main_page.is_getting_called:
                        print(f"User got a call but he is busy")
                    else:
                        try:
                            getting_called_by = user_that_called
                            print(f"User is called by {getting_called_by}")
                            self.main_page.is_getting_called = True
                            self.main_page.getting_called_by = getting_called_by
                            QMetaObject.invokeMethod(self.main_page,
                                                     "update_chat_page_without_messages_signal",
                                                     Qt.QueuedConnection)
                            QMetaObject.invokeMethod(self.main_page,
                                                     "getting_call_signal", Qt.QueuedConnection)
                        except Exception as e:
                            print(f"error in action calling error:{e}")
                if self.main_page.is_getting_called or self.main_page.is_calling or self.main_page.is_joining_call:
                    if action == "rejected":
                        print(f"call was rejected")
                        QMetaObject.invokeMethod(self.main_page, "stop_sound_signal",
                                                 Qt.QueuedConnection)
                        QMetaObject.invokeMethod(self.main_page, "reset_call_var_signal",
                                                 Qt.QueuedConnection)
                    if action == "accepted":
                        print(f"call was accepted")
                        QMetaObject.invokeMethod(self.main_page, "stop_sound_signal",
                                                 Qt.QueuedConnection)
                        QMetaObject.invokeMethod(self.main_page, "initiating_call_signal",
                                                 Qt.QueuedConnection)
                        QMetaObject.invokeMethod(self.main_page, "updated_chat_signal",
                                                 Qt.QueuedConnection)
                        QMetaObject.invokeMethod(self.main_page,
                                                 "start_call_threads_signal", Qt.QueuedConnection)
                    if action == "timeout":
                        print("call timeout passed")
                        QMetaObject.invokeMethod(self.main_page, "stop_sound_signal",
                                                 Qt.QueuedConnection)
                        QMetaObject.invokeMethod(self.main_page, "reset_call_var_signal",
                                                 Qt.QueuedConnection)
                if action == "ended":
                    print("call ended")
                    QMetaObject.invokeMethod(self.main_page, "close_call_threads_signal",
                                             Qt.QueuedConnection)
                    QMetaObject.invokeMethod(self.main_page, "reset_call_var_signal",
                                             Qt.QueuedConnection)
            if call_action_type == "call_dictionary":
                action = data.get("action")
                if action == "dict":
                    call_dictionary = data.get("dict")
                    print(f"got call dict {call_dictionary}")
                    call_dict = call_dictionary
                    if self.main_page.is_call_dict_exists_by_id(call_dict.get("call_id")):
                        self.main_page.update_call_dict_by_id(call_dict)
                        if self.main_page.is_watching_screen:
                            if self.main_page.username in call_dict.get("participants"):
                                if self.main_page.watching_type == "ScreenStream":
                                    if self.main_page.watching_user not in call_dict.get(
                                            "screen_streamers"):
                                        QMetaObject.invokeMethod(self.main_page,
                                                                 "stop_watching_stream_signal",
                                                                 Qt.QueuedConnection)
                                else:
                                    if self.main_page.watching_user not in call_dict.get(
                                            "camera_streamers"):
                                        QMetaObject.invokeMethod(self.main_page,
                                                                 "stop_watching_stream_signal",
                                                                 Qt.QueuedConnection)
                    else:
                        self.main_page.call_dicts.append(call_dict)
                    QMetaObject.invokeMethod(self.main_page, "update_chat_page_without_messages_signal",
                                             Qt.QueuedConnection)
                if action == "list_call_dicts":
                    list_call_dicts = json.loads(data.get("list_call_dicts"))
                    list_of_call_dicts = list_call_dicts
                    self.main_page.call_dicts = list_of_call_dicts
                    print(f"got list of call dicts: {list_of_call_dicts}")
            if call_action_type == "update_calls":
                action = data.get("action")
                if action == "remove_id":
                    id_to_remove = data.get("removed_id")
                    self.main_page.remove_call_dict_by_id(id_to_remove)
        elif message_type == "profile_dicts_list":
            profile_dicts_list = (data.get("profile_dicts_list"))
            print(profile_dicts_list)
            self.main_page.list_user_profile_dicts = profile_dicts_list
            QMetaObject.invokeMethod(self.main_page, "updated_settings_signal",
                                     Qt.QueuedConnection)
            QMetaObject.invokeMethod(self.main_page, "update_chat_page_without_messages_signal",
                                     Qt.QueuedConnection)
            QMetaObject.invokeMethod(self.main_page,
                                     "caching_circular_images_of_users_signal", Qt.QueuedConnection)
            print("got list of profile dictionaries")
        elif message_type == "updated_profile_dict":
            profile_dict = json.loads(data.get("profile_dict"))
            name_of_profile_dict = data.get("username")
            self.main_page.updating_profile_dict_signal.emit(name_of_profile_dict,
                                                             profile_dict)
            print(f"got updated profile dictionary of {name_of_profile_dict}")
        elif message_type == "status_changed":
            status = data.get("status")
            user = data.get("user")
            if status == "online":
                self.main_page.online_users_list.append(user)
            else:
                self.main_page.online_users_list.remove(user)
            QMetaObject.invokeMethod(self.main_page, "updated_social_page_signal",
                                     Qt.QueuedConnection)
        elif message_type == "requests_rate":
            try:
                status = data.get("status")
                if status == "invalid":
                    self.main_page.too_many_request_signal.emit(status)
                    print(f'got "too many requests per min" from server')
                elif status == "warned":
                    self.main_page.too_many_request_signal.emit(status)
                    print(f'got "warned" from server')
                elif status == "kicked":
                    print("got kicked from server")
                    self.main_page.quit_application_signal.emit()
            except Exception as e:
                print(e)
        elif message_type == "update_group_dict":
            group_dict = json.loads(data.get("group_dict"))
            self.main_page.update_group_lists_by_group.emit(group_dict)
            print(f"got updated group dic {group_dict.get('group_id')}")
        elif message_type == "data":
            action = data.get("action")
            if action == "receive":
                receive_status = data.get("receive_status")
                if receive_status == "done":
                    QMetaObject.invokeMethod(self.splash_page, "stop_loading_signal",
                                             Qt.QueuedConnection)
        elif message_type == "security_token":
            security_token = data.get("security_token")
            save_token(security_token)
        elif message_type == "friend_request":
            status = data.get("friend_request_status")
            if status == "not exist":
                self.main_page.friends_box.friend_not_found()
            elif status == "already friends":
                self.main_page.friends_box.request_was_friend()
            elif status == "worked":
                self.main_page.friends_box.request_was_sent()
            elif status == "active":
                self.main_page.friends_box.request_is_pending()


if __name__ == '__main__':
    page_controller_object = PageController()

