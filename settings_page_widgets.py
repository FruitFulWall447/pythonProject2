from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import QSize, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QPixmap
from io import BytesIO
from PIL import Image, ImageDraw
import warnings
import re
import pyaudio
import cv2


def is_valid_image(image_bytes):
    try:
        # Use Pillow to try opening the image from bytes
        image = Image.open(BytesIO(image_bytes))
        # If successful, it's a valid image
        return True
    except Exception as e:
        # If there is an exception, it's not a valid image
        print(f"Error: {e}")
        return False


def file_to_bytes(file_path):
    with open(file_path, "rb") as file:
        image_bytes = file.read()
        return image_bytes


def create_custom_circular_label(width, height, parent):
    label = QLabel(parent)

    label_size = QSize(width, height)
    label.setFixedSize(label_size)

    label.setStyleSheet("""
        QLabel {
            border-radius: """ + str(height // 2) + """px; /* Set to half of the label height */
            background-color: transparent; /* Make the background color transparent */

        }
    """)

    return label


def try_to_open_output_stream(index):
    audio_format = pyaudio.paInt16
    channels = 1
    rate = 44100
    chunk = 1024
    p = pyaudio.PyAudio()
    try:
        output_stream = p.open(format=audio_format, channels=channels, rate=rate, output=True, frames_per_buffer=chunk,
                               output_device_index=index)
        return True
    except:
        return False


def try_to_open_input_stream(index):
    audio_format = pyaudio.paInt16
    channels = 1
    rate = 44100
    chunk = 1024
    p = pyaudio.PyAudio()
    try:
        input_stream = p.open(format=audio_format,
                              channels=channels,
                              rate=rate,
                              input=True,
                              frames_per_buffer=chunk,
                              input_device_index=index)
        return True
    except:
        return False


def get_output_devices():
    input_devices = []
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        device_name = device_info["name"].lower()
        if device_info["maxOutputChannels"] > 0 and ("headset" in device_name or "speaker" in device_name or "headphones" in device_name):
            if device_info["name"] not in input_devices:
                device_index = i
                if try_to_open_output_stream(device_index):
                    input_devices.append(device_info["name"])
    p.terminate()
    return input_devices


def get_input_devices():
    output_devices = []
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        device_name = device_info["name"].lower()
        if device_info["maxInputChannels"] > 0 and ("microphone" in device_name):
            if device_info["name"] not in output_devices:
                device_index = i
                if try_to_open_input_stream(device_index):
                    output_devices.append(device_info["name"])
    p.terminate()
    return output_devices


def set_icon_from_path_to_label(label, image_path):
    # Load the image from file path
    pixmap = QPixmap(image_path)

    # Get the size of the label
    label_size = label.size()
    label_width = label_size.width()
    label_height = label_size.height()

    # Calculate the aspect ratio of the image
    image_width = pixmap.width()
    image_height = pixmap.height()
    image_aspect_ratio = image_width / image_height

    # Determine how to scale the image based on its aspect ratio
    if image_aspect_ratio <= 0.5:
        scaled_pixmap = pixmap.scaledToWidth(label_width, Qt.SmoothTransformation)
    elif image_aspect_ratio >= 1.5:
        scaled_pixmap = pixmap.scaledToHeight(label_height, Qt.SmoothTransformation)
    else:
        scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    # Set the scaled pixmap to the label
    label.setPixmap(scaled_pixmap)
    label.setAlignment(Qt.AlignCenter)


def set_icon_from_bytes_to_label(label, image_bytes):
    # Load the image from bytes
    pixmap = QPixmap()
    pixmap.loadFromData(image_bytes)

    # Get the size of the label
    label_size = label.size()
    label_width = label_size.width()
    label_height = label_size.height()

    # Calculate the aspect ratio of the image
    image_width = pixmap.width()
    image_height = pixmap.height()
    image_aspect_ratio = image_width / image_height

    # Determine how to scale the image based on its aspect ratio
    if image_aspect_ratio <= 0.5:
        scaled_pixmap = pixmap.scaledToWidth(label_width, Qt.SmoothTransformation)
    elif image_aspect_ratio >= 1.5:
        scaled_pixmap = pixmap.scaledToHeight(label_height, Qt.SmoothTransformation)
    else:
        scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    # Set the scaled pixmap to the label
    label.setPixmap(scaled_pixmap)
    label.setAlignment(Qt.AlignCenter)


def set_button_icon(button, icon_path, width, height):
    try:
        icon = QIcon(icon_path)
        button.setIcon(icon)
        icon_size = QSize(width, height)

        # Use the provided width and height to scale the icon
        scaled_size = icon.pixmap(icon_size).size()
        button.setIconSize(scaled_size)
    except Exception as e:
        print(f"Error in setting button icon: {e}")


def extract_number(s):
    # Use regular expression to find the number in the string
    match = re.search(r'\d+', s)
    if match:
        # Convert the matched number to an integer and return it
        return int(match.group())
    else:
        # If no number is found, return None or raise an exception, depending on your use case
        return None  # or raise ValueError("No number found in the string")


def make_circular_image(image_bytes):
    """Converts an image to a circular image with the same width and height.

    Args:
        image_bytes (bytes): Image data as bytes.

    Returns:
        bytes: The circular image as bytes.
    """
    try:
        # Load the image using Pillow
        with BytesIO(image_bytes) as image_buffer:
            image = Image.open(image_buffer)

            # Convert the image to RGBA mode (if not already)
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # Determine the minimum dimension for the circular image
            min_dimension = min(image.width, image.height)

            # Create a square-shaped image
            square_image = Image.new('RGBA', (min_dimension, min_dimension), (255, 255, 255, 0))
            offset = ((min_dimension - image.width) // 2, (min_dimension - image.height) // 2)
            square_image.paste(image, offset)

            # Determine the maximum circular area based on the minimum dimension
            max_radius = min_dimension // 2

            # Create a mask with a transparent circle
            mask = Image.new('L', (min_dimension, min_dimension), 0)  # Create a black mask
            draw = ImageDraw.Draw(mask)
            draw.ellipse(((0, 0), (min_dimension, min_dimension)), fill=255)

            # Apply the mask to the image
            circular_image = Image.new('RGBA', (min_dimension, min_dimension), (255, 255, 255, 0))
            circular_image.paste(square_image, mask=mask)

            # Convert the circular image to bytes
            output_buffer = BytesIO()
            circular_image.save(output_buffer, format='PNG')  # Save as PNG format
            circular_image_bytes = output_buffer.getvalue()

        return circular_image_bytes

    except Exception as e:
        print(f"Error converting image: {e}")
        return None


def make_q_object_clear(object):
    object.setStyleSheet("background-color: transparent; border: none;")


def check_camera(i):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Ignore OpenCV warnings
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            _, frame = cap.read()
            cap.release()
            return f"Camera {i}"
    except Exception as e:
        pass  # Handle any exceptions that may occur during camera check
    return None


def get_camera_names():
    camera_names = []
    for i in range(10):  # You can adjust the range according to your needs
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            camera_names.append(f"Camera {i}")
            cap.release()
        else:
            break
    return camera_names


def get_default_output_device_name():
    p = pyaudio.PyAudio()
    return p.get_default_output_device_info().get("name").lower()


def get_default_input_device_name():
    p = pyaudio.PyAudio()
    return p.get_default_input_device_info().get("name").lower()


def find_input_device_index(device_name):
    p = pyaudio.PyAudio()
    input_device_index = None

    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info["name"].lower() == device_name.lower():
            input_device_index = i
            break

    p.terminate()
    return input_device_index


def find_output_device_index(device_name):
    p = pyaudio.PyAudio()
    output_device_index = None

    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info["name"].lower() == device_name.lower():
            output_device_index = i
            break

    p.terminate()
    return output_device_index


class SettingsBox(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.font_size = 60
        self.parent = parent
        self.Network = self.parent.Network
        self.settings_button_height = 50
        self.file_dialog = QFileDialog(self)
        self.file_dialog.setFileMode(QFileDialog.ExistingFile)
        self.file_dialog.setNameFilter("Image files (*.png *.jpg)")


        delta_of_main_buttons = 50

        starter_x_of_main_buttons = 350
        starter_y_of_main_buttons = 100

        self.privacy_button_width, self.privacy_button_height = (200, 30)

        label_height = 30
        label_width = 300
        self.default_labels_font_size = 10
        user_settings_label = self.create_white_label(starter_x_of_main_buttons+10 , starter_y_of_main_buttons-35, self.default_labels_font_size,label_width, label_height, "USER SETTINGS")
        self.my_account_button = self.create_settings_main_buttons("My Account", self.my_account_pressed, (
        starter_x_of_main_buttons, starter_y_of_main_buttons))

        starter_y_of_main_buttons += delta_of_main_buttons

        self.user_profile_button = self.create_settings_main_buttons("User Profile", self.user_profile_pressed, (
        starter_x_of_main_buttons, starter_y_of_main_buttons))

        starter_y_of_main_buttons += delta_of_main_buttons

        self.appearance_button = self.create_settings_main_buttons("Appearance", self.appearance_pressed, (
        starter_x_of_main_buttons, starter_y_of_main_buttons))

        starter_y_of_main_buttons += delta_of_main_buttons

        self.voice_video_button = self.create_settings_main_buttons("Voice && Video", self.voice_video_pressed, (
        starter_x_of_main_buttons, starter_y_of_main_buttons))

        starter_y_of_main_buttons += delta_of_main_buttons

        self.privacy_safety_button = self.create_settings_main_buttons("Privacy && Safety", self.privacy_safety, (
        starter_x_of_main_buttons, starter_y_of_main_buttons))

        background_color = self.parent.background_color_hex
        hover_color = self.parent.standard_hover_color

        self.label = QLabel(self)
        self.label.setStyleSheet(f"border-right: 3px solid {self.parent.standard_hover_color}; padding-left: 10px;")
        self.label.setGeometry(starter_x_of_main_buttons + self.privacy_safety_button.width()-3, -20, 3, 1020)

        self.combo_box_style_sheet = """
            QComboBox {
                background-color: %s;
                selection-background-color: %s;
                border: 1px solid %s;
                border-radius: 5px;
                padding: 2px 18px 2px 3px;
                color: white;
                min-width: 150px;  /* Adjust min-width as needed */
                max-width: 500px;  /* Set max-width to accommodate longer text */
                font-size: 14px;  /* Adjust font size as needed */
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;  /* Position the drop-down at the top right */
                width: 20px;
                border-left: 1px solid transparent;
            }

            QComboBox QAbstractItemView {
                color: white;
                background-color: %s;
                selection-background-color: %s;
                padding: 2px;
                font-size: 14px;
            }

        """ % (background_color, hover_color, hover_color, background_color, hover_color)

        slider_style_sheet_color = "#3498db"
        self.volume_slider_style_sheet = f"""
                       QSlider::groove:horizontal {{
                           border: 1px solid #bbb;
                           background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ddd, stop:1 #eee);
                           height: 10px;
                           margin: 0px;
                       }}

                       QSlider::handle:horizontal {{
                           background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc);
                           border: 1px solid #777;
                           width: 20px;
                            margin: -2px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */
                           border-radius: 5px;
                       }}

                       QSlider::add-page:horizontal {{
                           background: #fff;
                       }}

                       QSlider::sub-page:horizontal {{
                           background: {slider_style_sheet_color}; /* Change this color to the desired color for the left side */
                       }}
                               """

        label_page = self.create_white_label(800, 70, 20, None, None, self.parent.selected_settings)
        try:
            dark_green = "#1e9644"
            other_green = "#044f1c"
            red_hex = "#9e0817"
            dark_red_hex = "#690d16"
            if self.parent.selected_settings == "My Account":
                start_y = 100
                start_x = 500
                dark_green = "#1e9644"
                other_green = "#044f1c"
                width, height = (120, 120)
                self.profile_image_label = create_custom_circular_label(width, height, self)
                profile_image_x, profile_image_y = (800, 200)
                user_image = self.parent.get_circular_image_bytes_by_name(self.parent.username)
                if user_image is None:
                    icon_path = "discord_app_assets/regular_profile.png"
                    set_icon_from_path_to_label(self.profile_image_label, icon_path)
                else:
                    set_icon_from_bytes_to_label(self.profile_image_label, user_image)
                self.profile_image_label.move(profile_image_x, profile_image_y)

                label_name_next_to_image_x, label_name_next_to_image_y = (950, 240)
                label_name_next_to_image = self.create_white_label(label_name_next_to_image_x, label_name_next_to_image_y, 20, None, None, self.parent.username)

                button_edit_user_profile_x, button_edit_user_profile_y = (1250, 240)
                button_width, button_height = (180, 50)
                button_edit_user_profile = self.create_colored_button(dark_green, other_green, None, button_edit_user_profile_x, button_edit_user_profile_y, button_width , button_height, "Edit User Profile")
                button_edit_user_profile.clicked.connect(self.user_profile_pressed)

                first_account_label_y = label_name_next_to_image_y+120
                account_label_x = label_name_next_to_image_x-135
                self.create_my_account_labels(account_label_x, first_account_label_y, self.default_labels_font_size+2, "USERNAME", self.parent.username)
                y = first_account_label_y + 80
                text = self.parent.email
                if text is None:
                    text = "None"
                self.create_my_account_labels(account_label_x, y, self.default_labels_font_size+2,
                                              "EMAIL", text)
                y = y + 80
                text = self.parent.phone_number
                if text is None:
                    text = "None"
                self.create_my_account_labels(account_label_x, y, self.default_labels_font_size+2,
                                              "PHONE NUMBER", text)
                change_password_button_x, change_password_button_y = account_label_x-30, y+120
                change_password_button = self.create_colored_button(dark_green, other_green, None,
                                                                      change_password_button_x,
                                                                      change_password_button_y, button_width,
                                                                      button_height, "Change Password")
                delete_account_button_x, delete_account_button_y = change_password_button_x, change_password_button_y+100
                delete_account_button = self.create_colored_button(red_hex, dark_red_hex, None,
                                                                      delete_account_button_x,
                                                                      delete_account_button_y, button_width,
                                                                      button_height, "Delete Account")


            elif self.parent.selected_settings == "Voice & Video":
                # Check if the device has input capability
                input_devices = get_input_devices()
                output_devices = get_output_devices()

                camera_names_list = self.parent.camera_devices_names

                starter_y = 170
                volume_slider_y = starter_y+100
                volume_slider_label_y = volume_slider_y - 15
                volume_slider__x = 800
                volume_slider_label_x = volume_slider__x
                width, height = (300, 45)
                slider_min_value = 0
                slider_max_value = 100
                self.volume_slider = self.create_slider(slider_min_value, slider_max_value, self.parent.volume, self.set_volume, volume_slider__x, volume_slider_y
                                                        , width, height, self.volume_slider_style_sheet)

                volume_slider_label = self.create_white_label(volume_slider_label_x, volume_slider_label_y, self.default_labels_font_size, None, None, "OUTPUT VOLUME")
                self.volume_label = self.create_white_label(volume_slider_label_x + width + 10, volume_slider_y+7, self.default_labels_font_size, 100, 30, str(self.parent.volume))

                space_between_option_box_and_label = 30
                output_x, output_y = (800, starter_y)
                self.output_combobox = self.create_option_box(width, height, output_x, output_y, output_devices)
                self.output_combobox.addItem("Default")
                self.output_combobox.currentIndexChanged.connect(self.output_device_changed)
                output_label = self.create_white_label(output_x, output_y-space_between_option_box_and_label, self.default_labels_font_size, None, None, "OUTPUT DEVICES")
                self.output_combobox.setCurrentText(get_default_output_device_name())

                input_x, input_y = (1150, starter_y)
                self.input_combobox = self.create_option_box(width, height, input_x, input_y, input_devices)
                self.input_combobox.addItem("Default")
                self.input_combobox.currentIndexChanged.connect(self.input_device_changed)
                self.input_combobox.setCurrentText(get_default_input_device_name())

                input_label = self.create_white_label(input_x, input_y - space_between_option_box_and_label, self.default_labels_font_size, None,
                                                       None, "INPUT DEVICES")
                camera_x, camera_y = (800, 670)
                self.camara_devices_combobox = self.create_option_box(width, height, camera_x, camera_y, camera_names_list)
                self.camara_devices_combobox.currentIndexChanged.connect(self.camera_device_changed)
                camera_label = self.create_white_label(camera_x, camera_y - space_between_option_box_and_label, self.default_labels_font_size, None,
                                                       None, "CAMERA")

                input_mode_x, input_mode_y = (800, 370)
                self.create_input_mode_select_button(input_mode_y, input_mode_x)
                input_mode_label = self.create_white_label(input_mode_x, input_mode_y - space_between_option_box_and_label, self.default_labels_font_size, None,
                                                       None, "INPUT MODE")
                push_to_talk_select_x, push_to_talk_select_y = (800, 550)
                push_to_talk_select = self.create_select_push_to_talk_key(push_to_talk_select_x, push_to_talk_select_y)
                push_to_talk_select_label = self.create_white_label(push_to_talk_select_x, push_to_talk_select_y - space_between_option_box_and_label, self.default_labels_font_size, None,
                                                       None, "Push to Talk Keybind")

            elif self.parent.selected_settings == "Appearance":
                starter_y = 170
                space_between_option_box_and_label = 30
                list_optional_colors = self.parent.color_design_options
                width, height = (300, 45)
                appearance_select_box_x, appearance_select_box_y = (800, starter_y)
                self.color_combobox = self.create_option_box(width, height, appearance_select_box_x, appearance_select_box_y, list_optional_colors)
                self.color_combobox.setCurrentText(self.parent.background_color)
                self.color_combobox.currentIndexChanged.connect(self.background_color_changed)
                appearance_select_box_label = self.create_white_label(appearance_select_box_x, appearance_select_box_y - space_between_option_box_and_label, self.default_labels_font_size, None,
                                                       None, "THEME COLOR")
                font_size_slider_x, font_size_slider_y = 800, starter_y+100
                font_size_slider_style_sheet = self.volume_slider_style_sheet
                font_size_slider_width, font_size_slider_height = (300, 50)
                font_size_slider_min_value, font_size_slider_max_value = (6, 20)

                font_slider_label = self.create_white_label(font_size_slider_x, font_size_slider_y-15,
                                                              self.default_labels_font_size, None, None, "FONT SIZE")
                self.font_size_slider = self.create_slider(font_size_slider_min_value, font_size_slider_max_value, self.parent.font_size,
                                                           self.font_size_changed, font_size_slider_x, font_size_slider_y
                , font_size_slider_width, font_size_slider_height, font_size_slider_style_sheet)

                self.font_size_label = self.create_white_label(font_size_slider_x + font_size_slider_width + 10, font_size_slider_y + 7,
                                                            self.default_labels_font_size, 100, 30,
                                                            str(self.parent.messages_font_size))
                font_option_x, font_option_y = 800, starter_y+200
                font_slider_label = self.create_white_label(font_option_x, font_option_y-space_between_option_box_and_label,
                                                              self.default_labels_font_size, None, None, "FONT STYLE")
                self.font_box = self.create_option_box(width, height, font_option_x, font_option_y, self.parent.font_options)
                self.font_box.setCurrentText(self.parent.font_text)
                self.font_box.currentIndexChanged.connect(self.font_updated)

            elif self.parent.selected_settings == "User Profile":
                width, height = (120, 120)
                self.profile_image_label = create_custom_circular_label(width, height, self)
                self.profile_image_label.setStyleSheet("""
                    QLabel {
                    border-radius: """ + str(height // 2) + """px; /* Set to half of the label height */
                    }
                """)

                profile_image_x, profile_image_y = (800, 200)
                user_image = self.parent.get_circular_image_bytes_by_name(self.parent.username)
                try:
                    if user_image is None:
                        icon_path = "discord_app_assets/regular_profile.png"
                        set_icon_from_path_to_label(self.profile_image_label, icon_path)
                    else:
                        set_icon_from_bytes_to_label(self.profile_image_label, user_image)
                except Exception as e:
                    print(f"error in putting profile image on label {e}")
                self.profile_image_label.move(profile_image_x, profile_image_y)
                width_change_profile_pic, height_change_profile_pic = (160, 40)
                x_change_profile_pic, y_change_profile_pic = (800, 400)
                change_profile_pic_button = self.create_colored_button(dark_green, other_green, None,
                                                                      x_change_profile_pic,
                                                                      y_change_profile_pic, width_change_profile_pic,
                                                                      height_change_profile_pic, "Change Avatar")
                change_profile_pic_button.clicked.connect(self.edit_profile_pic_pressed)
                x_remove_profile_pic, y_remove_profile_pic = (1000, 400)
                remove_profile_pic_button = self.create_colored_button(red_hex, dark_red_hex, None,
                                                                      x_remove_profile_pic,
                                                                      y_remove_profile_pic, width_change_profile_pic,
                                                                      height_change_profile_pic, "Remove Avatar")
                remove_profile_pic_button.clicked.connect(self.remove_profile_pic)
            elif self.parent.selected_settings == "Privacy & Safety":
                privacy_page_starter_x, privacy_page_starter_y = (800, 150)
                space_between_labels = 120
                option_list = ["Private account", "Censor data from strangers", "Two factor authentication"]
                self.create_privacy_labels(privacy_page_starter_x, privacy_page_starter_y, option_list, space_between_labels)
                button_starter_x, button_starter_y = privacy_page_starter_x, privacy_page_starter_y + 50
                labels_matching_vars_list = [self.parent.is_private_account, self.parent.censor_data_from_strangers, self.parent.two_factor_authentication]
                vars_names = ["is_private_account", "censor_data_from_strangers",
                                             "two_factor_authentication"]
                self.create_privacy_buttons(button_starter_x, button_starter_y, space_between_labels, labels_matching_vars_list, vars_names)
        except Exception as e:
            print(f"error setting page {e}")

    def input_device_changed(self):
        self.parent.input_device_name = self.input_combobox.currentText()
        print(f"changed input device to {self.parent.input_device_name}")
        if self.parent.play_vc_data_thread.is_alive():
            self.parent.close_send_vc_thread()
            self.parent.start_send_vc_thread()

    def output_device_changed(self):
        self.parent.output_device_name = self.output_combobox.currentText()
        print(f"changed output device to {self.parent.input_device_name}")
        if self.parent.play_vc_data_thread.is_alive():
            self.parent.close_listen_thread()
            self.parent.start_listen_thread()

    def camera_device_changed(self):
        self.parent.camera_index = extract_number(self.camara_devices_combobox.currentText())
        print(f"changed camera decive index to {self.parent.camera_index}")
        if self.parent.send_camera_data_thread.is_alive():
            self.parent.end_share_camera_thread()
            self.parent.start_camera_data_thread()

    def create_privacy_labels(self, starter_x, starter_y, list_of_label_content, space_between_labels):
        for content in list_of_label_content:
            label1 = self.create_white_label(starter_x, starter_y,
                                                    self.default_labels_font_size, None, None, content)
            starter_y += space_between_labels

    def create_privacy_buttons(self, starter_x, starter_y, space_between, list_of_button_vars, var_names):
        off_icon_path = "discord_app_assets/off_button.png"
        on_icon_path = "discord_app_assets/on_button.png"
        index = 0
        for index, (var, var_name) in enumerate(zip(list_of_button_vars, var_names)):
            button = QPushButton(self)
            make_q_object_clear(button)
            # button.setFixedSize(button_width, button_height)  # Set the size of the button
            if var:
                set_button_icon(button, on_icon_path, self.privacy_button_width, self.privacy_button_height)
            else:
                set_button_icon(button, off_icon_path, self.privacy_button_width, self.privacy_button_height)
            button.move(starter_x, starter_y)
            button.clicked.connect(
                lambda checked, btn=button, name=var_name: self.switch_off_variable_plus_change_icon(btn, name)
            )
            starter_y += space_between

    def switch_off_variable_plus_change_icon(self, button, var_name):
        off_icon_path = "discord_app_assets/off_button.png"
        on_icon_path = "discord_app_assets/on_button.png"
        try:
            var_value = not getattr(self.parent, var_name)
            set_button_icon(button, on_icon_path if var_value else off_icon_path, self.privacy_button_width,
                            self.privacy_button_height)
            setattr(self.parent, var_name, var_value)
        except Exception as e:
            print(f"error in changing privacy button icon {e}")

    def background_color_changed(self):
        new_background_color = self.color_combobox.currentText()
        self.parent.update_background_color(new_background_color)
        print(new_background_color)

    def font_updated(self):
        new_font = self.font_box.currentText()
        self.parent.font_text = new_font
        print(f"new_font is {new_font}")

    def remove_profile_pic(self):
        try:
            self.parent.profile_pic = None
            try:
                self.Network.send_profile_pic(None)
            except Exception as e:
                print(f"error in sending profile picture: {e}")
            print("send profile pic to server")
            self.parent.activateWindow()
            self.parent.update_profile_pic_dicts_list(self.parent.username, None)
        except Exception as e:
            print(f"error in resetting profile pic {e}")

    def edit_profile_pic_pressed(self):
        self.open_file_dialog()

    def open_file_dialog(self):
        if self.file_dialog.exec_():
            selected_files = self.file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                image_bytes = file_to_bytes(selected_files[0])
                if is_valid_image(image_bytes):
                    self.parent.profile_pic = image_bytes
                    self.Network.send_profile_pic(image_bytes)
                    print("send profile pic to server")
                    self.parent.activateWindow()
                    circular_pic = make_circular_image(image_bytes)
                    if circular_pic is not None:
                        set_icon_from_bytes_to_label(self.profile_image_label, circular_pic)
                        self.parent.update_profile_pic_dicts_list(self.parent.username, image_bytes, circular_pic)

    def font_size_changed(self, font_size):
        try:
            self.parent.font_size = int(font_size)
            self.font_size_label.setText(str(font_size))
        except Exception as e:
            print(f"font_size_changed error :{e}")

    def create_my_account_labels(self, x, y, font_size, text1, text2):
        label1 = self.create_custom_label(x, y, font_size, None, None, text1, "grey", False)
        label2 = self.create_custom_label(x, y+font_size+15, font_size, None, None, text2, "white", False)

    def change_input_mode(self):
        if self.parent.is_push_to_talk:
            self.parent.is_push_to_talk = False
        else:
            self.parent.is_push_to_talk = True
        self.parent.updated_settings_page()

    def create_colored_button(self, background_color, hover_color, border_color, x, y, width, height, text):
        new_button = QPushButton(text, self)
        if border_color is None:
            border_color = "#00000000"
        new_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {background_color};
                border: 2px solid {border_color};
                border-radius: 5px;
                padding: 8px 16px;
                padding-left: 35px;  /* Adjust the padding to move text to the right */
                color: white;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        new_button.setGeometry(x, y, width, height)

        return new_button

    def create_select_push_to_talk_key(self, x, y):
        red = "#FF0000"
        if self.parent.is_editing_push_to_talk_button:
            push_to_talk_label = self.push_to_talk_label(x, y, 20, 340, 50, self.parent.push_to_talk_key, "red", red)
        else:
            border_color = self.parent.standard_hover_color
            if self.parent.background_color == "Black and White":
                font_color = "black"
            else:
                font_color = "white"
            push_to_talk_label = self.push_to_talk_label(x, y, 20, 340, 50, self.parent.push_to_talk_key, font_color, border_color)

        hover_red = "#CC0000"  # Slightly darker than red

        grey = "#808080"
        hover_grey = "#6e6e6e"  # slightly darker than grey

        button_width = 160
        button_height = 37

        if self.parent.is_editing_push_to_talk_button:
            record_keybind_button = self.create_colored_button(red, hover_red, red, x + 170, y+6, button_width, button_height, "Stop Recording")
            record_keybind_button.clicked.connect(self.handle_push_to_talk_selection_button_clicked)
        else:
            edit_keybind_button = self.create_colored_button(grey, hover_grey, grey, x+170, y+6, button_width, button_height, "Edit Keybind")
            edit_keybind_button.clicked.connect(self.handle_push_to_talk_selection_button_clicked)

    def create_slider(self, min_value, max_value, value, connected_function, x, y, width, height, style_sheet):
        volume_slider = QSlider(Qt.Horizontal, self)
        volume_slider.setMinimum(min_value)
        volume_slider.setMaximum(max_value)
        volume_slider.setValue(value)  # Set initial volume
        volume_slider.valueChanged.connect(connected_function)
        volume_slider.setGeometry(x, y, width, height)
        volume_slider.setStyleSheet(style_sheet)
        return volume_slider

    def handle_push_to_talk_selection_button_clicked(self):
        if self.parent.is_editing_push_to_talk_button:
            self.parent.is_editing_push_to_talk_button = False
        else:
            self.parent.is_editing_push_to_talk_button = True
        self.parent.updated_settings_page()

    def push_to_talk_label(self, x, y, font_size, width, height, text, color, border_color):
        brighter_blue = self.parent.standard_hover_color
        if text is None:
            label = QLabel("None", self)
        else:
            label = QLabel(text, self)
        if width is None and height is None:
            label.move(x, y)
        else:
            label.setGeometry(x, y, width, height)


        label.setStyleSheet(f"""
            QLabel {{
                background-color: {brighter_blue};
                border: 2px solid {border_color};
                border-radius: 5px;
                padding: 8px 16px;
                color: {color};
                font-family: Arial, sans-serif;
                font-size: {font_size}px;
                font-weight: normal;
                text-align: left;
            }}

        """)

        return label

    def create_input_mode_select_button(self, starter_y, buttons_x):
        regular_blue = "#192549"
        brighter_blue = self.parent.standard_hover_color
        width_buttons = 620
        height_buttons = 50
        selected_path = "discord_app_assets/select_circle.png"
        not_selected_path = "discord_app_assets/not_select_circle.png"
        icons_size = 30
        no_background_color = "transparent"
        border_color = self.parent.standard_hover_color
        if not self.parent.is_push_to_talk:
            text1 = "Voice Activity"
            voice_activity_button = self.create_colored_button(no_background_color, brighter_blue, border_color, buttons_x, starter_y, width_buttons,height_buttons, text1)
            text2 = "Push to Talk"
            second_button_y = starter_y + 60
            push_to_talk_button = self.create_colored_button(no_background_color, brighter_blue, border_color, buttons_x, second_button_y, width_buttons,height_buttons, text2)
            voice_activity_button.clicked.connect(self.change_input_mode)
            push_to_talk_button.clicked.connect(self.change_input_mode)

            selected_button_image = self.create_image_label(selected_path, icons_size, icons_size, buttons_x + 5, starter_y+10)
            not_selected_button_image = self.create_image_label(not_selected_path, icons_size, icons_size, buttons_x + 5, second_button_y + 10)
        else:
            text1 = "Voice Activity"
            voice_activity_button = self.create_colored_button(no_background_color, brighter_blue, border_color, buttons_x, starter_y, width_buttons, height_buttons, text1)
            text2 = "Push to Talk"
            second_button_y = starter_y + 60
            push_to_talk_button = self.create_colored_button(no_background_color, brighter_blue, border_color, buttons_x, second_button_y, width_buttons,height_buttons, text2)
            voice_activity_button.clicked.connect(self.change_input_mode)
            push_to_talk_button.clicked.connect(self.change_input_mode)

            selected_button_image = self.create_image_label(selected_path, icons_size, icons_size, buttons_x + 5, second_button_y + 10)
            not_selected_button_image = self.create_image_label(not_selected_path, icons_size, icons_size, buttons_x + 5, starter_y + 10)
        if self.parent.background_color == "Black and White":
            push_to_talk_button.setStyleSheet(push_to_talk_button.styleSheet() + "color: black;")
            voice_activity_button.setStyleSheet(voice_activity_button.styleSheet() + "color: black;")

    def create_option_box(self, width, height, x, y, item_list):
        color_combobox = CustomComboBox(self)

        if len(item_list) > 0:
            for i in item_list:
                color_combobox.addItem(i)
        else:
            color_combobox.addItem("No Devices Found")

        color_combobox.setStyleSheet(self.combo_box_style_sheet)

        color_combobox.setGeometry(x, y, width, height)
        icon_path = "discord_app_assets/down_arrow_icon.png"
        arrow_label = self.create_image_label(icon_path, 30, x + (width * 0.87), x + (width * 0.87), y + 10)
        color_combobox.visibility_changed.connect(lambda is_visible: self.handle_combobox_visibility_changed(is_visible, arrow_label))
        arrow_label.mousePressEvent = lambda event: color_combobox.showPopup()

        return color_combobox

    def handle_combobox_visibility_changed(self, is_visible, arrow_label):
        if is_visible:
            arrow_label.setPixmap(
                QPixmap("discord_app_assets/up_arrow_icon.png").scaledToWidth(30, Qt.SmoothTransformation))
        else:
            arrow_label.setPixmap(
                QPixmap("discord_app_assets/down_arrow_icon.png").scaledToWidth(30, Qt.SmoothTransformation))

    def create_image_label(self, image_path, height, width, x, y):
        image_label = QLabel(self)
        image_label.setStyleSheet("background-color: transparent;")
        icon_path = image_path
        button_icon = QIcon(icon_path)
        pixmap = button_icon.pixmap(width, height)
        image_label.setPixmap(pixmap)
        image_label.move(x, y)
        return image_label

    def create_white_label(self, x, y, font_size, width, height, text):
        white_label = self.create_custom_label(x, y, font_size, width, height, text, "white", True)
        return white_label

    def create_custom_label(self, x, y, font_size, width, height, text, color=None, is_bold=False):
        custom_label = QLabel(text, self)
        if width is None and height is None:
            custom_label.move(x, y)
        else:
            custom_label.setGeometry(x, y, width, height)

        # Set text color
        if color is None:
            color = "white"  # Default color is white if not specified
        custom_label.setStyleSheet("color: {}; font-size: {}pt;".format(color, font_size))

        # Set text weight to bold if specified
        if is_bold:
            custom_label.setStyleSheet(custom_label.styleSheet() + "font-weight: bold;")

        return custom_label

    def change_username_function(self):
        # Implement the function for changing the username
        pass

    def change_password_function(self):
        # Implement the function for changing the password
        pass

    def delete_account_function(self):
        # Implement the function for deleting the account
        pass

    def set_volume(self, value):
        self.parent.volume = value
        self.volume_label.setText(str(value))
        self.parent.update_media_players_volume(value)

    def my_account_pressed(self):
        if self.parent.selected_settings !="My Account":
            self.parent.selected_settings = "My Account"
            self.parent.updated_settings_page()

    def user_profile_pressed(self):
        if self.parent.selected_settings != "User Profile":
            self.parent.selected_settings = "User Profile"
            self.parent.updated_settings_page()

    def appearance_pressed(self):
        if self.parent.selected_settings != "Appearance":
            self.parent.selected_settings = "Appearance"
            self.parent.updated_settings_page()

    def voice_video_pressed(self):
        if self.parent.selected_settings != "Voice & Video":
            self.parent.selected_settings = "Voice & Video"
            self.parent.updated_settings_page()

    def privacy_safety(self):
        if self.parent.selected_settings != "Privacy & Safety":
            self.parent.selected_settings = "Privacy & Safety"
            self.parent.updated_settings_page()

    def create_settings_main_buttons(self, text, funcion, position):

        button_text = text

        button = QPushButton(self)
        button.setText(button_text)
        button.move(position[0], position[1])
        button.setFixedHeight(self.settings_button_height)
        button.clicked.connect(funcion)

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.parent.background_color_hex};
                border: 2px solid {self.parent.standard_hover_color};
                border-radius: 5px;
                padding: 8px 16px;
                padding-left: 35px;  /* Adjust the padding to move text to the right */
                color: white;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                text-align: left;
            }}

            QPushButton:hover {{
                background-color: {self.parent.standard_hover_color};
            }}

            QPushButton:pressed {{
                background-color: #202225;
                border-color: #72767d;
            }}
        """)

        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedWidth(350)
        button.raise_()

        return button

    def generate_button_stylesheet(self, normal_color, hover_color, pressed_color):
        return f"""
            QPushButton {{
                background-color: {normal_color};
                border: 2px solid {self.parent.standard_hover_color};
                border-radius: 5px;
                padding: 8px 16px;
                padding-left: 35px;  /* Adjust the padding to move text to the right */
                color: white;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                text-align: left;
            }}

            QPushButton:hover {{
                background-color: {hover_color};
            }}

            QPushButton:pressed {{
                background-color: {pressed_color};
                border-color: #72767d;
            }}
        """


class CustomComboBox(QComboBox):
    visibility_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(CustomComboBox, self).__init__(parent)

    def showPopup(self):
        super(CustomComboBox, self).showPopup()
        self.visibility_changed.emit(True)

    def hidePopup(self):
        super(CustomComboBox, self).hidePopup()
        self.visibility_changed.emit(False)