import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QIntValidator, QIcon, QImage
from PyQt5.QtCore import Qt, QSize, QPoint, QCoreApplication, QTimer, QMetaObject, Q_ARG, QObject, pyqtSignal,  QSettings, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from discord_comms_protocol import client_net
from chat_file import ChatBox, FriendsBox, SettingsBox
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
import struct
import re
from queue import Queue, Empty

email_providers = ["gmail", "outlook", "yahoo", "aol", "protonmail", "zoho", "mail", "fastmail", "gmx", "yandex", "mail.ru",
                   "tutanota", "icloud", "rackspace","mailchimp",

]
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy

def save_token(token):
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

Flag_recv_messages = True
vc_data_sequence = br'\vc_data'
share_screen_sequence = br'\share_screen_data'

def return_vc_bytes_parameters(vc_bytes):
    try:
        sequence_and_name = vc_bytes.split(b":")[0]
        encoded_name = sequence_and_name[len(vc_data_sequence):]
        compressed_vc_data = vc_bytes[len(sequence_and_name)+1:]
        name_of_talker = encoded_name.decode("utf-8")
        return name_of_talker, compressed_vc_data
    except Exception as e:
        print(vc_bytes)

def return_share_screen_bytes_parameters(share_screen_data):
    try:
        sequence_and_name = share_screen_data.split(b":")[0]
        frame_shape_bytes = share_screen_data.split(b":")[-1]
        encoded_name = sequence_and_name[len(share_screen_sequence):]
        compressed_share_screen_data = share_screen_data[len(sequence_and_name)+1:]
        name_of_talker = encoded_name.decode("utf-8")
        return name_of_talker, compressed_share_screen_data, frame_shape_bytes
    except Exception as e:
        print(share_screen_data)


def thread_recv_messages():
    global n, main_page, vc_thread_flag, vc_data_queue, vc_play_flag
    print("receiving thread started running")
    temp_count = 0
    while Flag_recv_messages:
        data = n.recv_str()
        if is_string(data):
            if data.startswith("error"):
                parts = data.split(":")
                if parts[1] == "disconnect":
                    print(f"lost connection with the server")
                    QMetaObject.invokeMethod(main_page, "disconnect_signal", Qt.QueuedConnection)
            if data == "new_message":
                QMetaObject.invokeMethod(main_page, "new_message_play_audio_signal", Qt.QueuedConnection)
                print("got new message")
            if data.startswith("security_token:"):
                security_token = data.split(":")[1]
                save_token(security_token)
            if data.startswith("messages_list:"):
                try:
                    temp = data.split("messages_list:", 1)[1]
                    main_page.list_messages = json.loads(temp)
                    QMetaObject.invokeMethod(main_page, "updated_chat_signal", Qt.QueuedConnection)
                    print("Updated the messages list")
                except Exception as e:
                    print(f"error in messages_list {e}")
            if data.startswith("groups_list:"):
                try:
                    temp = data.split("groups_list:", 1)[1]
                    main_page.groups_list = json.loads(temp)
                    QMetaObject.invokeMethod(main_page, "updated_chat_signal", Qt.QueuedConnection)
                    print("Updated the Groups list")
                except Exception as e:
                    print(f"error in groups_list {e}")
            if data.startswith("chats_list:"):
                try:
                    temp = data.split("chats_list:", 1)[1]
                    main_page.chats_list = json.loads(temp)
                    QMetaObject.invokeMethod(main_page, "updated_chat_signal", Qt.QueuedConnection)
                    print("Updated the chats list")
                    print(f"chats list is: {main_page.chats_list}")
                except Exception as e:
                    print(f"error in chats_list {e}")
            if data.startswith('list_status:'):
                print(f"got ({data}) from server")
            if data.startswith("friend_request:"):
                print(f"got ({data}) from server")
                parts = data.split(":")
                status = parts[1]
                if status == "not exist":
                    main_page.friends_box.friend_not_found()
                elif status == "already friends":
                    main_page.friends_box.request_was_friend()
                elif status == "worked":
                    main_page.friends_box.request_was_sent()
                elif status == "active":
                    main_page.friends_box.request_is_pending()
            if data.startswith("requests_list:"):
                try:
                    request_list = data.split("requests_list:", 1)[1]
                    main_page.request_list = json.loads(request_list)
                    QMetaObject.invokeMethod(main_page, "updated_requests_signal", Qt.QueuedConnection)
                    print("Updated the requests list")
                except Exception as e:
                    print(f"error in requests_list {e}")
            if data.startswith("online_users"):
                try:
                    online_users_list = data.split("online_users:", 1)[1]
                    online_users_list = json.loads(online_users_list)
                    main_page.online_users_list = online_users_list
                    QMetaObject.invokeMethod(main_page, "updated_requests_signal", Qt.QueuedConnection)
                    QMetaObject.invokeMethod(main_page, "updated_chat_signal", Qt.QueuedConnection)
                    print(f"Got online users list: {online_users_list}")
                except Exception as e:
                    print(f"error in online_users error:{e}")
            if data.startswith("friends_list:"):
                try:
                    friends_list = data.split("friends_list:", 1)[1]
                    main_page.friends_list = json.loads(friends_list)
                    #if main_page.chat_box.chat_name_label.text() == "" and len(friends_list) > 0:
                        #main_page.chat_box.selected_chat_changed(main_page.friends_list[0])
                    QMetaObject.invokeMethod(main_page, "updated_requests_signal", Qt.QueuedConnection)
                    QMetaObject.invokeMethod(main_page, "updated_chat_signal", Qt.QueuedConnection)
                    print(f"Got friends list: {main_page.friends_list}")
                    print("Updated friends_list list")
                except Exception as e:
                    print(f"error in got friends_list:{e}")
            if data.startswith("call"):
                parts = data.split(':')
                action = parts[1]
                if action == "calling":
                    if main_page.is_in_a_call or main_page.is_calling or main_page.is_getting_called:
                        print(f"User got a call but he is busy")
                    else:
                        try:
                            getting_called_by = parts[2]
                            print(f"User is called by {getting_called_by}")
                            main_page.is_getting_called = True
                            main_page.getting_called_by = getting_called_by
                            QMetaObject.invokeMethod(main_page, "updated_chat_signal", Qt.QueuedConnection)
                            QMetaObject.invokeMethod(main_page, "getting_call_signal", Qt.QueuedConnection)
                        except Exception as e:
                            print(f"error in action calling error:{e}")
                if main_page.is_getting_called or main_page.is_calling or main_page.is_joining_call:
                    if action == "rejected":
                        print(f"call was rejected")
                        QMetaObject.invokeMethod(main_page, "stop_sound_signal", Qt.QueuedConnection)
                        QMetaObject.invokeMethod(main_page, "reset_call_var_signal", Qt.QueuedConnection)
                    if action == "accepted":
                        print(f"call was accepted")
                        QMetaObject.invokeMethod(main_page, "stop_sound_signal", Qt.QueuedConnection)
                        QMetaObject.invokeMethod(main_page, "initiating_call_signal", Qt.QueuedConnection)
                        QMetaObject.invokeMethod(main_page, "updated_chat_signal", Qt.QueuedConnection)
                        vc_thread_flag = True
                        vc_play_flag = True
                        send_vc_thread = threading.Thread(target=thread_send_voice_chat_data, args=())
                        recv_vc_data = threading.Thread(target=thread_play_vc_data, args=())
                        send_vc_thread.start()
                        recv_vc_data.start()
                    if action == "timeout":
                        print("call timeout passed")
                        QMetaObject.invokeMethod(main_page, "stop_sound_signal", Qt.QueuedConnection)
                        QMetaObject.invokeMethod(main_page, "reset_call_var_signal", Qt.QueuedConnection)
                if action == "ended":
                    print("call ended")
                    vc_data_queue = Queue()
                    vc_thread_flag = False
                    vc_play_flag = False
                    send_vc_thread.join()
                    recv_vc_data.join()
                    QMetaObject.invokeMethod(main_page, "reset_call_var_signal", Qt.QueuedConnection)
                if action == "dict":
                    second_colon_index = data.find(':', data.find(':') + 1)
                    json_str = data[second_colon_index + 1:].strip()
                    call_dict = json.loads(json_str)
                    if main_page.is_call_dict_exists_by_id(call_dict.get("call_id")):
                        main_page.update_call_dict_by_id(call_dict)
                        if main_page.is_watching_screen:
                            if main_page.username in call_dict.get("participants"):
                                if main_page.watching_type == "ScreenStream":
                                    if main_page.watching_user not in call_dict.get("screen_streamers"):
                                        QMetaObject.invokeMethod(main_page, "stop_watching_stream_signal", Qt.QueuedConnection)
                                else:
                                    if main_page.watching_user not in call_dict.get("camera_streamers"):
                                        QMetaObject.invokeMethod(main_page, "stop_watching_stream_signal",
                                                                 Qt.QueuedConnection)
                    else:
                        main_page.call_dicts.append(call_dict)
                    QMetaObject.invokeMethod(main_page, "updated_chat_signal", Qt.QueuedConnection)
                    print("got call dict from server")
                    print(call_dict)
                if action == "list_call_dicts":
                    second_colon_index = data.find(':', data.find(':') + 1)
                    list_of_call_dicts = json.loads(data[second_colon_index + 1:].strip())
                    main_page.call_dicts = list_of_call_dicts
                    print(f"got list of call dicts: {list_of_call_dicts}")
                if action == "remove_id":
                    call_id_to_remove = parts[2]
                    main_page.remove_call_dict_by_id(call_id_to_remove)
        else:
            try:
                if data.startswith(vc_data_sequence):
                    speaker, compressed_vc_data = return_vc_bytes_parameters(data)
                    vc_data = zlib.decompress(compressed_vc_data)
                    vc_data_queue.put(vc_data)
                elif data.startswith(share_screen_sequence):
                    streamer, compressed_share_screen_data, frame_shape_bytes = return_share_screen_bytes_parameters(data)
                    frame_shape = struct.unpack('III', frame_shape_bytes)
                    share_screen_data = zlib.decompress(compressed_share_screen_data)
                    decompressed_frame = np.frombuffer(share_screen_data, dtype=np.uint8).reshape(frame_shape)
                    main_page.update_stream_screen_frame(decompressed_frame)
            except Exception as e:
                print(f"error in getting byte data:{e}")



flag_updates = True

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
p = pyaudio.PyAudio()
vc_thread_flag = False
vc_play_flag = False
accumulated_data = []
vc_data_queue = Queue()

def thread_play_vc_data():
    global vc_data_queue
    output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
    while vc_play_flag:
        try:
            vc_data = vc_data_queue.get(block=True, timeout=1)

            output_stream.write(vc_data)
        except Empty:
            pass  # Handle the case where the queue is empty
    output_stream.stop_stream()
    output_stream.close()

def thread_send_voice_chat_data():
    global n, main_page
    accumulated_data = []
    print("started voice chat thread....")
    input_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    count = 0
    const = 20
    # Open output stream (speakers)
    while vc_thread_flag:
        if not main_page.mute and not main_page.deafen:
            input_data = input_stream.read(CHUNK)
            accumulated_data.append(input_data)

            count += 1
            if count % const == 0:  # Send every 10 chunks (adjust as needed)
                # Send the accumulated data over the network

                data = b''.join(accumulated_data)
                # output_stream.write(data)

                n.send_vc_data(data)
                accumulated_data = []  # Reset accumulated data
        else:
            time.sleep(0.1)
    input_stream.stop_stream()
    input_stream.close()
    print("stopped voice chat thread....")

def thread_send_share_screen_data():
    global main_page
    try:
        while main_page.is_screen_shared:
            # Capture the screen using PyAutoGUI
            screen = pyautogui.screenshot()

            # Convert the screenshot to a NumPy array
            frame = np.array(screen)
            frame_bytes = frame.tobytes()
            # Send the frame to the server
            n.send_share_screen_data(frame_bytes, frame.shape)

            time.sleep(0.04)  # Adjust the sleep time based on your needs
        print("send share screen data thread closed")
    except Exception as e:
        print(f"Screen sharing error: {e}")

def thread_send_share_camera_data():
    global main_page
    try:
        # Initialize the camera
        cap = cv2.VideoCapture(0)  # Use 0 for default camera, change as needed

        while main_page.is_camera_shared:
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
            n.send_share_screen_data(frame_bytes, frame_np.shape)

            time.sleep(0.04)  # Adjust the sleep time based on your needs

        # Release the camera and close thread
        cap.release()
        print("send share camera data thread closed")
    except Exception as e:
        print(f"Camera sharing error: {e}")


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Set window properties
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
        logo_label.setPixmap(QPixmap('discord_app_assets/connectify_icon.png'))  # Replace with the actual path to your PNG file
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.move(1690//2, 300)

        # Create loading label
        loading_label = QLabel('Loading...', self)
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setObjectName('loading_label')
        loading_label.move(1690//2+55, 460)

        # Set up dot counter
        self.dot_count = 0

        # Create timer to update loading dots
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.update_loading_dots)
        self.loading_timer.start(400)  # Update every 500 milliseconds

        # Set up elapsed time variable
        self.elapsed_time = 0

        # Show the splash screen
        self.show()

    def update_loading_dots(self):
        global is_logged_in, main_page, n
        wait_time_sec = 5
        self.dot_count = (self.dot_count + 1) % 5
        loading_label = self.findChild(QLabel, 'loading_label')
        loading_label.setText('Loading' + '.' * self.dot_count)
        loading_label.adjustSize()

        # Increment elapsed time
        self.elapsed_time += 500  # Timer interval is 500 milliseconds

        if self.elapsed_time >= wait_time_sec*1000:  # 5 seconds
            # Transition to the login page after 5 seconds
            if not are_token_saved():
                self.loading_timer.stop()
                login_page.showMaximized()
                self.close()
            else:
                security_token = get_saved_token()
                n.send_security_token(security_token)
                data = n.recv_str()
                if data.startswith("security_token"):
                    parts = data.split(":")
                    server_answer = parts[1]
                    if server_answer == "valid":
                        data = n.recv_str()
                        if data.startswith("username"):
                            parts = data.split(":")
                            username, action, action_state = parts[1], parts[2], parts[3]
                            username = data.split(":")[1]
                            if action == "login":
                                if action_state == "valid":
                                    self.loading_timer.stop()
                                    print("logged in successfully")
                                    self.hide()
                                    main_page.username = username
                                    main_page.update_values()
                                    main_page.showMaximized()
                                    is_logged_in = True
                                    threading.Thread(target=thread_recv_messages, args=()).start()
                                    self.close()
                                elif action_state == "invalid":
                                    print("username already logged in")
                    elif server_answer == "invalid":
                        print("security token isn't valid")
                        self.loading_timer.stop()
                        login_page.showMaximized()
                        self.close()

chat_clicked = True
social_clicked = False
setting_clicked = False
friends_list = []
list_last_messages = []
chat_messages_max = 33




request_list = []
is_logged_in = False

class MainPage(QWidget): # main page doesnt know when chat is changed...
    updated_chat_signal = pyqtSignal()
    updated_requests_signal = pyqtSignal()
    getting_call_signal = pyqtSignal()
    stop_sound_signal = pyqtSignal()
    initiating_call_signal = pyqtSignal()
    reset_call_var_signal = pyqtSignal()
    new_message_play_audio_signal = pyqtSignal()
    disconnect_signal = pyqtSignal()
    stop_watching_stream_signal = pyqtSignal()
    def __init__(self, Netwrok):
        super().__init__()
        self.background_color = "#141c4b"
        self.standard_hover_color = "#2980b9"
        self.color_design_options = ["Red", "Blue", "Black and White", "Green"]

        self.is_create_group_pressed = False
        self.is_rename_group_pressed = False
        self.is_add_users_to_group_pressed = False

        self.size_error_label = False
        self.is_chat_box_full = False
        self.is_friends_box_full = False
        self.is_last_message_on_screen = False
        self.list_messages = []
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

        self.mute = False
        self.deafen = False

        self.selected_settings = "My Account"
        self.is_push_to_talk = False
        self.push_to_talk_key = None
        self.is_editing_push_to_talk_button = False
        self.profile_pic = None

        self.volume = 50
        self.font_size = 12

        self.online_users_list = []
        self.friends_list = []
        # friend_box_page could be online, add friend, blocked, all, pending
        self.friends_box_page = "online"
        self.chats_list = []
        self.image_to_send = None
        self.image_file_name = ""
        self.chat_start_index = 0
        self.Network = Netwrok
        self.chat_box_chats_index = 0
        self.chat_box_index_y_start = 100

        self.friends_box_index = 0
        self.friends_box_index_y_start = 100
        self.current_friends_box_search = False

        self.selected_group_members = []
        self.create_group_index = 0
        self.add_users_to_group_index = 0
        self.group_max_members = 10

        self.blocked_list = []
        self.groups_list = []

        self.is_screen_shared = False
        self.is_watching_screen = False
        self.watching_user = ""
        self.watching_type = None
        self.is_camera_shared = False


        self.chat_start_index_max = float('inf')
        self.current_chat_box_search = False
        self.temp_search_list = []
        self.spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updated_chat_signal.connect(self.updated_chat)
        self.updated_requests_signal.connect(self.updated_requests)
        self.getting_call_signal.connect(self.getting_a_call)
        self.stop_sound_signal.connect(self.stop_sound)
        self.initiating_call_signal.connect(self.initiate_call)
        self.reset_call_var_signal.connect(self.reset_call_var)
        self.new_message_play_audio_signal.connect(self.new_message_play_audio)
        self.stop_watching_stream_signal.connect(self.stop_watching_video_stream)
        self.disconnect_signal.connect(self.quit_application)
        self.media_player = QMediaPlayer()
        self.media_player.stateChanged.connect(self.handle_state_changed)
        self.media_player.setVolume(70)
        self.ringtone = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Getting_called_sound_effect.mp3'))
        self.new_message_audio = QMediaContent(QUrl.fromLocalFile('discord_app_assets/new_message_sound_effect.mp3'))
        self.media_player.setMedia(self.ringtone)
        self.send_share_screen_thread = threading.Thread(target=thread_send_share_screen_data, args=())
        self.send_camera_data_thread = threading.Thread(target=thread_send_share_camera_data, args=())
        self.init_ui()


    def init_ui(self):
        global n
        # Set up the main window
        try:
            self.setGeometry(100, 100, 600, 400)
            self.setWindowTitle('Main Page')
            self.setStyleSheet(f'''
                QWidget {{
                    background-color: {self.background_color};
                }}
            ''')

            # Create an instance of ChatBox
            if chat_clicked:
                self.chat_box = ChatBox(self.selected_chat, self.list_messages, self.friends_list, parent=self, Network=n)   # Set the parent widget


            # Create layouts
            buttons_layout = QHBoxLayout()
            self.main_layout = QVBoxLayout(self)
            self.main_layout.addSpacing(30)
            self.main_layout.addLayout(buttons_layout)

            self.friends_box = FriendsBox(friends_list=self.friends_list,
                                          requests_list=self.request_list, Network=n, username=self.username, parent=self)
            self.friends_box.hide()

            self.settings_box = SettingsBox(parent=self)
            self.settings_box.hide()
            # Add some spacing between buttons and ChatBox

            # Add the ChatBox to the main layout
            self.stacked_widget = QStackedWidget(self)
            self.stacked_widget.addWidget(self.chat_box)
            self.stacked_widget.addWidget(self.settings_box)  # Placeholder for the Settings page
            self.stacked_widget.addWidget(self.friends_box)

            self.main_layout.addWidget(self.stacked_widget)

            # Set the layout
            self.setLayout(self.main_layout)
        except Exception as e:
            print(f"Error is: {e}")

    def start_share_screen_send_thread(self):
        self.send_share_screen_thread.start()
        print("Started Share screen thread")

    def start_camera_data_thread(self):
        self.send_camera_data_thread.start()
        print("Started Share camera thread")

    def update_share_screen_thread(self):
        self.send_share_screen_thread = threading.Thread(target=thread_send_share_screen_data, args=())

    def update_share_camera_thread(self):
        self.send_camera_data_thread = threading.Thread(target=thread_send_share_camera_data, args=())

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
        self.stream_screen = VideoClient()
        self.hide()
        self.stream_screen.showMaximized()

    def get_group_manager_by_group_id(self, id):
        for group_dict in self.groups_list:
            if group_dict["group_id"] == id:
                return group_dict.get("group_manager")
        else:
            return None

    def is_call_dict_exist_by_group_id(self, group_id):
        for call_dict in self.call_dicts:
            if call_dict.get("is_group_call"):
                if call_dict.get("group_id") == group_id:
                    return True
        return False

    def get_number_of_members_by_group_id(self, group_id):
        group_id = int(group_id)
        for group in self.groups_list:
            if group["group_id"] == group_id:
                return len(group["group_members"])
        return 0  # Return 0 if the group ID is not found

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
                        self.play_sound(join_sound)
                elif len(updated_participants) < len(participants_before) and self.username in updated_participants:
                    user_left_sound = QMediaContent(QUrl.fromLocalFile('discord_app_assets/leave_call_sound_effect.mp3'))
                    self.play_sound(user_left_sound)
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

    def parse_group_caller_format(self, input_format):
        # Define a regular expression pattern to capture the information
        print(f"input format is:{input_format}")
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
                    group_id, group_name, group_caller = self.parse_group_caller_format(self.getting_called_by)
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

    def handle_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            if self.is_getting_called:
                self.media_player.setMedia(self.ringtone)
                self.media_player.play()

    def getting_a_call(self):
        try:
            self.media_player.setMedia(self.ringtone)
            self.media_player.play()
        except Exception as e:
            print(f"::{e}")

    def new_message_play_audio(self):
        try:
            self.media_player.setMedia(self.new_message_audio)
            self.media_player.play()
        except Exception as e:
            print(f"::{e}")

    def play_sound(self, sound):
        try:
            self.media_player.setMedia(sound)
            self.media_player.play()
        except Exception as e:
            print(f"::{e}")

    def stop_sound(self):
        try:
            self.media_player.stop()
        except Exception as e:
            print(f"Error stopping sound: {e}")

    def Chat_clicked(self):
        global chat_clicked, setting_clicked, social_clicked
        if not chat_clicked:
            self.current_friends_box_search = False
            self.current_chat_box_search = False
            self.temp_search_list = []
            chat_clicked = True
            self.stacked_widget.setCurrentIndex(0)
            setting_clicked = False
            social_clicked = False

    def Settings_clicked(self):
        global chat_clicked, setting_clicked, social_clicked
        if not setting_clicked:
            self.current_friends_box_search = False
            self.current_chat_box_search = False
            self.stacked_widget.setCurrentIndex(1)
            chat_clicked = False
            setting_clicked = True
            social_clicked = False

    def Social_clicked(self):
        global chat_clicked, setting_clicked, social_clicked
        if not social_clicked:
            self.current_friends_box_search = False
            self.current_chat_box_search = False
            self.temp_search_list = []
            self.stacked_widget.setCurrentIndex(2)
            chat_clicked = False
            setting_clicked = False
            social_clicked = True


    def updated_requests(self):
        global social_clicked
        try:
            if self.friends_box_page == "add friend" or self.friends_box_page == "blocked":
                self.stacked_widget.removeWidget(self.friends_box)
                self.friends_box = FriendsBox(friends_list=self.friends_list,
                                              requests_list=self.request_list, Network=n, username=self.username,
                                              parent=self)
                self.stacked_widget.insertWidget(2, self.friends_box)
                if social_clicked:
                    self.stacked_widget.setCurrentIndex(2)
            else:
                search_bar_text = self.friends_box.search.text()
                has_had_focus_of_search_bar = self.friends_box.search.hasFocus()
                self.stacked_widget.removeWidget(self.friends_box)
                self.friends_box = FriendsBox(friends_list=self.friends_list,
                                              requests_list=self.request_list, Network=n, username=self.username, parent=self)
                self.stacked_widget.insertWidget(2, self.friends_box)

                if len(search_bar_text) > 0:
                    self.friends_box.search.setText(search_bar_text)
                    self.friends_box.search.setFocus(True)
                    self.friends_box.search.deselect()
                else:
                    if has_had_focus_of_search_bar:
                        self.friends_box.search.setFocus(True)
                        self.friends_box.search.deselect()

                if social_clicked:
                    self.stacked_widget.setCurrentIndex(2)
        except Exception as e:
            print(f"error in updating social page{e}")

    def updated_settings_page(self):
        try:
            self.stacked_widget.removeWidget(self.settings_box)
            self.settings_box = SettingsBox(parent=self)
            self.stacked_widget.insertWidget(1, self.settings_box)
            self.stacked_widget.setCurrentIndex(1)
        except Exception as e:
            print(f"error in updated_settings_page error:{e}")

    def keyPressEvent(self, event):
        global n, chat_clicked, social_clicked
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            try:
                if chat_clicked and self.chat_box.chat_name_label.text() != "":
                    if self.chat_box.check_editing_status():
                        if len(self.chat_box.text_entry.text()) > 0:
                            current_time = datetime.datetime.now()
                            formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
                            info = (self.chat_box.text_entry.text(), self.username, str(formatted_time))
                            self.list_messages.insert(0, info)
                            n.send_message(self.username, self.selected_chat, info[0])
                            print("Sent message to server")
                            self.updated_chat()
                            self.chat_box.text_entry.setText("")
                            self.chat_box.text_entry.setFocus()
                if self.image_to_send:
                    print(len(self.image_to_send))
                    # Compresses the byte representation of an image using zlib,
                    # encodes the compressed data as base64, and then decodes
                    # it into a UTF-8 string for transmission or storage.
                    compressed_base64_image = base64.b64encode(zlib.compress(self.image_to_send)).decode()
                    print(len(compressed_base64_image))
                    current_time = datetime.datetime.now()
                    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
                    info = (compressed_base64_image, self.username, str(formatted_time))
                    self.list_messages.insert(0, info)
                    n.send_message(self.username, self.selected_chat, compressed_base64_image)
                    self.image_to_send = None
                    self.image_file_name = ""
                    self.updated_chat()
                elif social_clicked:
                    self.friends_box.send_friend_request()
            except Exception as e:
                print(f"expection in key press event:{e}")
        elif event.key() == Qt.Key_Escape:
            if not chat_clicked:
                self.Chat_clicked()
            else:
                if self.is_create_group_pressed:
                    self.is_create_group_pressed = False
                    self.selected_group_members.clear()
                    self.updated_chat()
        else:
            if setting_clicked and self.is_editing_push_to_talk_button:
                key = event.key()
                special_keys_mapping = {
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

                # Use the dictionary or fallback to Qt enumeration values

                key_string = chr(key) if 32 <= key <= 126 else special_keys_mapping.get(key)
                self.push_to_talk_key = key_string
                self.is_editing_push_to_talk_button = False
                self.updated_settings_page()


    def wheelEvent(self, event):
        global chat_clicked
        # Handle the wheel event (scrolling)
        if chat_clicked:
            delta = event.angleDelta().y() / 120  # Normalize the delta
            mouse_pos = event.pos()

            if delta > 0 and self.chat_box.is_mouse_on_chat_box(mouse_pos) and not self.is_last_message_on_screen:
                # Scrolling up

                self.chat_start_index += 1
                self.updated_chat()
            elif delta < 0 and self.chat_start_index > 0 and self.chat_box.is_mouse_on_chat_box(mouse_pos):
                # Scrolling down, but prevent scrolling beyond the first message
                self.chat_start_index -= 1
                self.updated_chat()

            elif delta > 0 and self.chat_box.is_mouse_on_chats_list(mouse_pos) and (self.chat_box_chats_index < 0): #or something
                # Scrolling up

                self.chat_box_chats_index += 1
                self.updated_chat()
            elif delta < 0 and self.chat_box.is_mouse_on_chats_list(mouse_pos):
                # Scrolling down, but prevent scrolling beyond the first message
                self.chat_box_chats_index -= 1
                self.updated_chat()
        if social_clicked:
            try:
                delta = event.angleDelta().y() / 120  # Normalize the delta
                mouse_pos = event.pos()
                if delta > 0 and self.friends_box.is_mouse_on_friends_box(mouse_pos) and self.friends_box_index_y_start > self.friends_box.default_starting_y:
                    # Scrolling up

                    self.friends_box_index += 1
                    self.updated_requests()
                elif delta < 0 and self.friends_box.is_mouse_on_friends_box(mouse_pos) and self.is_friends_box_full:
                    # Scrolling down, but prevent scrolling beyond the first message
                    self.friends_box_index -= 1
                    self.updated_requests()
            except Exception as e:
                print(f"error in social_clicked scrolling error:{e}")

    def hide_chat(self):
        self.main_layout.addSpacerItem(self.spacer)
        self.chat_box.hide()

    def show_chat(self):
        self.main_layout.removeItem(self.spacer)
        self.chat_box.setVisible(True)

    def updated_chat(self):
        global chat_clicked
        try:
            text = ""
            try:
                text = self.chat_box.text_entry.text()
            except Exception as e:
                print(f"error in updated chat {e}")
            has_had_focus_of_search_bar = self.chat_box.find_contact_text_entry.hasFocus()
            self.stacked_widget.removeWidget(self.chat_box)
            name = self.selected_chat
            search_bar_text = self.chat_box.find_contact_text_entry.text()
            try:
                self.chat_box = ChatBox(name, self.list_messages, self.friends_list,
                                   parent=self, Network=n)
            except Exception as e:
                print(f"error in creating chat_box on updated_chat_func : {e}")
            if self.chat_box.messages_list is None:
                self.chat_start_index = 0

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
            if chat_clicked:
                self.stacked_widget.setCurrentIndex(0)
        except Exception as e:
            print(f"error in updated chat {e}")


    def update_values(self):
        self.friends_box.username = self.username

    def closeEvent(self, event):
        # This function is called when the window is closed
        self.quit_application()

    def quit_application(self):
        global app, flag_updates, Flag_recv_messages
        # Ensure your application quits
        Flag_recv_messages = False
        flag_updates = False
        print("closing app...")
        app.quit()

class Sign_up_page(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.password_not_match_label = QLabel('Password does not match', self)
        self.password_not_match_label.setStyleSheet("color: red; font-size: 12px;")
        self.password_not_match_label.move(1690//2+2, 413)
        self.password_not_match_label.hide()

        self.email_Required_field = self.create_label("Required field", (1690//2+25, 572))
        self.username_Required_field = self.create_label("Required field", (1690//2+25, 332))
        self.password_Required_field = self.create_label("Required field", (1690//2+25, 412))
        self.confirm_password_Required_field = self.create_label("Required field", (1690//2+25, 492))
        self.invalid_email = self.create_label("Invalid Email", (1690//2+25, 572))
        self.password_too_short = self.create_label("Password too short", (1690//2+25, 413))
        self.username_already_used = self.create_label("Username is taken", (1690 // 2 + 25, 332))
        self.hide_every_error_label()

    def hide_every_error_label(self):
        self.password_too_short.hide()
        self.email_Required_field.hide()
        self.username_Required_field.hide()
        self.password_Required_field.hide()
        self.confirm_password_Required_field.hide()
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

        icon_size = QSize(20, 20)  # Set your desired size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

        image_button.setIconSize(scaled_size)
        image_button.move(1690//2+60, 235)

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

        label.move(1690//2, 192)
        username.move(1690 // 2, 280)
        password.move(1690 // 2, 360)
        password_confirm.move(1690 // 2, 440)
        email.move(1690//2, 520)

        # Create button
        submit_button = QPushButton('Submit', self)
        submit_button.clicked.connect(lambda: self.submit_form(username.text(), password.text(), password_confirm.text(), email.text()))
        submit_button.move(1690//2-25, 600)

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

    def submit_form(self, username, password, password_confirm, email):
        global n
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
        if is_info_valid:
            n.send_sign_up_info(username, password, email)
            data = n.recv_str()
            if data.startswith("code:"):
                parts = data.split(":")
                action, destination = parts[1], parts[2]
                if action == "sent" and destination == "email":
                    verification_code_page.showMaximized()
                    self.hide()
            elif data.startswith("sign_up"):
                parts = data.split(":")
                result = parts[1]
                if result == "invalid":
                    self.username_already_used.show()

    def return_button_pressed(self):
        global Last_page
        Last_page.showMaximized()
        self.hide()


class Login_page(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.visibility_password_button = QPushButton(self)
        # Load an image and set it as the button's icon
        self.show_password_icon = QIcon("discord_app_assets/show_password_icon.png")
        self.hide_password_icon = QIcon("discord_app_assets/hide_password_icon1.png")
        self.visibility_password_button.setIcon(self.show_password_icon)
        self.current_icon = "discord_app_assets/show_password_icon.png"
        icon_size = QSize(40, 40)  # Set your desired size
        icon_actual_size = self.show_password_icon.actualSize(self.show_password_icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
        self.visibility_password_button.setIconSize(scaled_size)
        self.visibility_password_button.move(1690 // 2 + 170, 360)
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
        self.password.move(1690 // 2, 360)

        self.username = QLineEdit(self)
        self.remember_me_status = False
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet("color: white;")
        self.username.move(1690 // 2, 280)
        self.incorrect_label = QLabel('Username or Password incorrect', self)
        self.incorrect_label.setStyleSheet(
            "color: red; font-size: 12px;")  # Set the text color to blue and font size to 12px
        self.incorrect_label.move(1690//2+10, 333)
        self.incorrect_label.hide()

        self.user_is_logged_in = QLabel('Username already logged in', self)
        self.user_is_logged_in.setStyleSheet(
            "color: red; font-size: 12px;")  # Set the text color to blue and font size to 12px
        self.user_is_logged_in.move(1690//2+10, 333)
        self.user_is_logged_in.hide()

    def init_ui(self):

        label = QLabel("Welcome Back", self)
        image_button = QPushButton(self)

        # Load an image and set it as the button's icon
        icon = QIcon("discord_app_assets/right-arrow-icon-27.png")
        image_button.setIcon(icon)

        icon_size = QSize(20, 20)  # Set your desired size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

        image_button.setIconSize(scaled_size)
        image_button.move(1690//2+60, 235)


        # Create "Forgot your password?" label
        forgot_password_label = QLabel('<a href="forgot">Forgot your password</a>', self)
        forgot_password_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        forgot_password_label.setOpenExternalLinks(False)  # Disable external links to capture linkActivated signal
        forgot_password_label.setStyleSheet("color: blue; font-size: 12px;")  # Set the text color to blue and font size to 12px

        sign_up_label = QLabel('<a href="sign_up">Dont have a user yet? sign up here</a>', self)
        sign_up_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        sign_up_label.setOpenExternalLinks(False)  # Disable external links to capture linkActivated signal
        sign_up_label.setStyleSheet("color: blue; font-size: 12px;")  # Set the text color to blue and font size to 12px

        checkbox = QCheckBox('Keep me signed in', self)
        checkbox.setStyleSheet("QCheckBox { color: white; font-size: 12px}")
        checkbox.stateChanged.connect(self.on_checkbox_change)
        checkbox.move(1690//2+10, 415)
        # Connect the linkActivated signal to a custom slot
        forgot_password_label.linkActivated.connect(self.forgot_password_clicked)
        forgot_password_label.move(1690//2+10, 445)
        sign_up_label.linkActivated.connect(self.move_to_sign_up_page)
        sign_up_label.move(1690//2-30, 535)
        label.move(1690//2+10, 192)


        # Create button
        submit_button = QPushButton('Login', self)
        submit_button.clicked.connect(self.submit_form)
        submit_button.move(1690//2-30, 465)
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
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
        """)

    def on_checkbox_change(self, state):
        # This function is called when the checkbox state changes
        if state == 2:  # 2 corresponds to checked state
            self.remember_me_status = True
        else:
            self.remember_me_status = False

    def submit_form(self):
        global n, is_logged_in
        self.incorrect_label.hide()
        self.user_is_logged_in.hide()
        username = self.username.text()
        password = self.password.text()
        n.send_login_info(username, password)
        data = n.recv_str()
        if data.startswith("login"):
            result = data.split(":")[1]
            if result == "confirm":
                print("logged in successfully")
                self.hide()

                if self.remember_me_status:
                    n.ask_for_security_token()
                    print("You will be remembered")
                    main_page.username = username
                    main_page.update_values()
                    main_page.showMaximized()
                    is_logged_in = True
                    threading.Thread(target=thread_recv_messages, args=()).start()
                else:
                    main_page.username = username
                    main_page.update_values()
                    main_page.showMaximized()
                    is_logged_in = True
                    threading.Thread(target=thread_recv_messages, args=()).start()
            elif data == "already_logged_in":
                print("User logged in from another device")
                self.user_is_logged_in.show()
            else:
                print("login info isn't correct")
                self.incorrect_label.show()

    def forgot_password_clicked(self):
        global Last_page

        Last_page = login_page
        forget_password_page.showMaximized()
        self.hide()

    def move_to_sign_up_page(self):
        global Last_page
        Last_page = login_page
        sign_up_page.showMaximized()
        self.hide()

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
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.image_label)

        self.setGeometry(100, 100, 800, 600)
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
        global main_page
        if event.key() == Qt.Key_Escape:
            main_page.showMaximized()
            main_page.Network.stop_watching_current_stream()
            print(f"stopped watching {main_page.watching_user} share screen")
            main_page.is_watching_screen = False
            main_page.watching_user = ""
            main_page.watching_type = None
            self.close()

class Forget_password_page(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.username = QLineEdit(self)
        self.username.move(1690 // 2, 280)
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet("color: white;")
        self.email = QLineEdit(self)
        self.email.setPlaceholderText("Email")
        self.email.setStyleSheet("color: white;")
        self.email.move(1690 // 2, 360)


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
        icon_size = QSize(20, 20)  # Set your desired size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
        image_button.setIconSize(scaled_size)
        image_button.move(1690 // 2 + 60, 235)
        image_button.clicked.connect(self.return_button_pressed)




        # Set placeholder text and color


        # Create "Forgot your password?" label
        code_label = QLabel('<a href="forgot">Resend code</a>', self)
        code_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        code_label.setOpenExternalLinks(False)  # Disable external links to capture linkActivated signal
        code_label.setStyleSheet("color: blue; font-size: 15px;")  # Set the text color to blue and font size to 12px

        # Connect the linkActivated signal to a custom slot
        code_label.linkActivated.connect(self.resend_code_clicked)
        code_label.move(1690//2+20, 420)


        label.move(1690//2, 192)


        # Create button
        submit_button = QPushButton('Submit info', self)
        submit_button.clicked.connect(self.submit_form)
        submit_button.move(1690//2-30, 450)
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

    def return_button_pressed(self):
        global Last_page
        Last_page.showMaximized()
        Last_page = splash_page
        self.hide()

    def submit_form(self):
        global n, verification_code_page
        username = self.username.text()
        email = self.email.text()
        flag_change_password = True
        while flag_change_password:
            if is_email_valid(email) and len(username) > 0:
                n.send_username_and_email_froget_password(username, None, email)
                data = n.recv_str()
                if data.startswith("forget_password"):
                    parts = data.split(":")
                    result = parts[1]
                    if result == "valid":
                        print("Server send code to email")
                        self.hide()
                        verification_code_page.showMaximized()
                        break
                    elif result == "invalid":
                        break

    def resend_code_clicked(self):
        print(4)



class Verification_code_page(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.info_label = QLabel(self)
        pixmap = QPixmap('discord_app_assets/info_icon.png')  # Replace with the path to your 'i' icon
        scaled_pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio)
        self.info_label.setPixmap(scaled_pixmap)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("background-color: #141c4b; border-radius: 25px;")
        self.info_label.setToolTip('A mail will be sent to your chosen email address')
        self.info_label.move(900, 250)
        self.info_label.setMouseTracking(True)
        self.info_label.installEventFilter(self)
        self.code = QLineEdit(self)
        self.code.setMaxLength(6)
        self.code.setValidator(QIntValidator())

        # Set placeholder text and color

        self.code.setPlaceholderText("code")
        self.code.setStyleSheet("color: white;")
        self.code.move(1690 // 2, 320)

        self.successfully_signed_up = self.create_label("successfully signed up", (1690 // 2+5, 540))
        self.successfully_signed_up.hide()


        self.image_button = QPushButton(self)
        # Load an image and set it as the button's icon
        icon = QIcon("discord_app_assets/right-arrow-icon-27.png")
        self.image_button.setIcon(icon)
        icon_size = QSize(20, 20)  # Set your desired size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
        self.image_button.setIconSize(scaled_size)
        self.image_button.move(1690 // 2 + 60, 205)
        self.image_button.hide()
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
        global login_page
        self.hide()
        login_page.showMaximized()

    def eventFilter(self, obj, event):
        if obj == self.info_label and event.type() == event.Enter:
            # Set a fixed position for the tooltip
            fixed_position = self.mapToGlobal(QPoint(800, 300))
            QToolTip.showText(fixed_position, self.info_label.toolTip())
            return True  # Consume the event to prevent further processing
        return super().eventFilter(obj, event)

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
        code_label.linkActivated.connect(self.Resend_code_clicked)
        code_label.move(1690//2+10, 410)

        label.move(1690//2, 180)


        # Create button
        submit_button = QPushButton('Submit code', self)
        submit_button.clicked.connect(self.submit_form)
        submit_button.move(1690//2+10, 450)
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
            QPushButton {
                background-color: #6fa8b6;
                color: #f0f1f1;
                padding: 20px;
                border: 1px solid #2980b9;
                border-radius: 5px;
                min-width: 30px;
                max-width: 100px;
                min-height: 0px;  /* Set the minimum height to 50 pixels */
                max-height: 16px; /* Set the maximum height to 200 pixels */
                font-size: 16px;  /* Set your desired font size */
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
        """)


    def submit_form(self):
        global n, change_password_page
        code = self.code.text()
        try:
            if len(code) == 6:
                n.send_sign_up_verification_code(code)
                print("Sent verification code to server")
                data = n.recv_str()
                if data.startswith("sign_up"):
                    kind = data.split(":")[1]
                    if kind == "code":
                        result = data.split(":")[2]
                        if result == "valid":
                            print("Server got the code")
                            self.successfully_signed_up.show()
                            self.image_button.show()
                        elif result == "invalid":
                            pass
                elif data.startswith("forget_password"):
                    parts = data.split(":")
                    kind = parts[1]
                    result = parts[2]
                    if kind == "code":
                        if result == "valid":
                            self.hide()
                            change_password_page.showMaximized()
                        elif result == "invalid":
                            pass
        except Exception as e:
            print(f"error in submit_form verification code {e}")

    def Resend_code_clicked(self, link):
        if link == "resend":
            print("resend code")

class Change_password_page(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.change_password_label = QLabel("Change password:", self)
        self.change_password_label.move(1690 // 2, 200)
        self.new_password = QLineEdit(self)
        self.new_password.move(1690 // 2, 280)
        self.new_password.setPlaceholderText("New password")
        self.new_password.setStyleSheet("color: white;")
        self.status = False
        self.image_button = QPushButton(self)
        # Load an image and set it as the button's icon
        icon = QIcon("discord_app_assets/right-arrow-icon-27.png")
        self.image_button.setIcon(icon)
        icon_size = QSize(20, 20)  # Set your desired size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
        self.image_button.setIconSize(scaled_size)
        self.image_button.move(1690 // 2 + 60, 205)

        self.image_button.clicked.connect(self.return_button_pressed)
        self.image_button.hide()
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
        global login_page
        self.hide()
        login_page.showMaximized()



    def create_label(self, text, position):
        label = QLabel(text, self)
        label.setStyleSheet("color: red; font-size: 12px;")
        label.move(position[0], position[1])
        label.hide()
        return label

    def init_ui(self):
        self.too_short = QLabel("Password too short", self)

        image_button = QPushButton(self)
        # Load an image and set it as the button's icon
        icon = QIcon("discord_app_assets/right-arrow-icon-27.png")
        image_button.setIcon(icon)
        icon_size = QSize(20, 20)  # Set your desired size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
        image_button.setIconSize(scaled_size)
        image_button.move(1690 // 2 + 60, 235)
        image_button.clicked.connect(self.return_button_pressed)

        self.too_short.move(1690//2+10, 340)
        self.too_short.hide()
        self.too_short.setStyleSheet(
            "color: red; font-size: 14px;")  # Set the text color to blue and font size to 12px
        self.changed_password_label = QLabel("Password changed", self)
        self.changed_password_label.move(1690 // 2, 340)
        self.changed_password_label.hide()
        # Create button
        submit_button = QPushButton('Submit info', self)
        submit_button.clicked.connect(self.submit_form)
        submit_button.move(1690//2-30, 450)
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

    def return_button_pressed(self):
        global Last_page
        if self.status:
            Last_page.showMaximized()
            Last_page = splash_page
            self.hide()

    def submit_form(self):
        global n, verification_code_page
        flag_change_password = True
        self.too_short.hide()
        self.changed_password_label.hide()
        while flag_change_password:
            if len(self.new_password.text()) >= 8:
                n.send_new_password(self.new_password.text())
                print("Password changed")
                self.changed_password_label.show()
                self.status = True
                break
            else:
                self.too_short.show()
                break



    def resend_code_clicked(self):
        print(4)

def load_all_pages(n):
    global sign_up_page, forget_password_page, login_page, verification_code_page, main_page, change_password_page
    sign_up_page = Sign_up_page()
    forget_password_page = Forget_password_page()
    login_page = Login_page()
    main_page = MainPage(n)
    change_password_page = Change_password_page()
    verification_code_page = Verification_code_page()
    main_page.showMaximized()
    main_page.hide()
    sign_up_page.showMaximized()
    forget_password_page.showMaximized()
    login_page.showMaximized()
    login_page.hide()
    verification_code_page.showMaximized()
    sign_up_page.hide()
    forget_password_page.hide()
    verification_code_page.hide()
    change_password_page.showMaximized()
    change_password_page.hide()


Last_page = None
if __name__ == '__main__':
    n = client_net()
    app = QApplication(sys.argv)
    splash_page = SplashScreen()
    splash_page.showMaximized()
    load_all_pages(n)
    app.exec_()

