from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QColor
from PyQt5.QtCore import pyqtSignal
from functools import partial
from discord_comms_protocol import client_net
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter, QPainterPath
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PIL import Image
from io import BytesIO
import base64
import binascii
import zlib
import pygetwindow
import numpy as np
from PIL import Image, ImageDraw
import webbrowser


def open_image_bytes(image_bytes):
    """Opens an image from bytes using the default image viewer application.

    Args:
        image_bytes (bytes): The image data as bytes.

    Returns:
        bool: True if the image was opened successfully, False otherwise.
    """
    try:
        # Create a temporary file to save the image bytes
        with open("temp_image.png", "wb") as f:
            f.write(image_bytes)

        # Open the temporary file using the default image viewer application
        webbrowser.open("temp_image.png")

        return True

    except Exception as e:
        print(f"Error opening image: {e}")
        return False

def make_circular_image1(image_path_or_bytes):
    """Converts an image to a circular image.

    Args:
        image_path_or_bytes (str or bytes): Path to the image file or image data as bytes.

    Returns:
        bytes: The circular image as bytes.
    """
    try:
        # Load the image using Pillow
        if isinstance(image_path_or_bytes, str):
            with open(image_path_or_bytes, 'rb') as f:
                image_data = f.read()
            # Determine file format from file extension
            file_extension = image_path_or_bytes.split('.')[-1].upper()
            format = 'JPEG' if file_extension in ['JPG', 'JPEG'] else file_extension
        else:
            image_data = image_path_or_bytes
            format = None

        # Open the image using BytesIO
        with BytesIO(image_data) as image_buffer:
            image = Image.open(image_buffer)

            # Convert the image to RGBA mode (if not already)
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # Determine the maximum circular area based on image dimensions
            width, height = image.size
            max_radius = min(width // 2, height // 2)

            # Create a mask with a transparent circle
            mask = Image.new('L', (width, height), 0)  # Create a black mask
            draw = ImageDraw.Draw(mask)
            draw.ellipse(((width - max_radius * 2) // 2, (height - max_radius * 2) // 2,
                        (width + max_radius * 2) // 2, (height + max_radius * 2) // 2), fill=255)

            # Apply the mask to the image
            circular_image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            circular_image.paste(image, mask=mask)

            # Convert the circular image to bytes
            output_buffer = BytesIO()
            circular_image.save(output_buffer, format=format)
            circular_image_bytes = output_buffer.getvalue()

        return circular_image_bytes

    except Exception as e:
        print(f"Error converting image: {e}")
        return None

def make_circular_image(image_path_or_bytes):
    """Converts an image to a circular image.

    Args:
        image_path_or_bytes (str or bytes): Path to the image file or image data as bytes.

    Returns:
        bytes: The circular image as bytes.
    """
    try:
        # Load the image using Pillow
        if isinstance(image_path_or_bytes, str):
            with open(image_path_or_bytes, 'rb') as f:
                image_data = f.read()
        else:
            image_data = image_path_or_bytes

        # Determine the file format from the provided bytes
        with BytesIO(image_data) as image_buffer:
            image = Image.open(image_buffer)

            # Convert the image to RGBA mode (if not already)
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # Determine the maximum circular area based on image dimensions
            width, height = image.size
            max_radius = min(width // 2, height // 2)

            # Create a mask with a transparent circle
            mask = Image.new('L', (width, height), 0)  # Create a black mask
            draw = ImageDraw.Draw(mask)
            draw.ellipse(((width - max_radius * 2) // 2, (height - max_radius * 2) // 2,
                        (width + max_radius * 2) // 2, (height + max_radius * 2) // 2), fill=255)

            # Apply the mask to the image
            circular_image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            circular_image.paste(image, mask=mask)

            # Convert the circular image to bytes
            output_buffer = BytesIO()
            circular_image.save(output_buffer, format='PNG')  # Save as PNG format
            circular_image_bytes = output_buffer.getvalue()

        return circular_image_bytes

    except Exception as e:
        print(f"Error converting image: {e}")
        return None

def create_custom_circular_label(width, height, parent):
    label = QLabel(parent)

    label_size = QSize(width, height)
    label.setFixedSize(label_size)

    label.setStyleSheet("""
        QLabel {
            border-radius: """ + str(height // 2) + """px; /* Set to half of the label height */
        }
    """)

    return label


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


def image_to_bytes(file_path):
    with open(file_path, "rb") as file:
        image_bytes = file.read()
        return image_bytes


def check_active_cameras():
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            return True
        else:
            return False
    except Exception as e:
        print(f"could not find active camera, error: {e}")
        return False


def set_icon_from_bytes_to_label(label, image_bytes):
    # Load the image from bytes
    pixmap = QPixmap()
    pixmap.loadFromData(image_bytes)
    # Set the icon to the label with the exact width and height of the label
    image_aspect_ratio = pixmap.width() / pixmap.height()
    if image_aspect_ratio <= 0.5:
        x = pixmap.scaledToWidth(label.width())
    elif image_aspect_ratio >= 1.5:
        x = pixmap.scaledToHeight(label.height())
    else:
        x = pixmap.scaledToWidth(label.width()).scaledToHeight(label.height())
    label.setPixmap(x)
    label.setAlignment(Qt.AlignCenter)


def set_icon_to_label(label, icon_path, width=None, height=None):
    # Create QIcon object from the provided icon path
    icon = QIcon(icon_path)

    # Get the size of the icon
    icon_size = icon.availableSizes()[0]  # Get the size of the icon
    icon_width = width if width is not None else icon_size.width()
    icon_height = height if height is not None else icon_size.height()

    # Set the icon to the label
    label.setPixmap(icon.pixmap(icon_width, icon_height))


def set_icon_to_circular_label(label, icon_path, width=None, height=None):
    # Create QIcon object from the provided icon path
    icon = QIcon(icon_path)

    # Get the size of the icon
    icon_size = icon.availableSizes()[0]
    icon_width = width if width is not None else icon_size.width()
    icon_height = height if height is not None else icon_size.height()

    # Load the icon pixmap
    pixmap = icon.pixmap(icon_width, icon_height)

    # Create a transparent QImage with the same size as the icon
    image = QImage(pixmap.size(), QImage.Format_ARGB32)
    image.fill(Qt.transparent)

    # Create a QPainter to draw on the image
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)

    # Create a circular path
    path = QPainterPath()
    path.addEllipse(image.rect())

    # Set the painter to use the circular path as a clipping path
    painter.setClipPath(path)

    # Draw the icon onto the circular area
    painter.drawPixmap(0, 0, pixmap)

    # End painting
    painter.end()

    # Set the circular icon to the label
    label.setPixmap(QPixmap.fromImage(image))


def set_icon_to_circular_label_from_bytes(label, image_bytes, width=None, height=None):
    # Create QIcon object from the provided icon path
    pixmap = QPixmap()
    pixmap.loadFromData(image_bytes)
    set_icon_to_circular_label(label, pixmap, width, height)


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


def calculate_font_size(text):
    # You can adjust the coefficients for the linear relationship
    base_size = 28
    reduction_factor = 1

    return max(base_size - reduction_factor * len(text), 10)  # Ensure the minimum font size is 10


def filter_and_sort_chats(search_str, chat_list):
    # Check if chat_list is a list of tuples or a list of strings
    if len(chat_list) == 0:
        return []
    if isinstance(chat_list[0], tuple):
        # Filter out tuples where chat_name does not contain the search_str
        if not search_str:
            return chat_list
        filtered_chats = [(chat_name, unread_messages) for chat_name, unread_messages in chat_list if
                          search_str.lower() in chat_name.lower()]

        # Sort the filtered_chats based on relevance to the search_str
        sorted_chats = sorted(filtered_chats,
                              key=lambda x: (not x[0].lower().startswith(search_str.lower()), x[0].lower()))
        return sorted_chats
    elif isinstance(chat_list[0], str):
        # Filter out strings that do not contain the search_str
        if not search_str:
            return chat_list
        filtered_chats = [chat_name for chat_name in chat_list if search_str.lower() in chat_name.lower()]

        # Sort the filtered_chats based on relevance to the search_str
        sorted_chats = sorted(filtered_chats,
                              key=lambda x: (not x.lower().startswith(search_str.lower()), x.lower()))
        return sorted_chats
    else:
        # Handle other cases or raise an exception based on your requirements
        raise ValueError("Invalid format for chat_list")


def calculate_division_value(friends_list_length):
    if friends_list_length == 0:
        return 0
    elif 1 <= friends_list_length <= 5:
        return 1
    else:
        return friends_list_length // 5


def gets_group_attributes_from_format(group_format):
    if "(" not in group_format:
        return group_format, None
    else:
        parts = group_format.split(")")
        id = parts[0][1]
        name = parts[1]
        return name, int(id)


class ChatBox(QWidget):

    def __init__(self, chat_name, messages_list, friends_list, Network, parent=None):
        super().__init__()

        self.Network = Network
        self.parent = parent
        self.is_getting_called = self.parent.is_getting_called
        self.square_label = QLabel(self)
        self.width_of_chat_box = 800
        self.height_of_chat_box = 1000
        self.file_dialog = QFileDialog(self)
        self.file_dialog.setFileMode(QFileDialog.ExistingFile)
        self.file_dialog.setNameFilter("Image files (*.png)")
        self.image_file_name = ""
        self.image_height = 100 * 3
        self.image_width = 100 * 2.3
        self.chats_buttons_list = []
        self.border_labels = []
        self.buttons_style_sheet = """
        QPushButton {
            color: white;
            font-size: 16px;
            background-color: rgba(0, 0, 0, 0); /* Transparent background */
            border: 2px solid #2980b9; /* Use a slightly darker shade for the border */
            border-radius: 5px;
            }
                        QPushButton:hover {
                background-color: #2980b9;
            }
        """
        self.call_button_style_sheet = """
            QPushButton {
                color: white;
                font-size: 16px;
                background-color: rgba(0, 0, 0, 0); /* Transparent background */
            }
            QPushButton:hover {
                filter: brightness(80%); /* Adjust the brightness to make it darker */
            }
        """

        self.create_group_open = QPushButton(self)

        # Load an image and set it as the button's icon
        icon = QIcon("discord_app_assets/add_image_button.png")
        self.create_group_open.setIcon(icon)

        # Set the desired size for the button
        button_size = QSize(25, 25)  # Adjust this to your desired button size
        self.create_group_open.setFixedSize(button_size)

        # Scale the icon while keeping its aspect ratio
        icon_size = QSize(25, 25)  # Set your desired icon size
        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

        # Set the scaled icon size for the button
        self.create_group_open.setIconSize(scaled_size)
        self.create_group_open.setStyleSheet("""            
         QPushButton {
            background-color: transparent;
            }
        QPushButton:pressed {
            background-color: #202225;
            border-color: #72767d;
        }
        """)
        self.create_group_open_x = 570
        self.create_group_open_y = 143
        self.create_group_open.move(self.create_group_open_x, self.create_group_open_y)
        self.create_group_open.clicked.connect(self.create_group_clicked)
        self.text_entry = QLineEdit(self)
        self.text_entry.hide()

        ringing_square_label_x = 1500
        ringing_square_label_width = 240
        self.ringing_square_label = QLabel(self)
        self.ringing_square_label.setGeometry(ringing_square_label_x, 200, ringing_square_label_width, 400)
        self.ringing_square_label.setStyleSheet(f"background-color: {self.parent.background_color}; border: 5px #2980b9;")
        self.ringing_square_label.move(ringing_square_label_x, 220)

        self.square_pos = (600, 0)
        self.square_label.setGeometry(self.square_pos[0], self.square_pos[1], self.width_of_chat_box,
                                      self.height_of_chat_box)
        self.square_label.setStyleSheet(f"background-color: {self.parent.background_color}; border: 5px solid #2980b9;")

        around_name_y = self.square_pos[1]
        around_name_x = self.square_pos[0]
        self.around_name = QLabel(self)
        self.around_name.setStyleSheet(f"background-color: {self.parent.background_color}; border: 5px solid #2980b9;")
        start_height_of_around_name = 50
        height_of_around_name = 50
        self.around_name_delta = 220
        if (self.parent.is_calling and self.parent.selected_chat == self.parent.calling_to) or \
                (self.parent.is_in_a_call and self.parent.selected_chat == self.parent.in_call_with):
            height_of_around_name = start_height_of_around_name + self.around_name_delta

        self.call_profiles_list = []

        self.current_chat, self.current_group_id = gets_group_attributes_from_format(self.parent.selected_chat)
        if self.current_group_id:
            if self.parent.is_call_dict_exist_by_group_id(self.current_group_id):
                height_of_around_name = start_height_of_around_name + self.around_name_delta
            else:
                print(self.parent.call_dicts)

        self.around_name.setGeometry(self.square_pos[0], around_name_y, self.width_of_chat_box, height_of_around_name)
        self.around_name.move(around_name_x, around_name_y)
        self.around_name.raise_()

        self.call_profiles_list = []


        if self.parent.selected_chat != "":
            self.ringing_square_label = QLabel(self)
            ringing_square_label_x = 1500
            ringing_square_label_width = 240

            self.send_image_button = QPushButton(self)

            # Load an image and set it as the button's icon
            icon = QIcon("discord_app_assets/add_image_button.png")
            self.send_image_button.setIcon(icon)

            # Set the desired size for the button
            button_size = QSize(35, 35)  # Adjust this to your desired button size
            self.send_image_button.setFixedSize(button_size)

            # Scale the icon while keeping its aspect ratio
            icon_size = QSize(35, 35)  # Set your desired icon size
            icon_actual_size = icon.actualSize(icon.availableSizes()[0])
            scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

            # Set the scaled icon size for the button
            self.send_image_button.setIconSize(scaled_size)
            self.send_image_y = 928
            self.send_image_button.move(610, self.send_image_y)
            self.send_image_button.setStyleSheet("""            
            QPushButton:hover {
                background-color: #2980b9;
            }
             QPushButton {
                background-color: transparent;
                }
            QPushButton:pressed {
                background-color: #202225;
                border-color: #72767d;
            }
            """)
            self.send_image_button.clicked.connect(self.open_image_file_dialog)

            if self.parent.is_calling and self.parent.selected_chat == self.parent.calling_to:
                try:
                    y_of_label = 95
                    rings_to_x = 920
                    if self.parent.selected_chat.startswith("("):
                        text = f"Ringing Group..."
                    else:
                        text = f"Ringing User..."
                    self.ringing_to_label = QLabel(text, self)
                    self.ringing_to_label.setStyleSheet("color: gray; font-size: 14px; margin: 10px;")
                    self.ringing_to_label.move(rings_to_x, y_of_label)
                    text_1_width = self.ringing_to_label.width()

                    text = f"{self.parent.calling_to}"
                    self.calling_to_label = QLabel(text, self)
                    self.calling_to_label.setStyleSheet("color: white; font-size: 25px; margin: 10px;")
                    text_2_width = self.calling_to_label.width()
                    self.calling_to_label.move(rings_to_x + (text_1_width - text_2_width), y_of_label + 20)

                    self.stop_calling_button = QPushButton(self)

                    # Set button styles
                    button_size = QSize(50, 50)  # Adjust this to your desired button size
                    self.stop_calling_button.setFixedSize(button_size)
                    icon_size = QSize(35, 35)  # Set your desired icon size
                    icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                    icon = QIcon("discord_app_assets/reject_button.png")
                    self.stop_calling_button.setIcon(icon)
                    icon_size = QSize(65, 65)  # Set your desired icon size
                    icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                    scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
                    self.stop_calling_button.setIconSize(scaled_size)
                    self.stop_calling_button.setObjectName("stop_calling_button")
                    original_style_sheet = self.buttons_style_sheet

                    # Define a more specific style for self.stop_calling_button
                    specific_style = """
                        QPushButton#stop_calling_button {
                            border: none;
                        }
                    """

                    # Append the specific style for self.stop_calling_button to the original style sheet
                    modified_style_sheet = original_style_sheet + specific_style

                    # Apply the modified style sheet to the button
                    self.stop_calling_button.setStyleSheet(modified_style_sheet)
                    self.stop_calling_button.move(rings_to_x + (text_1_width // 2) - 15, y_of_label + 110)
                    self.stop_calling_button.clicked.connect(self.stop_calling)
                except Exception as e:
                    print(f"error in showing calling {e}")

            if self.parent.is_getting_called:
                pop_up_x = 850
                pop_up_y = 250
                pop_up_width = 200
                pop_up_height = 300

                text = f"Incoming Call..."
                y_of_label = pop_up_y + 120
                self.incoming_call_label = QLabel(text, self)
                self.incoming_call_label.setStyleSheet("color: gray; font-size: 14px; margin: 10px "
                                                       ";background-color: transparent;")
                self.incoming_call_label.move(pop_up_x + 45, y_of_label)

                text = f"{self.parent.getting_called_by}"
                self.caller_label = QLabel(text, self)
                start_point = int(len(text) - 4) * 1
                font_size = calculate_font_size(text)
                if start_point < 0:
                    start_point = pop_up_x + 50
                else:
                    start_point = pop_up_x + 50 - start_point

                self.caller_label.setStyleSheet(f"color: white; font-size: {font_size}px; margin: 10px; "
                                                "background-color: transparent;")
                self.caller_label.move(start_point, y_of_label - 30)

                self.pop_up_label = QLabel(self)
                custom_color = QColor("#053d76")
                self.pop_up_label.setStyleSheet(f"background-color: {custom_color.name()};")
                self.pop_up_label.setGeometry(pop_up_x, pop_up_y, pop_up_width, pop_up_height)

                self.accept_button = QPushButton(self)
                self.reject_button = QPushButton(self)

                # Set button styles
                button_size = QSize(35, 35)  # Adjust this to your desired button size
                self.accept_button.setFixedSize(button_size)
                self.reject_button.setFixedSize(button_size)
                # Set button icons (assuming you have phone icons available)

                icon = QIcon("discord_app_assets/accept_button.png")
                self.accept_button.setIcon(icon)
                icon_size = QSize(50, 50)  # Set your desired icon size
                icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

                self.accept_button.setIconSize(scaled_size)
                self.accept_button.setStyleSheet(self.call_button_style_sheet)
                icon = QIcon("discord_app_assets/reject_button.png")
                self.reject_button.setIcon(icon)
                icon_size = QSize(50, 50)  # Set your desired icon size
                icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
                self.reject_button.setIconSize(scaled_size)
                # Set button positions
                accept_button_x = pop_up_x + 115
                reject_button_x = pop_up_x + 50

                self.accept_button.move(accept_button_x, pop_up_y + 200)
                self.reject_button.move(reject_button_x, pop_up_y + 200)
                self.reject_button.setStyleSheet(self.call_button_style_sheet)
                # Connect button signals to functions
                self.accept_button.clicked.connect(self.accept_call)
                self.reject_button.clicked.connect(self.reject_call)
            if self.parent.is_in_a_call and self.parent.selected_chat == self.parent.in_call_with:
                try:
                    share_camera_height = 45
                    share_camera_button_width = 45
                    share_camera_x = 840
                    share_camera_y = 215
                    self.share_camera_off_icon = QIcon("discord_app_assets/no_camera_icon.png")
                    self.share_camera_on_icon = QIcon("discord_app_assets/camera_icon.png")
                    self.share_camera_button = self.create_custom_in_call_button(share_camera_height, share_camera_button_width, share_camera_x,
                                                                        share_camera_y, self.share_camera_and_unshare)
                    share_screen_height = 45
                    share_screen_button_width = 45
                    share_screen_x = 905
                    share_screen_y = 215
                    self.share_screen_button = self.create_custom_in_call_button(share_screen_height,
                                                                                 share_screen_button_width,
                                                                                 share_screen_x,
                                                                                 share_screen_y,
                                                                                 self.share_screen_and_unshare)
                    try:
                        try:
                            if self.parent.is_camera_shared:
                                set_button_icon(self.share_camera_button, self.share_camera_on_icon, share_camera_height, share_camera_button_width)
                            else:
                                set_button_icon(self.share_camera_button, self.share_camera_off_icon, share_camera_height,
                                                     share_camera_button_width)
                        except Exception as e:
                            print(f"error in setting camera icon {e}")

                        self.share_screen_off_icon = QIcon("discord_app_assets/share_screen_off_icon.png")
                        self.share_screen_on_icon = QIcon("discord_app_assets/share_screen_on_icon.png")
                        try:
                            if self.parent.is_screen_shared:
                                set_button_icon(self.share_screen_button, self.share_screen_on_icon, share_screen_height, share_screen_button_width)
                            else:
                                set_button_icon(self.share_screen_button, self.share_screen_off_icon, share_screen_height,
                                                     share_screen_button_width)
                        except Exception as e:
                            print(f"error in setting icon for share screen button{e}")
                    except Exception as e:
                        print(f"error in creating shares buttons {e}")

                    deafen_button_height = 45
                    deafen_button_width = 45
                    self.deafened_icon = QIcon("discord_app_assets/deafened.png")
                    self.not_deafened_icon = QIcon("discord_app_assets/not_deafened.png")
                    deafen_x = share_screen_x + 65
                    deafen_y = share_screen_y
                    self.deafen_button = self.create_custom_in_call_button(deafen_button_width, deafen_button_height, deafen_x, deafen_y, self.deafen_and_undeafen)
                    if self.parent.deafen:
                        set_button_icon(self.deafen_button, self.deafened_icon, deafen_button_width, deafen_button_height)
                    else:
                        set_button_icon(self.deafen_button, self.not_deafened_icon, deafen_button_width,
                                             deafen_button_height)


                    mic_button_height = 45
                    mic_button_width = 45
                    self.unmuted_mic_icon = QIcon("discord_app_assets/mic_not_muted_icon.png")
                    self.muted_mic_icon = QIcon("discord_app_assets/mic_muted_icon.png")
                    mic_x = deafen_x + 65
                    mic_button_y = share_screen_y
                    self.mic_button = self.create_custom_in_call_button(mic_button_width, mic_button_height, mic_x, mic_button_y, self.mute_and_unmute)
                    if self.parent.mute:
                        set_button_icon(self.mic_button, self.muted_mic_icon, mic_button_width, mic_button_height)
                    else:
                        set_button_icon(self.mic_button, self.unmuted_mic_icon, mic_button_width, mic_button_height)

                    self.end_call_button = QPushButton(self)

                    # Set button styles
                    call_button_height = 70
                    call_button_width = 70
                    button_size = QSize(call_button_width, call_button_height)  # Adjust this to your desired button size
                    self.end_call_button.setFixedSize(button_size)
                    set_button_icon(self.end_call_button, "discord_app_assets/reject_button.png", call_button_width, call_button_height)
                    self.end_call_button.setStyleSheet(self.call_button_style_sheet)
                    end_call_button_x = mic_x + 55
                    self.end_call_button.move(end_call_button_x,
                                              share_screen_y-15)
                    self.end_call_button.clicked.connect(self.end_current_call)
                    self.put_call_icons_on_the_screen()
                except Exception as e:
                    print(f"error in incall func {e}")


            # Load an image and set it as the button's icon
            icon = QIcon("discord_app_assets/ringing_blue_icon.png")
            call_button_x = 600 + (self.width_of_chat_box // 2) + 340
            call_button_y = 8
            self.call_button = self.create_top_page_button(call_button_x, call_button_y, icon)
            self.call_button.clicked.connect(self.call_user)
            icon = QIcon("discord_app_assets/add_user.png")
            add_user_x = call_button_x - 50
            add_user_y = call_button_y
            self.add_user_button = self.create_top_page_button(add_user_x, add_user_y, icon)

            if self.current_group_id:
                group_manager = self.parent.get_group_manager_by_group_id(self.current_group_id)
                if group_manager == self.parent.username:
                    icon = QIcon("discord_app_assets/edit_name.png")
                    rename_group_x = add_user_x - 50
                    rename_group_y = call_button_y
                    self.rename_group = self.create_top_page_button(rename_group_x, rename_group_y, icon)
                # if in chat where there is a group call gives option to join
                if self.current_group_id:
                    if self.parent.is_call_dict_exist_by_group_id(self.current_group_id) and not self.parent.is_in_a_call:

                        icon_size = 60
                        y_of_label = 95
                        rings_to_x = 920
                        icon = QIcon("discord_app_assets/accept_button.png")

                        join_button_x = rings_to_x + (35 // 2) + 15
                        join_button_y = y_of_label + 110
                        join_button_width_or_height = 50
                        self.join_call_button = self.create_custom_in_call_button(join_button_width_or_height, join_button_width_or_height,
                                                                                  join_button_x, join_button_y,  self.join_call)
                        set_button_icon(self.join_call_button, icon, icon_size, icon_size)
                        self.put_call_icons_on_the_screen()

            self.text_entry = QLineEdit(self)
            self.text_entry.setGeometry(10, 10, self.width_of_chat_box-70, 40)
            self.text_entry.setStyleSheet(
                "background-color: #2980b9; color: white; padding: 10px; border: 1px solid #2980b9; border-radius: 5px; font-size: 14px;")
            text_entry_y = self.send_image_y
            self.text_entry.move(650, text_entry_y)
            text = self.current_chat.replace("/", "")
            place_holder_text = "Message" + " " + text
            self.text_entry.setPlaceholderText(place_holder_text)
            self.send_image_button.raise_()
        else:
            if self.parent.is_getting_called:
                pop_up_x = 850
                pop_up_y = 250
                pop_up_width = 200
                pop_up_height = 300

                text = f"Incoming Call..."
                y_of_label = pop_up_y + 120
                self.incoming_call_label = QLabel(text, self)
                self.incoming_call_label.setStyleSheet("color: gray; font-size: 14px; margin: 10px "
                                                       ";background-color: transparent;")
                self.incoming_call_label.move(pop_up_x + 45, y_of_label)

                text = f"{self.parent.getting_called_by}"
                self.caller_label = QLabel(text, self)
                start_point = int(len(text) - 4) * 1
                font_size = calculate_font_size(text)
                if start_point < 0:
                    start_point = pop_up_x + 50
                else:
                    start_point = pop_up_x + 50 - start_point

                self.caller_label.setStyleSheet(f"color: white; font-size: {font_size}px; margin: 10px; "
                                                "background-color: transparent;")
                self.caller_label.move(start_point, y_of_label - 30)

                self.pop_up_label = QLabel(self)
                custom_color = QColor("#053d76")
                self.pop_up_label.setStyleSheet(f"background-color: {custom_color.name()};")
                self.pop_up_label.setGeometry(pop_up_x, pop_up_y, pop_up_width, pop_up_height)

                self.accept_button = QPushButton(self)
                self.reject_button = QPushButton(self)

                # Set button styles
                button_size = QSize(35, 35)  # Adjust this to your desired button size
                self.accept_button.setFixedSize(button_size)
                self.reject_button.setFixedSize(button_size)
                # Set button icons (assuming you have phone icons available)

                icon = QIcon("discord_app_assets/accept_button.png")
                self.accept_button.setIcon(icon)
                icon_size = QSize(50, 50)  # Set your desired icon size
                icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

                self.accept_button.setIconSize(scaled_size)
                self.accept_button.setStyleSheet(self.call_button_style_sheet)
                icon = QIcon("discord_app_assets/reject_button.png")
                self.reject_button.setIcon(icon)
                icon_size = QSize(50, 50)  # Set your desired icon size
                icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
                self.reject_button.setIconSize(scaled_size)
                # Set button positions
                accept_button_x = pop_up_x + 115
                reject_button_x = pop_up_x + 50

                self.accept_button.move(accept_button_x, pop_up_y + 200)
                self.reject_button.move(reject_button_x, pop_up_y + 200)
                self.reject_button.setStyleSheet(self.call_button_style_sheet)
                # Connect button signals to functions
                self.accept_button.clicked.connect(self.accept_call)
                self.reject_button.clicked.connect(self.reject_call)

        # List to store message labels
        self.chat_name_label = QLabel(self.current_chat.replace("/", ""), self)
        self.chat_name_label.setStyleSheet("color: white; font-size: 20px; margin: 10px;")
        # Set a fixed width for the label
        self.chat_name_label.setFixedWidth(200)
        chat_name_label_x = 620
        self.chat_name_label.move(chat_name_label_x, 3)
        self.messages_list = messages_list
        self.message_labels = []

        self.filename_label = QLabel(self)
        self.filename_label.move(620, 830)
        self.filename_label.setGeometry(620, 830, 200, 50)  # Adjust the size as needed
        self.filename_label.setWordWrap(True)  # Enable word wrap
        self.filename_label.raise_()
        self.filename_label.setStyleSheet(
            "background-color: #333333; color: white; font-size: 16px;"
        )
        self.filename_label.hide()
        if self.parent.image_file_name != "":
            self.filename_label.setText(self.parent.image_file_name + " is loaded")
            self.filename_label.show()
        else:
            self.filename_label.setText(self.parent.image_file_name)

        self.image_too_big = QLabel(self)
        self.image_too_big.move(620, 830)
        self.image_too_big.setGeometry(620, 830, 200, 50)  # Adjust the size as needed
        self.image_too_big.setWordWrap(True)  # Enable word wrap
        self.image_too_big.raise_()
        self.image_too_big.setStyleSheet(
            "background-color: #333333; color: red; font-size: 16px;"
        )
        self.image_too_big.setText("Image size it too big")
        if self.parent.size_error_label:
            self.image_too_big.show()
        else:
            self.image_too_big.hide()

        self.show_messages_on_screen(self.messages_list)

        style_sheet = '''
            color: white;
            font-size: 15px;
            margin-bottom: 2px;
        '''

        self.chats_label = QLabel("DIRECT MESSAGES", self)
        self.chats_label.setStyleSheet('''
            color: white;
            font-size: 12px;
            padding: 5px;
            margin-bottom: 2px;
        ''')
        self.friends_button_height = 50
        friend_starter_y = 170
        friend_x = 250
        self.chats_label.move(friend_x + 15, friend_starter_y - 28)
        friends_button_y = 90
        friends_button_height = self.friends_button_height
        border_height = 912
        border_width = 350
        info_y = 902
        self.border_label = QLabel(self)
        self.border_label.setStyleSheet('''
                        border: 2px solid #2980b9;
                        border-radius: 5px;
                        padding: 5px;
                        margin-bottom: 2px;
                    ''')
        self.border_label.setGeometry(friend_x, 0, border_width, border_height)
        self.border_label.lower()

        self.border_label2 = QLabel(self)
        self.border_label2.setStyleSheet('''

                            padding: 5px;
                            margin-bottom: 2px;
                            border-top: 2px solid #2980b9; /* Top border */
                            border-left: 2px solid #2980b9; /* Left border */
                            border-right: 2px solid #2980b9; /* Right border */
                        ''')
        self.border_label2.setGeometry(friend_x, 0, border_width, 170)
        self.border_label2.lower()

        find_contact_pos = (260, 20)
        find_contact_size = (320, 40)
        self.find_contact_text_entry = QLineEdit(self)
        self.find_contact_text_entry.setPlaceholderText("Find a conversation")
        self.find_contact_text_entry.setStyleSheet(
            "background-color: #2980b9; color: white; padding: 10px; border: 1px solid #2980b9; border-radius: 5px; font-size: 14px;")
        self.find_contact_text_entry.setGeometry(find_contact_pos[0], find_contact_pos[1], find_contact_size[0],
                                                 find_contact_size[1])
        self.find_contact_text_entry.textChanged.connect(self.on_text_changed_in_contact_search)

        self.friends_button = QPushButton("  Social", self)
        self.friends_button.setStyleSheet('''
            QPushButton {
            color: white;
            font-size: 15px;
            border: none;  /* Remove the border */
            border-radius: 5px;
            padding: 5px;
            margin-bottom: 2px;
            text-align: left;  /* Align the text to the left */
            alignment: left;   /* Align the icon and text to the left */
            padding-left: 10px;   /* Adjust the starting position to the right */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }

            QPushButton:pressed {
                background-color: #202225;
                border-color: #72767d;
            }

        ''')
        icon = QIcon("discord_app_assets/friends_icon.png")  # Replace with the path to your icon image
        self.friends_button.setIcon(icon)

        # Set the position and size of the button
        self.friends_button.setGeometry(friend_x + 5, friends_button_y - 10, border_width - 15,
                                        friends_button_height)  # Adjust size as needed

        # Set the text alignment to show both the icon and text

        # Optional: Adjust the spacing between the icon and text
        self.friends_button.setIconSize(QSize(50, 50))  # Adjust size as needed
        self.friends_button.clicked.connect(self.parent.Social_clicked)

        try:
            if not self.parent.current_chat_box_search:
                self.drew_friends_buttons_on_screen_by_list(self.parent.chats_list)
            else:
                self.drew_friends_buttons_on_screen_by_list(self.parent.temp_search_list)
        except Exception as e:
            print(f"error in showing chats list{e}")

        username_label = QLabel(self.parent.username, self)
        username_label.setStyleSheet('''
            color: white;
            font-size: 18px;
            background-color: #2980b9;
            border: 2px solid #2980b9;  /* Use a slightly darker shade for the border */
            border-radius: 5px;
            padding: 5px;
            margin-bottom: 18px;
        ''')

        username_label.setGeometry(friend_x, info_y, border_width, 90)
        settings_button = QPushButton(self)
        settings_button.setFixedSize(50, 50)  # Set the fixed size of the button
        # Set the icon for the chat button
        settings_button_icon = QIcon(QPixmap("discord_app_assets/Setting_logo.png"))
        settings_button.setIcon(settings_button_icon)
        settings_button.setIconSize(settings_button_icon.actualSize(QSize(50, 50)))  # Adjust the size as needed
        settings_button.move(friend_x + 260, info_y + 5)
        settings_button.setStyleSheet('''
            QPushButton {
                background-color: transparent;
            }

            QPushButton:hover {
                background-color: #808080; /* Gray color for hover */
            }
        ''')
        settings_button.clicked.connect(self.parent.Settings_clicked)

        if self.parent.is_create_group_pressed:
            self.display_create_group_box()


        self.raise_needed_elements()

    # Layout



    def create_custom_in_call_button(self, width, height, x, y, click_function):
        button = QPushButton(self)

        button_size = QSize(width, height)
        button.setFixedSize(button_size)

        button.move(x, y)

        button.clicked.connect(click_function)

        button.setStyleSheet("""
            QPushButton {
                background-color: #6fa8b6;
                background-repeat: no-repeat;
                background-position: center;
                border-radius: """ + str(height // 2) + """px;  /* Set to half of the button height */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        return button

    def put_call_icons_on_the_screen(self):
        try:
            if self.current_group_id:
                current_call_dict = self.parent.get_call_dict_by_group_id(self.current_group_id)
                print(f"dict is {current_call_dict}")
            else:
                current_call_dict = self.parent.get_call_dict_by_user(self.parent.username)
                print(f"dict is {current_call_dict}")
            numbers_of_users_in_call = len(current_call_dict.get("participants"))
            starts_x = 900+((numbers_of_users_in_call-2) * -70)
            y_of_profiles = 95

            names = current_call_dict.get("participants")
            for name in names:
                self.create_profile_button(starts_x, y_of_profiles, name, current_call_dict)
                if name in current_call_dict.get("screen_streamers") and name != self.parent.username:
                    stream_type = "ScreenStream"
                    self.create_watch_stream_button(starts_x+10, y_of_profiles-35, name, stream_type)
                if name in current_call_dict.get("camera_streamers") and name != self.parent.username:
                    stream_type = "CameraStream"
                    self.create_watch_stream_button(starts_x+10, y_of_profiles-35, name, stream_type)
                starts_x += 105
        except Exception as e:
            print(f"error is {e} in icon management")

    def create_watch_stream_button(self, x, y, name, stream_type):
        width, height = (70, 30)
        if stream_type == "ScreenStream":
            button = QPushButton(self)
            button_size = QSize(width, height)
            button.setFixedSize(button_size)
            image_icon = f"discord_app_assets/monitor_icon.png"
            set_button_icon(button, image_icon, width, height)  # Corrected function call
        else:
            y -= 50
            button = QPushButton(self)
            button_size = QSize(width, height)
            button.setFixedSize(button_size)
            image_icon = "discord_app_assets/camera_watch_icon.png"
            set_button_icon(button, image_icon, width, height)  # Corrected function call
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.parent.standard_hover_color}; 
                color: white; /* Default font color */
                border-radius: 15px; /* Adjust the radius as needed */
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
        """)
        button.move(x, y)

        button.clicked.connect(lambda: self.watch_stream_button_pressed(name, stream_type))
        self.call_profiles_list.append(button)

    def watch_stream_button_pressed(self, name, stream_type):
        try:
            if not self.parent.is_watching_screen:
                self.parent.is_watching_screen = True
                self.parent.watching_user = name
                self.parent.watching_type = stream_type
                if stream_type == "ScreenStream":
                    self.Network.watch_screen_stream_of_user(name)
                else:
                    self.Network.watch_camera_stream_of_user(name)
                print(f"Started watching stream of {name} of type: {stream_type}")
                self.parent.start_watching_video_stream()
            else:
                print("does not suppose to happen")
        except Exception as e:
            print(f"Problem with watch button, error {e}")

    def create_profile_button(self, x, y, name, dict):
        button = QPushButton(self)
        width, height = (90, 90)
        button_size = QSize(width, height)
        button.setFixedSize(button_size)

        button.move(x, y)
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                background-repeat: no-repeat;
                background-position: center;
                border-radius: """ + str(height // 2) + """px;  /* Set to half of the button height */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        muted_icon = QIcon("discord_app_assets/muted_profile.png")
        deafened_icon = QIcon("discord_app_assets/deafened_profile.png")
        regular_icon = QIcon("discord_app_assets/regular_profile.png")
        deafened = dict.get("deafened")
        muted = dict.get("muted")
        if name in dict.get("deafened"):
            set_button_icon(button, deafened_icon, width, height)
        elif name in dict.get("muted"):
            set_button_icon(button, muted_icon, width, height)
        else:
            set_button_icon(button, regular_icon, width, height)
        self.call_profiles_list.append(button)
        return button

    def create_top_page_button(self, x, y, icon_path):
        button = QPushButton(self)
        width, height = (35, 35)
        button_size = QSize(width, height)
        button.setFixedSize(button_size)

        button.move(x, y)
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                background-repeat: no-repeat;
                background-position: center;
                border-radius: """ + str(height // 2) + """px;  /* Set to half of the button height */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        set_button_icon(button, icon_path, width, height)
        return button


    def stop_calling(self):
        self.Network.stop_ringing_to_group_or_user()

    def create_group_clicked(self):
        if self.parent.is_create_group_pressed:
            self.parent.is_create_group_pressed = False
            self.parent.selected_group_members.clear()
            self.parent.create_group_index = 0
        else:
            self.parent.is_create_group_pressed = True
        self.parent.updated_chat()

        # Create Group button

    def display_add_users_to_group_box(self):
        starter_x = self.create_group_open_x
        starter_y_of_border = self.create_group_open_y + 50
        adding_border_height = 400
        adding_border_width = 300
        border_of_adding = QLabel(self)
        border_of_adding.setGeometry(starter_x, starter_y_of_border, adding_border_width, adding_border_height)
        border_of_adding.raise_()
        border_of_adding.setStyleSheet("""border: 2px solid black;  
        /* Use a slightly darker shade for the border */
                        border-radius: 5px;""")

        label = QLabel(f"Select friends", self)
        label.setStyleSheet("""color: white;font-size: 20px;""")
        label.move(starter_x + 20, starter_y_of_border + 10)

        label = QLabel(
            f"You can add {(self.parent.group_max_members - 1) - len(self.parent.selected_group_members)} more friends",
            self)
        label.setStyleSheet("""color: white;font-size: 14px;""")
        label.move(starter_x + 20, starter_y_of_border + 45)

        Page = 0
        if len(self.parent.friends_list) > 0:
            Page = self.parent.add_users_to_group_index + 1
        label = QLabel(f"Page({Page}/"
                       f"{calculate_division_value(len(self.parent.friends_list))})"
                       f"     "
                       f"Selected({len(self.parent.selected_group_members)})", self)
        label.setStyleSheet("""color: white;font-size: 12px;""")
        label.move(starter_x + 40, starter_y_of_border + 75)

        style_sheet = """
        QPushButton {
            color: white;
            font-size: 16px;
            background-color: rgba(0, 0, 0, 0); /* Transparent background */
            border: 2px solid #2980b9; /* Use a slightly darker shade for the border */
            border-radius: 5px;
            }
                        QPushButton:hover {
                background-color: #2980b9;
            }
        """
        scroll_up_button = QPushButton("↑", self)
        scroll_up_button.move(starter_x + 230, starter_y_of_border + 25)
        scroll_up_button.clicked.connect(lambda: self.handle_create_group_index("up"))
        scroll_up_button.setFixedWidth(50)
        scroll_up_button.setStyleSheet(style_sheet)

        scroll_down_button = QPushButton("↓", self)
        scroll_down_button.move(starter_x + 230, starter_y_of_border + 55)
        scroll_down_button.clicked.connect(lambda: self.handle_create_group_index("down"))
        scroll_down_button.setFixedWidth(50)
        scroll_down_button.setStyleSheet(style_sheet)

        starter_x = self.create_group_open_x
        starter_y = self.create_group_open_y + 150
        i = 0
        for friend in self.parent.friends_list:
            # self.parent.create_group_index default value is 0
            if i >= self.parent.add_users_to_group_index * 5:
                friend_label = QPushButton(friend, self)
                friend_label.friend_name = friend
                friend_label.setStyleSheet('''
                    color: white;
                    font-size: 18px;
                    border: 2px solid #2980b9;
                    border-radius: 5px;
                    padding: 5px;
                    margin-bottom: 18px;
                    text-align: left; /* Align text to the left */
                }

                QPushButton:hover {
                    background-color: #3498db; /* Bluish hover color */
                }
                ''')
                friend_label.clicked.connect(self.toggle_checkbox)
                friend_checkbox = QCheckBox(self)
                if friend in self.parent.selected_group_members:
                    friend_checkbox.setChecked(True)
                friend_checkbox.friend_name = friend  # Store friend's name as an attribute
                friend_checkbox.stateChanged.connect(self.friend_checkbox_changed)
                height = friend_label.height() + 30
                friend_label.setGeometry(starter_x + 10, starter_y, adding_border_width - 20, height)
                friend_checkbox.move(starter_x + 260, starter_y + 15)
                starter_y += friend_label.height() - 20
                friend_label.raise_()
                friend_checkbox.raise_()
            i += 1
        button = QPushButton("Create DM", self)
        button.move(starter_x + 15, starter_y_of_border + adding_border_height - 80)
        button.setFixedHeight(self.friends_button_height)
        button.clicked.connect(self.create_dm_pressed)

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.parent.background_color};
                border: 2px solid #2980b9;
                border-radius: 5px;
                padding: 8px 16px;
                color: #b9c0c7;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }}

            QPushButton:hover {{
                background-color: #2980b9;
            }}

            QPushButton:pressed {{
                background-color: #202225;
                border-color: #72767d;
            }}
        """)

        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedWidth(adding_border_width - 30)

    def display_create_group_box(self):
        starter_x = self.create_group_open_x
        starter_y_of_border = self.create_group_open_y + 50
        adding_border_height = 400
        adding_border_width = 300
        border_of_adding = QLabel(self)
        border_of_adding.setGeometry(starter_x, starter_y_of_border, adding_border_width, adding_border_height)
        border_of_adding.raise_()
        border_of_adding.setStyleSheet("""border: 2px solid black;  
        /* Use a slightly darker shade for the border */
                        border-radius: 5px;""")

        label = QLabel(f"Select friends", self)
        label.setStyleSheet("""color: white;font-size: 20px;""")
        label.move(starter_x + 20, starter_y_of_border + 10)

        label = QLabel(
            f"You can add {(self.parent.group_max_members - 1) - len(self.parent.selected_group_members)} more friends",
            self)
        label.setStyleSheet("""color: white;font-size: 14px;""")
        label.move(starter_x + 20, starter_y_of_border + 45)

        Page = 0
        if len(self.parent.friends_list) > 0:
            Page = self.parent.create_group_index + 1
        label = QLabel(f"Page({Page}/"
                       f"{calculate_division_value(len(self.parent.friends_list))})"
                       f"     "
                       f"Selected({len(self.parent.selected_group_members)})", self)
        label.setStyleSheet("""color: white;font-size: 12px;""")
        label.move(starter_x + 40, starter_y_of_border + 75)

        style_sheet = """
        QPushButton {
            color: white;
            font-size: 16px;
            background-color: rgba(0, 0, 0, 0); /* Transparent background */
            border: 2px solid #2980b9; /* Use a slightly darker shade for the border */
            border-radius: 5px;
            }
                        QPushButton:hover {
                background-color: #2980b9;
            }
        """
        scroll_up_button = QPushButton("↑", self)
        scroll_up_button.move(starter_x + 230, starter_y_of_border + 25)
        scroll_up_button.clicked.connect(lambda: self.handle_create_group_index("up"))
        scroll_up_button.setFixedWidth(50)
        scroll_up_button.setStyleSheet(style_sheet)

        scroll_down_button = QPushButton("↓", self)
        scroll_down_button.move(starter_x + 230, starter_y_of_border + 55)
        scroll_down_button.clicked.connect(lambda: self.handle_create_group_index("down"))
        scroll_down_button.setFixedWidth(50)
        scroll_down_button.setStyleSheet(style_sheet)

        starter_x = self.create_group_open_x
        starter_y = self.create_group_open_y + 150
        i = 0
        for friend in self.parent.friends_list:
            # self.parent.create_group_index default value is 0
            if i >= self.parent.create_group_index * 5:
                friend_label = QPushButton(friend, self)
                friend_label.friend_name = friend
                friend_label.setStyleSheet('''
                    color: white;
                    font-size: 18px;
                    border: 2px solid #2980b9;
                    border-radius: 5px;
                    padding: 5px;
                    margin-bottom: 18px;
                    text-align: left; /* Align text to the left */
                }

                QPushButton:hover {
                    background-color: #3498db; /* Bluish hover color */
                }
                ''')
                friend_label.clicked.connect(self.toggle_checkbox)
                friend_checkbox = QCheckBox(self)
                if friend in self.parent.selected_group_members:
                    friend_checkbox.setChecked(True)
                friend_checkbox.friend_name = friend  # Store friend's name as an attribute
                friend_checkbox.stateChanged.connect(self.friend_checkbox_changed)
                height = friend_label.height() + 30
                friend_label.setGeometry(starter_x + 10, starter_y, adding_border_width - 20, height)
                friend_checkbox.move(starter_x + 260, starter_y + 15)
                starter_y += friend_label.height() - 20
                friend_label.raise_()
                friend_checkbox.raise_()
            i += 1
        button = QPushButton("Create DM", self)
        button.move(starter_x + 15, starter_y_of_border + adding_border_height - 80)
        button.setFixedHeight(self.friends_button_height)
        button.clicked.connect(self.create_dm_pressed)

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.parent.background_color};
                border: 2px solid #2980b9;
                border-radius: 5px;
                padding: 8px 16px;
                color: #b9c0c7;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }}

            QPushButton:hover {{
                background-color: #2980b9;
            }}

            QPushButton:pressed {{
                background-color: #202225;
                border-color: #72767d;
            }}
        """)

        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedWidth(adding_border_width - 30)

    def toggle_checkbox(self):
        sender = self.sender()
        if isinstance(sender, QPushButton):
            friend_name = sender.friend_name
            friend_checkbox = next(
                child for child in sender.parent().children()
                if isinstance(child, QCheckBox) and child.friend_name == friend_name
            )
            friend_checkbox.toggle()
            self.friend_checkbox_changed(friend_checkbox.isChecked())

    def handle_create_group_index(self, format):
        change = False
        try:
            if format == "down":
                if len(self.parent.friends_list) + self.parent.create_group_index > 5:
                    self.parent.create_group_index += 1
                    change = True
            else:
                if self.parent.create_group_index > 0:
                    self.parent.create_group_index -= 1
                    change = True
        except Exception as e:
            print("error in hadnling index")
        if change:
            self.parent.updated_chat()
        else:
            print("no change")

    def create_dm_pressed(self):
        self.Network.create_group(self.parent.selected_group_members)
        print("You a created new group")
        self.parent.is_create_group_pressed = False
        self.parent.selected_group_members.clear()
        self.parent.create_group_index = 0
        self.parent.updated_chat()

    def friend_checkbox_changed(self, state):
        checkbox = self.sender()
        friend_name = checkbox.friend_name
        wanted_len = self.parent.group_max_members - 1
        try:
            if state == 2 and len(self.parent.selected_group_members) < wanted_len:  # Checked state
                self.parent.selected_group_members.append(friend_name)
            else:
                if friend_name in self.parent.selected_group_members and state == 0:
                    self.parent.selected_group_members.remove(friend_name)
        except Exception as e:
            print(e)
        self.parent.updated_chat()

    def is_mouse_on_chats_list(self, mouse_pos):
        box_geometry = self.border_label.geometry()
        return box_geometry.contains(mouse_pos)

    def on_text_changed_in_contact_search(self):
        # This function will be called when the text inside QLineEdit changes
        try:
            if self.find_contact_text_entry.hasFocus():
                if len(self.find_contact_text_entry.text()) > 0:
                    self.parent.current_chat_box_search = True
                    self.parent.temp_search_list = self.return_search_list()
                    self.parent.updated_chat()
                else:
                    try:
                        self.parent.current_chat_box_search = False
                        self.parent.temp_search_list = []
                        self.parent.updated_chat()
                    except Exception as e:
                        print(e)
        except Exception as e:
            print(e)

    def return_search_list(self):
        # Get the filtered and sorted list of buttons
        try:
            filtered_buttons = filter_and_sort_chats(self.find_contact_text_entry.text(), self.parent.chats_list)
            # Remove all existing buttons from the layout
            # Create and add the updated buttons to the layout
            temp_list = []
            if not isinstance(filtered_buttons[0], str):
                for chat_name, button in filtered_buttons:
                    temp_list.append(chat_name)
                return temp_list
            else:
                for chat_name in filtered_buttons:
                    temp_list.append(chat_name)
                return temp_list
        except Exception as e:
            print(e)

    def drew_friends_buttons_on_screen_by_list(self, list):
        # Clear the existing buttons
        for _, button in self.chats_buttons_list:
            button.setParent(None)
            button.deleteLater()

        self.chats_buttons_list.clear()

        style_sheet = '''
            color: white;
            font-size: 15px;
            margin-bottom: 2px;
        '''
        self.friends_button_height = 50
        friend_starter_y = 170 + (self.parent.chat_box_chats_index * -50)
        self.parent.chat_box_index_y_start = friend_starter_y
        friend_x = 250
        for chat in list:
            try:
                button = self.create_friend_button(chat, self, style_sheet, (friend_x, friend_starter_y))
                self.chats_buttons_list.append((chat, button))
                friend_starter_y += self.friends_button_height
            except Exception as e:
                print(f"error in drew friends button {e}")
        self.raise_needed_elements()

    def raise_needed_elements(self):
        try:
            if self.parent.selected_chat != "":
                self.add_user_button.raise_()
                if self.current_group_id:
                    group_manager = self.parent.get_group_manager_by_group_id(self.current_group_id)
                    if group_manager == self.parent.username:
                        self.rename_group.raise_()
            self.border_label2.raise_()
            self.find_contact_text_entry.raise_()
            self.friends_button.raise_()
            self.chats_label.raise_()
            self.create_group_open.raise_()
            if self.parent.is_calling:
                self.ringing_to_label.raise_()
                self.calling_to_label.raise_()
                self.stop_calling_button.raise_()
            if self.parent.is_getting_called:
                self.pop_up_label.raise_()
                self.accept_button.raise_()
                self.reject_button.raise_()
                self.incoming_call_label.raise_()
                self.caller_label.raise_()
            if self.parent.is_in_a_call:
                self.mic_button.raise_()
                self.end_call_button.raise_()
                self.share_screen_button.raise_()
                self.deafen_button.raise_()
                self.share_camera_button.raise_()
                for profile_button in self.call_profiles_list:
                    profile_button.raise_()
            if self.current_group_id:
                if self.parent.is_call_dict_exist_by_group_id(self.current_group_id) and not self.parent.is_in_a_call:
                    self.join_call_button.raise_()
                    for profile_button in self.call_profiles_list:
                        profile_button.raise_()
        except Exception as e:
            print(f"error in raising elements {e}")

    def create_friend_button(self, label, parent, style_sheet, position):
        text, id = gets_group_attributes_from_format(label)
        if id:
            len_group = self.parent.get_number_of_members_by_group_id(id)
        button_text = text

        button = QPushButton(parent)
        button.setText(button_text)
        button.move(position[0], position[1])
        button.setFixedHeight(self.friends_button_height)
        button.clicked.connect(partial(self.on_friend_button_clicked, label))

        style = '''
            color: white;
            font-size: 10px;
            margin-bottom: 2px;
            background-color: rgba(0,0,0,0);
        '''

        if id:
            members_label = QLabel(f"{len_group} Members", self)
            members_label.setStyleSheet(style)
            memeber_x = position[0] + 35
            members_label.move(memeber_x, position[1] + 28)

        padding_top = "padding-top: -7px;" if label.startswith("(") else ""  # Adjust the padding value as needed

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.parent.background_color};
                border: 2px solid #2980b9;
                border-radius: 5px;
                padding: 8px 16px;
                padding-left: 35px;  /* Adjust the padding to move text to the right */
                {padding_top}
                color: white;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                text-align: left;
            }}

            QPushButton:hover {{
                background-color: #2980b9;
            }}

            QPushButton:pressed {{
                background-color: #202225;
                border-color: #72767d;
            }}
        """)

        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedWidth(350)
        button.raise_()
        if id:
            members_label.raise_()

        return button

    def raise_around_name_label(self):
        self.around_name.raise_()

    def is_valid_image(self, image_bytes):
        try:
            # Use Pillow to try opening the image from bytes
            image = Image.open(BytesIO(image_bytes))
            # If successful, it's a valid image
            return True
        except Exception as e:
            # If there is an exception, it's not a valid image
            print(f"Error: {e}")
            return False

    def open_file_dialog(self):
        if self.file_dialog.exec_():
            selected_files = self.file_dialog.selectedFiles()
            if selected_files:
                self.parent.image_file_name = selected_files[0].split("/")[-1]
                print(f"Selected file: {self.parent.image_file_name}")
                image_bytes = self.image_to_bytes(selected_files[0])

                if self.is_valid_image(image_bytes):
                    self.parent.image_to_send = image_bytes
                    print("image to send defined")
                    self.filename_label.setText(self.parent.image_file_name + " is loaded")
                    self.filename_label.show()
                    self.parent.updated_chat()
                    self.parent.activateWindow()
                else:
                    print("couldn't load image")
                # You can add additional processing here

    def open_image_file_dialog(self):
        self.open_file_dialog()

    def image_to_bytes(self, file_path):
        with open(file_path, "rb") as file:
            image_bytes = file.read()
            max_size_kb = 40
            max_size_bytes = max_size_kb * 1024  # Convert KB to bytes
            if len(image_bytes) > max_size_bytes:
                print("Image size exceeds 40 KB")
                self.image_too_big.show()
                self.parent.size_error_label = True
                return
            else:
                self.image_too_big.hide()
                self.parent.size_error_label = False
                return image_bytes

    def join_call(self):
        self.parent.is_joining_call = True
        self.parent.joining_to = self.parent.selected_chat
        self.Network.send_join_call_of_group_id(self.current_group_id)

    def end_current_call(self):
        self.parent.end_current_call()

    def mute_and_unmute(self):
        try:
            if self.parent.mute:
                media_content = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Discord_mute_sound_effect.mp3'))
                self.parent.play_sound(media_content)
                print("mic is not muted")
                self.parent.mute = False
                self.mic_button.setIcon(self.unmuted_mic_icon)
                self.Network.toggle_mute_for_myself()
            else:
                media_content = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Discord_mute_sound_effect.mp3'))
                self.parent.play_sound(media_content)
                print("mic is muted")
                self.parent.mute = True
                self.mic_button.setIcon(self.muted_mic_icon)
                self.Network.toggle_mute_for_myself()
        except Exception as e:
            print(e)

    def deafen_and_undeafen(self):
        if self.parent.deafen:
            media_content = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Discord_mute_sound_effect.mp3'))
            self.parent.play_sound(media_content)
            self.parent.deafen = False
            self.deafen_button.setIcon(self.not_deafened_icon)
            self.Network.toggle_deafen_for_myself()
        else:
            media_content = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Discord_mute_sound_effect.mp3'))
            self.parent.play_sound(media_content)
            self.parent.deafen = True
            self.deafen_button.setIcon(self.deafened_icon)
            self.Network.toggle_deafen_for_myself()

    def share_camera_and_unshare(self):
        try:
            if self.parent.is_camera_shared:
                self.parent.is_camera_shared = False
                self.share_camera_button.setIcon(self.share_camera_off_icon)
                self.Network.close_camera_stream()
                self.parent.update_share_camera_thread()
            else:
                if check_active_cameras():
                    self.parent.is_camera_shared = True
                    self.share_camera_button.setIcon(self.share_camera_on_icon)
                    self.Network.start_camera_stream()
                    self.parent.start_camera_data_thread()
                else:
                    print("tried share camera but no camera is connected")
        except Exception as e:
            print(f"error in sharing or closing share camera error is: {e}")

    def share_screen_and_unshare(self):
        try:
            if self.parent.is_screen_shared:
                self.parent.is_screen_shared = False
                self.share_screen_button.setIcon(self.share_screen_off_icon)
                self.Network.close_screen_stream()
                self.parent.update_share_screen_thread()
            else:
                self.parent.is_screen_shared = True
                self.share_screen_button.setIcon(self.share_screen_on_icon)
                self.parent.start_share_screen_send_thread()
                self.Network.start_screen_stream()
        except Exception as e:
            print(f"error in sharing or closing share screen error is: {e}")



    def accept_call(self):
        # Add your logic when the call is accepted
        self.Network.send_accept_call_with(self.parent.getting_called_by)

    def reject_call(self):
        # Add your logic when the call is rejected
        self.Network.send_reject_call_with(self.parent.getting_called_by)
        self.parent.stop_sound()
        self.parent.reset_call_var()

    def ringing_user(self, name):
        self.parent.is_calling = True
        self.parent.calling_to = name
        try:
            self.parent.updated_chat()
        except Exception as e:
            print(e)

    def call_user(self):
        try:
            if not self.parent.is_getting_called and not self.parent.is_calling and not self.parent.is_in_a_call:
                if self.parent.selected_chat.startswith("("):
                    print(f"Calling Group...{self.parent.selected_chat}")  # Replace this with your actual functionality
                else:
                    print(f"Calling User...{self.parent.selected_chat}")  # Replace this with your actual functionality
                media_content = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Phone_Internal_RingingCalling - Sound Effect.mp3'))
                self.parent.play_sound(media_content)
                self.Network.send_calling_user(self.parent.selected_chat)
                self.ringing_user(self.parent.selected_chat)
        except Exception as e:
            print(e)

    def on_friend_button_clicked(self, label):
        try:
            self.selected_chat_changed(label)
        except Exception as e:
            print(e)

    def Return_pos(self):
        return self.square_pos[0], self.square_pos[1]

    def custom_show(self):
        self.showMaximized()

    def showEvent(self, event):
        super().showEvent(event)

    def is_base64_encoded(self, s):
        try:
            # Attempt to decode the Base64 string
            decoded_bytes = base64.b64decode(s)
            return True
        except (binascii.Error, TypeError):
            # If decoding fails, it's not a valid Base64 string
            return False

    def load_image_from_bytes_to_label(self, image_bytes, label):
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)

        if pixmap.width() == 0 or pixmap.height() == 0:
            print("there is a error with image_bytes")
            return
        # Calculate the scaled size while maintaining the aspect ratio
        aspect_ratio = pixmap.width() / pixmap.height()
        target_width = self.image_width
        target_height = int(target_width / aspect_ratio)
        # Scale the image to the target size
        pixmap = pixmap.scaled(self.image_width, target_height, Qt.KeepAspectRatio)
        label.setGeometry(100, 100, self.image_width, target_height)  # Adjust size as needed
        label.setPixmap(pixmap)

    def load_image_from_bytes_to_button(self, image_bytes, button):
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)

        if pixmap.width() == 0 or pixmap.height() == 0:
            print("There is an error with image_bytes")
            return

        # Calculate the scaled size while maintaining the aspect ratio
        aspect_ratio = pixmap.width() / pixmap.height()
        target_width = self.image_width
        target_height = int(target_width / aspect_ratio)

        # Scale the image to the target size
        pixmap = pixmap.scaled(target_width, target_height, Qt.KeepAspectRatio)

        # Set the button's icon
        button.setIconSize(pixmap.size())
        button.setIcon(QIcon(pixmap))
        button.setGeometry(100, 100, self.image_width, target_height)  # Adjust size as needed


    def open_image_bytes(self, image_bytes):
        """Opens an image from bytes using the default image viewer application.

        Args:
            image_bytes (bytes): The image data as bytes.

        Returns:
            bool: True if the image was opened successfully, False otherwise.
        """
        try:
            # Create a temporary file to save the image bytes
            with open("temp_image.png", "wb") as f:
                f.write(image_bytes)

            # Open the temporary file using the default image viewer application
            webbrowser.open("temp_image.png")

            return True

        except Exception as e:
            print(f"Error opening image: {e}")
            return False

    def show_messages_on_screen(self, list_messages):
        # can show up to 33 message in the chat
        # Delete existing message labels
        self.delete_message_labels()
        x_pos = 620
        starter = 850
        if self.filename_label.text() != "":
            starter_y_pos = starter
        else:
            starter_y_pos = starter + 50
        end_y_pos = 50
        y = starter_y_pos
        index = 0
        for i in list_messages:
            if self.parent.chat_start_index <= index:
                if index == len(self.parent.list_messages) - 1:
                    self.parent.is_last_message_on_screen = True
                if not self.is_base64_encoded(i[0]) or len(str(i[0])) < 200:

                    # first parts = content
                    message = i[0]
                    label = self.create_temp_message_label(message)
                    label.move(x_pos, y)
                    self.message_labels.append(label)
                    y -= 20

                    # second part = Name + timestamp
                    label2 = QLabel()
                    label2 = self.create_temp_message_label("")
                    label2.setText(f'<span style="font-size: 14px; color: white; font-weight: bold;">{i[1]}</span>'
                                   f'<span style="font-size: 9px; color: gray;"> {i[2]}</span>')
                    self.message_labels.append(label2)
                    label2.move(x_pos, y)
                    y -= 20
                    if index != len(self.parent.list_messages) - 1:
                        self.parent.is_last_message_on_screen = False
                else:
                    try:
                        compressed_image_bytes = base64.b64decode(i[0])
                        image_bytes = zlib.decompress(compressed_image_bytes)
                        #label1 = QLabel(self)

                        image_label = QPushButton(self)
                        image_label.setStyleSheet("background-color: transparent; border: none;")
                        #self.load_image_from_bytes_to_label(image_bytes, label1)

                        self.load_image_from_bytes_to_button(image_bytes, image_label)
                        image_label.clicked.connect(lambda _, image_bytes=image_bytes: open_image_bytes(image_bytes))
                        if y - image_label.height() - 10 < end_y_pos:
                            self.parent.is_chat_box_full = True
                            if index != len(self.parent.list_messages) - 1:
                                self.parent.is_last_message_on_screen = False

                        self.message_labels.append(image_label)
                        y -= image_label.height()
                        image_label.move(x_pos, y)
                        image_label.raise_()
                        y -= 20
                        message = ""
                        label = self.create_temp_message_label(message)
                        label.setText(f'<span style="font-size: 14px; color: white; font-weight: bold;">{i[1]}</span>'
                                      f'<span style="font-size: 9px; color: gray;"> {i[2]}</span>')
                        label.move(x_pos, y)
                        self.message_labels.append(label)
                        y -= 20
                    except Exception as e:
                        print(f"error here is:{e}")
                    if y < end_y_pos:
                        self.parent.is_chat_box_full = True
                        if index != self.parent.list_messages:
                            self.parent.is_last_message_on_screen = False
                if y - 15 < end_y_pos:
                    self.parent.is_chat_box_full = True
                    break

            index += 1
        try:
            self.around_name.raise_()
            if self.parent.selected_chat != "":
                self.call_button.raise_()
            self.chat_name_label.raise_()
        except Exception as e:
            print(f"error in showing messages on screen: {e}")

    def on_button_clicked(self, label):
        self.button_clicked_signal.emit(label)

    def create_temp_button(self, button_label):

        x_pos = 470
        button = QPushButton(button_label, self)
        button.setStyleSheet("color: white;")
        font = button.font()
        font.setPointSize(12)
        button.setFont(font)
        button.clicked.connect(lambda checked, label=button_label: self.on_button_clicked(label))

        return button

    def create_temp_message_label(self, message):
        x_pos = 620
        label = QLabel(message, self)
        label.setStyleSheet("color: white;")
        font = label.font()
        font.setPointSize(12)
        label.setFont(font)

        return label

    def delete_message_labels(self):
        for label in self.message_labels:
            label.deleteLater()
        self.message_labels = []

    def check_editing_status(self):
        return self.text_entry.hasFocus()

    def updated_chatbox(self, updated_list):
        self.messages_list = updated_list

    def selected_chat_changed(self, name):
        if name != self.parent.selected_chat:
            if name.startswith("("):
                self.parent.is_current_chat_a_group = True
                text, _ = gets_group_attributes_from_format(name)
                print("chat is group")
            else:
                text = name
                self.parent.is_current_chat_a_group = False
                print("chat is a private chat")
            print(f"chat changed to {name}")
            self.chat_name_label.setText(text)
            place_holder_text = "Message" + " " + text
            try:
                if self.text_entry:
                    self.text_entry.setPlaceholderText(place_holder_text)
            except Exception as e:
                print(e)
            self.parent.selected_chat = name
            self.parent.chat_start_index = 0
            self.Network.updated_current_chat(name)
            self.image_too_big.hide()
            self.parent.size_error_label = False
            self.parent.image_to_send = None
            self.parent.image_file_name = ""
            self.parent.updated_chat()

    def is_mouse_on_chat_box(self, mouse_pos):
        box_geometry = self.square_label.geometry()
        return box_geometry.contains(mouse_pos)


class FriendsBox(QWidget):
    def __init__(self, friends_list, requests_list, Network, username, parent=None):
        super().__init__()
        self.font_size = 60
        # Styling
        self.raised_elements = []

        self.parent = parent
        self.Network = Network
        self.username = username
        self.requests_list = requests_list
        style_sheet = '''
            color: white;
            font-size: 40px;
            margin-bottom: 10px;
        '''

        main_style_sheet = '''
            color: white;
            font-size: 40px;
            padding: 10px;
            border: 2px solid #3498db; /* Blueish border color */
            border-radius: 10px;
            margin-bottom: 10px;
        '''
        self.friends_label = QPushButton("  Social", self)
        self.friends_label.setStyleSheet('''
            color: white;
            font-size: 15px;
            border: none;  /* Remove the border */
            border-radius: 5px;
            padding: 5px;
            margin-bottom: 2px;
            text-align: left;  /* Align the text to the left */
            alignment: left;   /* Align the icon and text to the left */
            padding-left: 10px;   /* Adjust the starting position to the right */
            hover {
                background-color: transparent;  /* Remove hover effect */
            }

        ''')

        icon = QIcon("discord_app_assets/friends_icon.png")  # Replace with the path to your icon image
        self.friends_label.setIcon(icon)
        button_y = 10
        # Set the position and size of the button
        friend_x = 600
        friends_label_y = 0
        self.friends_label.move(friend_x - 30, button_y)
        # Set the text alignment to show both the icon and text

        # Optional: Adjust the spacing between the icon and text
        self.friends_label.setIconSize(QSize(50, 50))  # Adjust size as needed

        selecting_buttons_stylesheet = (f"""
            QPushButton {{
                background-color: {self.parent.background_color};  /* Use your desired blue color */
                border: 2px solid #2980b9;  /* Use a slightly darker shade for the border */
                border-radius: 5px;
                padding: 8px 16px;
                color: #b9c0c7;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }}

            QPushButton:hover {{
                background-color: #2980b9;
            }}

            QPushButton:pressed {{
                background-color: #202225;
                border-color: #72767d;
            }}
        """)

        selecting_button_pressed_stylesheet = ("""
            QPushButton {
                background-color: #3498db;  /* Use your desired color for pressed state */
                border: 2px solid #2980b9;  /* Use a slightly darker shade for the border */
                border-radius: 5px;
                padding: 8px 16px;
                color: #b9c0c7;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2c3e50;  /* Use your desired color for pressed state */
                border-color: #34495e;  /* Use a slightly darker shade for the border in pressed state */
            }
        """)

        border1_width = 725
        border1_height = self.friends_label.height() + 48
        self.border1_label = QLabel(self)
        self.border1_label.setStyleSheet('''
                        border: 2px solid #2980b9;
                        border-radius: 5px;
                        padding: 5px;
                        margin-bottom: 2px;
                    ''')
        self.border1_label.setGeometry(friend_x - 40, 0, border1_width, border1_height)
        self.border1_label.lower()

        border2_width = border1_width
        border3_height = self.friends_label.height() + 900
        self.border2_label = QLabel(self)
        self.border2_label.setStyleSheet('''
                        border: 2px solid #2980b9;
                        border-radius: 5px;
                        padding: 5px;
                        margin-bottom: 2px;
                    ''')
        if self.parent.friends_box_page == "add friend":
            border2_height = 195 - border1_height + 85
        else:
            border2_height = 195 - border1_height + 10
        self.border2_label.setGeometry(friend_x - 40, border1_height - 3, border2_width, border2_height)
        self.border2_label.lower()

        self.border3_label = QLabel(self)
        self.border3_label.setStyleSheet('''
                        border: 2px solid #2980b9;
                        border-radius: 5px;
                        padding: 5px;
                        margin-bottom: 2px;
                    ''')
        self.border3_label.setGeometry(friend_x - 40, 195, border2_width, border3_height)
        self.border3_label.lower()

        buttons_y = button_y + 10

        online_button_x = friend_x + 150
        self.online_button = QPushButton("Online", self)
        self.online_button.move(online_button_x, buttons_y)
        self.online_button_height = 37
        self.online_button.setFixedHeight(self.online_button_height)
        self.online_button.clicked.connect(self.online_button_pressed)  # Connect the button to the function
        self.online_button.setStyleSheet(selecting_buttons_stylesheet)

        all_button_x = online_button_x + self.online_button.width() + 10
        self.all_button = QPushButton("All", self)
        self.all_button.move(all_button_x, buttons_y)
        self.all_button_height = 37
        self.all_button.setFixedHeight(self.all_button_height)
        self.all_button.clicked.connect(self.all_button_pressed)  # Connect the button to the function
        self.all_button.setStyleSheet(selecting_buttons_stylesheet)

        pending_button_x = all_button_x + self.all_button.width() - 15
        self.Pending_button = QPushButton("Pending", self)
        self.Pending_button.move(pending_button_x, buttons_y)
        self.Pending_button_height = 37
        self.Pending_button.setFixedHeight(self.Pending_button_height)
        self.Pending_button.clicked.connect(self.pending_button_pressed)  # Connect the button to the function
        self.Pending_button.setStyleSheet(selecting_buttons_stylesheet)

        blocked_button_x = pending_button_x + self.Pending_button.width() + 15
        self.blocked_button = QPushButton("Blocked", self)
        self.blocked_button.move(blocked_button_x, buttons_y)
        self.blocked_button_height = 37
        self.blocked_button.setFixedHeight(self.blocked_button_height)
        self.blocked_button.clicked.connect(self.blocked_button_pressed)  # Connect the button to the function
        self.blocked_button.setStyleSheet(selecting_buttons_stylesheet)

        add_friend_button_x = blocked_button_x + self.blocked_button.width() + 10
        self.add_friend = QPushButton("Add Friend", self)
        self.add_friend.move(add_friend_button_x, buttons_y)
        self.add_friend_height = 37
        self.add_friend.setFixedHeight(self.add_friend_height)
        self.add_friend.clicked.connect(self.add_friend_button_pressed)  # Connect the button to the function
        self.add_friend.setStyleSheet(selecting_buttons_stylesheet)

        search_x = friend_x - 10
        search_y = border1_height + 20
        search_height = 45
        search_width = border2_width - 65
        self.friends_list = friends_list

        self.search = QLineEdit(self)
        self.search.hide()

        self.social_label = QLabel("", self)
        self.social_label.hide()

        if self.parent.friends_box_page == "online":

            friends_box_list = []
            try:
                if self.parent.current_friends_box_search:
                    friends_box_list = self.parent.temp_search_list
                else:
                    friends_box_list = self.parent.online_users_list
            except Exception as e:
                print(f"error in friends_box{e}")

            self.social_label = QLabel(f"ONLINE — {len(friends_box_list)}", self)
            self.social_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")

            # Adjust the position and size of the label as needed
            self.social_label.move(search_x, search_y + 60)
            self.social_label.adjustSize()  # Adjust the size to fit the content

            self.online_button.setStyleSheet(selecting_button_pressed_stylesheet)

            self.search = QLineEdit(self)
            self.search.setPlaceholderText("Search")
            self.search.setStyleSheet(
                "background-color: #2980b9; color: white; padding: 10px; border: 1px solid #2980b9; border-radius: 5px; font-size: 14px;")
            self.search.setGeometry(search_x, search_y, search_width, search_height)
            self.search.textChanged.connect(self.on_text_changed_in_contact_search)

            self.default_starting_y = 200
            self.friend_labels = []
            friend_starter_y = 200 + (self.parent.friends_box_index * -50)
            self.parent.friends_box_index_y_start = friend_starter_y

            friends_label_x = search_x
            for friend in friends_box_list:
                friend_label = QLabel(friend, self)
                friend_label.setStyleSheet(style_sheet)
                friend_label.move(friends_label_x + 25, friend_starter_y)
                friend_label.setFixedHeight(self.font_size)  # Increase height
                friend_label.adjustSize()  # Ensure the label size is adjusted to its content

                line = QFrame(self)
                line.setGeometry(friend_x - 40, friend_starter_y + self.font_size + 5, border2_width, 2)
                line.setStyleSheet("background-color: #2980b9;")  # Set line color

                chat_button = QPushButton(self)
                chat_button_x = 1235
                self.chat_label = QLabel("Message", self)
                self.raised_elements.append(self.chat_label)
                self.connect_button_label_pair(
                    chat_button,
                    self.chat_label,
                    "Message",
                    "discord_app_assets/press_chat_icon.png",
                    self.chat_label,
                    chat_button_x,
                    friend_starter_y + 10,
                    friend  # Pass the friend parameter here
                )

                remove_friend_button = QPushButton(self)
                remove_friend_button_x = chat_button_x - 60
                self.remove_friend_label = QLabel("Remove", self)
                self.raised_elements.append(self.remove_friend_label)
                self.connect_button_label_pair(
                    remove_friend_button,
                    self.remove_friend_label,
                    "Remove",
                    "discord_app_assets/remove_friend_icon.png",
                    self.remove_friend_label,
                    remove_friend_button_x,
                    friend_starter_y + 10,
                    friend  # Pass the friend parameter here
                )

                block_friend_button = QPushButton(self)
                self.block_friend_label = QLabel("Block", self)
                self.raised_elements.append(self.block_friend_label)
                self.connect_button_label_pair(
                    block_friend_button,
                    self.block_friend_label,
                    "Block",
                    "discord_app_assets/block_icon.png",
                    self.block_friend,
                    remove_friend_button_x - 60,
                    friend_starter_y + 10,
                    friend  # Pass the friend parameter here
                )

                circle_label = QLabel(self)
                circle_label.setGeometry(friends_label_x, friend_starter_y + 20, 20, 20)
                if friend in self.parent.online_users_list:
                    self.draw_circle(circle_label, "green")
                else:
                    self.draw_circle(circle_label, "gray")
                if friend_starter_y > self.parent.height():
                    self.parent.is_friends_box_full = True
                    print("smaller then 0")
                    break

                friend_starter_y += 70
                self.friend_labels.append(friend_label)
                self.raise_all_element()
            if friend_starter_y < self.parent.height():
                self.parent.is_friends_box_full = False

        if self.parent.friends_box_page == "all":
            friends_box_list = []
            try:
                if self.parent.current_friends_box_search:
                    friends_box_list = self.parent.temp_search_list
                else:
                    friends_box_list = self.parent.friends_list
            except Exception as e:
                print(f"error in friends_box{e}")
            # Friends Label
            self.all_button.setStyleSheet(selecting_button_pressed_stylesheet)

            self.social_label = QLabel(f"ALL FRIENDS — {len(friends_box_list)}", self)
            self.social_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")

            # Adjust the position and size of the label as needed
            self.social_label.move(search_x, search_y + 60)
            self.social_label.adjustSize()  # Adjust the size to fit the content

            self.search = QLineEdit(self)
            self.search.setPlaceholderText("Search")
            self.search.setStyleSheet(
                "background-color: #2980b9; color: white; padding: 10px; border: 1px solid #2980b9; border-radius: 5px; font-size: 14px;")
            self.search.setGeometry(search_x, search_y, search_width, search_height)
            self.search.textChanged.connect(self.on_text_changed_in_contact_search)

            self.default_starting_y = 200
            self.friend_labels = []
            friend_starter_y = 200 + (self.parent.friends_box_index * -50)
            self.parent.friends_box_index_y_start = friend_starter_y

            friends_label_x = search_x
            for friend in friends_box_list:
                friend_label = QLabel(friend, self)
                friend_label.setStyleSheet(style_sheet)
                friend_label.move(friends_label_x + 25, friend_starter_y)
                friend_label.setFixedHeight(self.font_size)  # Increase height
                friend_label.adjustSize()  # Ensure the label size is adjusted to its content

                line = QFrame(self)
                line.setGeometry(friend_x - 40, friend_starter_y + self.font_size + 5, border2_width, 2)
                line.setStyleSheet("background-color: #2980b9;")  # Set line color

                chat_button = QPushButton(self)
                chat_button_x = 1235
                self.chat_label = QLabel("Message", self)
                self.raised_elements.append(self.chat_label)
                self.connect_button_label_pair(
                    chat_button,
                    self.chat_label,
                    "Message",
                    "discord_app_assets/press_chat_icon.png",
                    self.open_chat,
                    chat_button_x,
                    friend_starter_y + 10,
                    friend  # Pass the friend parameter here
                )

                remove_friend_button = QPushButton(self)
                remove_friend_button_x = chat_button_x - 60
                self.remove_friend_label = QLabel("Remove", self)
                self.raised_elements.append(self.remove_friend_label)
                self.connect_button_label_pair(
                    remove_friend_button,
                    self.remove_friend_label,
                    "Remove",
                    "discord_app_assets/remove_friend_icon.png",
                    self.remove_friend,
                    remove_friend_button_x,
                    friend_starter_y + 10,
                    friend  # Pass the friend parameter here
                )

                block_friend_button = QPushButton(self)

                self.block_friend_label = QLabel("Block", self)
                self.raised_elements.append(self.block_friend_label)
                self.connect_button_label_pair(
                    block_friend_button,
                    self.block_friend_label,
                    "Block",
                    "discord_app_assets/block_icon.png",
                    self.block_friend,
                    remove_friend_button_x - 60,
                    friend_starter_y + 10,
                    friend  # Pass the friend parameter here
                )

                circle_label = QLabel(self)
                circle_label.setGeometry(friends_label_x, friend_starter_y + 20, 20, 20)
                if friend in self.parent.online_users_list:
                    self.draw_circle(circle_label, "green")
                else:
                    self.draw_circle(circle_label, "gray")
                if friend_starter_y > self.parent.height():
                    self.parent.is_friends_box_full = True
                    print("smaller then 0")
                    break

                friend_starter_y += 70
                self.friend_labels.append(friend_label)
                self.raise_all_element()
            if friend_starter_y < self.parent.height():
                self.parent.is_friends_box_full = False

        if self.parent.friends_box_page == "pending":
            try:
                friends_box_list = []
                try:
                    if self.parent.current_friends_box_search:
                        friends_box_list = self.parent.temp_search_list
                    else:
                        friends_box_list = self.parent.request_list
                except Exception as e:
                    print(f"error in friends_box{e}")
                # Friends Label
                self.Pending_button.setStyleSheet(selecting_button_pressed_stylesheet)

                self.social_label = QLabel(f"Pending — {len(friends_box_list)}", self)
                self.social_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")

                # Adjust the position and size of the label as needed
                self.social_label.move(search_x, search_y + 60)
                self.social_label.adjustSize()  # Adjust the size to fit the content
                self.requests_items = []

                self.default_starting_y = 200
                self.friend_labels = []
                request_starter_y = 200 + (self.parent.friends_box_index * -50)
                self.parent.friends_box_index_y_start = request_starter_y

                request_x = search_x

                self.search = QLineEdit(self)
                self.search.setPlaceholderText("Search")
                self.search.setStyleSheet(
                    "background-color: #2980b9; color: white; padding: 10px; border: 1px solid #2980b9; border-radius: 5px; font-size: 14px;")
                self.search.setGeometry(search_x, search_y, search_width, search_height)
                self.search.textChanged.connect(self.on_text_changed_in_contact_search)

                for request in requests_list:
                    request_label = QLabel(request, self)
                    request_label.setStyleSheet(style_sheet)
                    request_label.move(request_x, request_starter_y)
                    request_label.setFixedHeight(70)  # Increase height

                    # "V" (Green) Button
                    accept_button = QPushButton("✔", self)
                    accept_button.setStyleSheet('''
                                background-color: #2ecc71;  /* Green color */
                                color: white;
                                padding: 10px;
                                border: 2px solid #2ecc71;
                                border-radius: 10px;
                                font-size: 24px;
                            ''')
                    accept_button.move(request_x + 200, request_starter_y)
                    accept_button.setFixedHeight(50)  # Increase height
                    accept_button.setFixedWidth(50)  # Fixed width

                    # "X" (Red) Button
                    reject_button = QPushButton("✘", self)
                    reject_button.setStyleSheet('''
                                background-color: #e74c3c;  /* Red color */
                                color: white;
                                padding: 10px;
                                border: 2px solid #e74c3c;
                                border-radius: 10px;
                                font-size: 24px;
                            ''')
                    reject_button.move(request_x + 260, request_starter_y)
                    reject_button.setFixedHeight(50)  # Increase height
                    reject_button.setFixedWidth(50)  # Fixed width

                    request_starter_y += 70
                    self.requests_items.append(request_label)
                    self.requests_items.append(accept_button)
                    self.requests_items.append(reject_button)
                    if request_starter_y > self.parent.height():
                        self.parent.is_friends_box_full = True
                        print("smaller then 0")
                        break
                if request_starter_y < self.parent.height():
                    self.parent.is_friends_box_full = False

                for i in range(0, len(self.requests_items), 3):
                    accept_button = self.requests_items[i + 1]
                    reject_button = self.requests_items[i + 2]

                    accept_button.clicked.connect(
                        lambda checked, index=i: self.handle_friend_request(index, accept=True))
                    reject_button.clicked.connect(
                        lambda checked, index=i: self.handle_friend_request(index, accept=False))
                self.raise_all_element()
            except Exception as e:
                print(e)

        if self.parent.friends_box_page == "add friend":
            self.add_friend.setStyleSheet(selecting_button_pressed_stylesheet)
            self.social_label = QLabel(f"ADD FRIEND", self)
            self.social_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")

            # Adjust the position and size of the label as needed
            self.social_label.move(search_x, search_y + 5)
            self.social_label.adjustSize()  # Adjust the size to fit the content

            self.add_friend_label = QLabel(f"You can add friends with their Connectify username.", self)
            self.add_friend_label.setStyleSheet("color: white; font-size: 12px;")

            # Adjust the position and size of the label as needed
            self.add_friend_label.move(search_x, search_y + 55)
            self.add_friend_label.adjustSize()  # Adjust the size to fit the content

            self.add_friend_entry = QLineEdit(self)
            self.add_friend_entry.setPlaceholderText("Add Friend")
            self.add_friend_entry.setGeometry(search_x, search_y + 100, search_width - 10, search_height + 50)
            self.add_friend_entry.setStyleSheet(
                "background-color: #2980b9; color: white; padding: 10px; border: 1px solid #2980b9; border-radius: 5px; font-size: 14px;")
            self.add_friend_entry.setFixedHeight(40)  # Increase height

        if self.parent.friends_box_page == "blocked":
            friends_box_list = []
            try:
                if self.parent.current_friends_box_search:
                    friends_box_list = self.parent.temp_search_list
                else:
                    friends_box_list = self.parent.blocked_list
            except Exception as e:
                print(f"error in friends_box{e}")
            # Friends Label
            self.blocked_button.setStyleSheet(selecting_button_pressed_stylesheet)

            self.social_label = QLabel(f"BLOCKED — {len(friends_box_list)}", self)
            self.social_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")

            # Adjust the position and size of the label as needed
            self.social_label.move(search_x, search_y + 60)
            self.social_label.adjustSize()  # Adjust the size to fit the content

            self.search = QLineEdit(self)
            self.search.setPlaceholderText("Search")
            self.search.setStyleSheet(
                "background-color: #2980b9; color: white; padding: 10px; border: 1px solid #2980b9; border-radius: 5px; font-size: 14px;")
            self.search.setGeometry(search_x, search_y, search_width, search_height)
            self.search.textChanged.connect(self.on_text_changed_in_contact_search)

        self.error_friend = QLabel("couldn't find user", self)
        self.error_friend.move(search_x, search_y + 100 + search_height)
        self.error_friend.hide()
        self.error_friend.setStyleSheet('''color: red;''')

        self.request_sent = QLabel("Request sent", self)
        self.request_sent.move(search_x, search_y + 100 + search_height)
        self.request_sent.hide()
        self.request_sent.setStyleSheet('''color: green;''')

        self.already_friends = QLabel("Already friends", self)
        self.already_friends.move(search_x, search_y + 100 + search_height)
        self.already_friends.hide()
        self.already_friends.setStyleSheet('''color: red;''')

        self.already_sent_request = QLabel("Request is pending", self)
        self.already_sent_request.move(search_x, search_y + 100 + search_height)
        self.already_sent_request.hide()
        self.already_sent_request.setStyleSheet('''color: gray;''')

    def connect_button_label_pair(self, button, label, label_text, icon_path, click_callback, x, y, friend):
        button.setFixedSize(40, 40)
        button_icon = QIcon(QPixmap(icon_path))
        button.setIcon(button_icon)
        if label_text != "Message":
            button.setIconSize(button_icon.actualSize(QSize(26, 26)))
        else:
            button.setIconSize(button_icon.actualSize(QSize(41, 41)))
        button.setStyleSheet("""           
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton {
                background-color: transparent;
            }
            QPushButton:pressed {
                background-color: #202225;
                border-color: #72767d;
            }""")

        button.clicked.connect(lambda checked: click_callback(friend))
        button.move(x, y)

        label.setText(label_text)
        label.hide()
        label.setStyleSheet("color: white; font-size: 12px;")
        label.move(x, y - 20)

        # Connect the label to show on hover
        button.enterEvent = lambda event: label.show()
        button.leaveEvent = lambda event: label.hide()

    def on_text_changed_in_contact_search(self):
        # This function will be called when the text inside QLineEdit changes
        default_list = []
        if self.parent.friends_box_page == "online":
            default_list = self.parent.online_users_list
        elif self.parent.friends_box_page == "all":
            default_list = self.parent.friends_list
        elif self.parent.friends_box_page == "pending":
            default_list = self.parent.friends_list
        try:
            if self.search.hasFocus():
                if len(self.search.text()) > 0:
                    self.parent.current_friends_box_search = True
                    self.parent.temp_search_list = filter_and_sort_chats(self.search.text(), default_list)
                    self.parent.updated_requests()
                else:
                    try:
                        self.parent.current_friends_box_search = False
                        self.parent.temp_search_list = []
                        self.parent.updated_requests()
                    except Exception as e:
                        print(f"problem with updating screen:{e}")
        except Exception as e:
            print(f"problem with updating screen:{e}")

    def raise_all_element(self):
        self.border1_label.raise_()
        self.border2_label.raise_()
        self.add_friend.raise_()
        self.all_button.raise_()
        self.Pending_button.raise_()
        self.online_button.raise_()
        self.friends_label.raise_()
        self.blocked_button.raise_()
        self.search.raise_()
        self.social_label.raise_()
        self.block_friend_label.raise_()
        self.remove_friend_label.raise_()
        self.chat_label.raise_()
        for element in self.raised_elements:
            element.raise_()

    def is_mouse_on_friends_box(self, mouse_pos):
        box_geometry = self.border3_label.geometry()
        return box_geometry.contains(mouse_pos)

    def online_button_pressed(self):
        if self.parent.friends_box_page != "online":
            if self.parent.friends_box_page != "add friend":
                self.search.clear()
            self.parent.current_friends_box_search = False
            self.parent.temp_search_list = []
            self.parent.friends_box_index = 0
            self.parent.friends_box_page = "online"
            self.parent.updated_requests()

    def all_button_pressed(self):
        if self.parent.friends_box_page != "all":
            if self.parent.friends_box_page != "add friend":
                self.search.clear()
            self.parent.current_friends_box_search = False
            self.parent.temp_search_list = []
            self.parent.friends_box_index = 0
            self.parent.friends_box_page = "all"
            self.parent.updated_requests()

    def pending_button_pressed(self):
        try:
            if self.parent.friends_box_page != "pending":
                if self.parent.friends_box_page != "add friend":
                    self.search.clear()
                self.parent.current_friends_box_search = False
                self.parent.temp_search_list = []
                self.parent.friends_box_index = 0
                self.parent.friends_box_page = "pending"
                self.parent.updated_requests()
        except Exception as e:
            print(e)

    def blocked_button_pressed(self):
        if self.parent.friends_box_page != "blocked":
            if self.parent.friends_box_page != "add friend":
                self.search.clear()
            self.parent.current_friends_box_search = False
            self.parent.temp_search_list = []
            self.parent.friends_box_index = 0
            self.parent.friends_box_page = "blocked"
            self.parent.updated_requests()

    def add_friend_button_pressed(self):
        try:
            if self.parent.friends_box_page != "add friend":
                if self.parent.friends_box_page != "add friend":
                    self.search.clear()
                self.parent.current_friends_box_search = False
                self.parent.temp_search_list = []
                self.parent.friends_box_index = 0
                self.parent.friends_box_page = "add friend"
                self.parent.updated_requests()
        except Exception as e:
            print(e)

    def show_online_list(self):
        print("online list")

    def open_chat(self, friend):
        # Implement the logic to start a chat with the selected friend
        print(f"Starting chat with {friend}")
        self.parent.chat_box.selected_chat_changed(friend)
        self.parent.Chat_clicked()

    def remove_friend(self, friend):
        # Implement the logic to start a chat with the selected friend
        print(f"Removing {friend} as friend")
        self.Network.send_remove_friend(friend)
        self.parent.friends_list.remove(friend)
        self.parent.updated_requests()

    def block_friend(self, friend):
        # Implement the logic to start a chat with the selected friend
        print(f"blocking {friend}")

    def draw_circle(self, widget, color_of_circle):
        pixmap = QPixmap(20, 20)
        pixmap.fill(QColor(color_of_circle))

        widget.setPixmap(pixmap)

    def send_friend_request(self):
        # Implement the logic to send friend requests here
        self.error_friend.hide()
        self.request_sent.hide()
        self.already_friends.hide()
        self.already_sent_request.hide()
        if self.add_friend_entry.hasFocus() and len(self.add_friend_entry.text()) > 0:
            username = self.username
            friend_username = self.add_friend_entry.text()
            self.Network.send_friend_request(username, friend_username)
            self.add_friend_entry.setText("")

    def friend_not_found(self):
        self.error_friend.show()

    def request_was_sent(self):
        self.request_sent.show()

    def request_was_friend(self):
        self.already_friends.show()

    def request_is_pending(self):
        self.already_sent_request.show()

    def handle_friend_request(self, index, accept=True):
        # Handle friend requests (accept or reject) here
        friend_index = index // 3
        friend_label = self.requests_items[index]
        friend_username = friend_label.text()

        if accept:
            self.Network.send_friends_request_acception(friend_username)
            self.parent.request_list.remove(friend_username)
        else:
            self.parent.request_list.remove(friend_username)
            self.Network.send_friends_request_rejection(friend_username)

        for i in range(index, index + 3):
            item = self.requests_items[i]
            item.setParent(None)
            item.deleteLater()

        # Remove the friend from the requests list
        del self.requests_items[index:index + 3]
        self.parent.updated_requests()

import pyaudio
import cv2


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


import concurrent.futures
import warnings

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


class SettingsBox(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.font_size = 60
        self.parent = parent
        self.Network = self.parent.Network
        self.settings_button_height = 50
        self.file_dialog = QFileDialog(self)
        self.file_dialog.setFileMode(QFileDialog.ExistingFile)
        self.file_dialog.setNameFilter("Image files (*.png)")

        delta_of_main_buttons = 50

        starter_x_of_main_buttons = 350
        starter_y_of_main_buttons = 100

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

        background_color = self.parent.background_color
        hover_color = self.parent.standard_hover_color

        self.label = QLabel(self)
        self.label.setStyleSheet("border-right: 3px solid #2980b9; padding-left: 10px;")
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

        self.volume_slider_style_sheet = """
                       QSlider::groove:horizontal {
                           border: 1px solid #bbb;
                           background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ddd, stop:1 #eee);
                           height: 10px;
                           margin: 0px;
                       }

                       QSlider::handle:horizontal {
                           background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc);
                           border: 1px solid #777;
                           width: 20px;
                           margin: -2px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */
                           border-radius: 5px;
                       }

                       QSlider::add-page:horizontal {
                           background: #fff;
                       }

                       QSlider::sub-page:horizontal {
                           background: #3498db; /* Change this color to the desired color for the left side */
                       }
                               """

        label_page = self.create_white_label(800, 70, 20, None, None, self.parent.selected_settings)
        try:
            dark_green = "#1e9644"
            other_green = "#044f1c"
            if self.parent.selected_settings == "My Account":
                start_y = 100
                start_x = 500
                dark_green = "#1e9644"
                other_green = "#044f1c"
                width, height = (120, 120)
                self.profile_image_label = create_custom_circular_label(width, height, self)
                profile_image_x, profile_image_y = (800, 200)
                if self.parent.profile_pic is None:
                    icon_path = "discord_app_assets/regular_profile.png"
                    set_icon_to_label(self.profile_image_label, icon_path, width, height)
                else:
                    circular_pic_bytes = make_circular_image(self.parent.profile_pic)
                    set_icon_from_bytes_to_label(self.profile_image_label, circular_pic_bytes)
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
                red_hex = "#9e0817"
                dark_red_hex = "#690d16"
                delete_account_button_x, delete_account_button_y = change_password_button_x, change_password_button_y+100
                delete_account_button = self.create_colored_button(red_hex, dark_red_hex, None,
                                                                      delete_account_button_x,
                                                                      delete_account_button_y, button_width,
                                                                      button_height, "Delete Account")


            elif self.parent.selected_settings == "Voice & Video":

                p = pyaudio.PyAudio()

                # Check if the device has input capability
                input_devices = []
                output_devices = []

                for i in range(p.get_device_count()):
                    device_info = p.get_device_info_by_index(i)
                    device_name = device_info["name"].lower()

                    # Check if the device has output capability and is a headset or speaker
                    if device_info["maxOutputChannels"] > 0 and ("headset" in device_name or "speaker" in device_name or "headphones" in device_name):
                        if device_info["name"] not in input_devices:
                            input_devices.append(device_info["name"])

                    # Check if the device has input capability and is a microphone
                    if device_info["maxInputChannels"] > 0 and ("microphone" in device_name):
                        if device_info["name"] not in output_devices:
                            output_devices.append(device_info["name"])
                camera_names_list = get_camera_names()

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

                volume_slider_label = self.create_white_label(volume_slider_label_x, volume_slider_label_y, self.default_labels_font_size, None, None, "INPUT VOLUME")
                self.volume_label = self.create_white_label(volume_slider_label_x + width + 10, volume_slider_y+7, self.default_labels_font_size, 100, 30, str(self.parent.volume))

                space_between_option_box_and_label = 30
                output_x, output_y = (800, starter_y)
                self.output_combobox = self.create_option_box(width, height, output_x, output_y, output_devices)
                output_label = self.create_white_label(output_x, output_y-space_between_option_box_and_label, self.default_labels_font_size, None, None, "OUTPUT DEVICES")

                input_x, input_y = (1150, starter_y)
                self.input_combobox = self.create_option_box(width, height, input_x, input_y, input_devices)
                input_label = self.create_white_label(input_x, input_y - space_between_option_box_and_label, self.default_labels_font_size, None,
                                                       None, "INPUT DEVICES")
                camera_x, camera_y = (800, 670)
                self.camara_devices_combobox = self.create_option_box(width, height, camera_x, camera_y, camera_names_list)
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
                font_size_label = self.create_white_label(font_size_slider_x + font_size_slider_width + 10, font_size_slider_y + 7,
                                                            self.default_labels_font_size, 100, 30,
                                                            str(self.parent.messages_font_size))
            elif self.parent.selected_settings == "User Profile":
                width, height = (120, 120)
                self.profile_image_label = create_custom_circular_label(width, height, self)
                self.profile_image_label.setStyleSheet("""
                    QLabel {
                    border-radius: """ + str(height // 2) + """px; /* Set to half of the label height */
                    }
                    QLabel:hover {
                        background-color: #2980b9; /* Change background color on hover */
                    }
                """)

                profile_image_x, profile_image_y = (800, 200)
                if self.parent.profile_pic is None:
                    icon_path = "discord_app_assets/regular_profile.png"
                    set_icon_to_label(self.profile_image_label, icon_path, width, height)
                else:
                    circular_pic_bytes = make_circular_image(self.parent.profile_pic)
                    set_icon_from_bytes_to_label(self.profile_image_label, circular_pic_bytes)
                self.profile_image_label.move(profile_image_x, profile_image_y)
                change_profile_pic_button = self.create_colored_button(dark_green, other_green, None,
                                                                      800,
                                                                      400, 100,
                                                                      30, "Change Avatar")
                change_profile_pic_button.clicked.connect(self.edit_profile_pic_pressed)




        except Exception as e:
            print(e)

    def edit_profile_pic_pressed(self):
        self.open_file_dialog()

    def open_file_dialog(self):
        width, height = (120, 120)
        if self.file_dialog.exec_():
            selected_files = self.file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                image_bytes = image_to_bytes(selected_files[0])
                if is_valid_image(image_bytes):
                    self.parent.profile_pic = image_bytes
                    self.parent.activateWindow()
                    circular_pic = make_circular_image(file_path)
                    if circular_pic is not None:
                        open_image_bytes(circular_pic)
                        set_icon_from_bytes_to_label(self.profile_image_label, circular_pic)


    def font_size_changed(self, font_size):
        try:
            self.parent.font_size = int(font_size)
            self.font_size_label.setText(str(font_size))
            self.parent.updated_chat()
        except Exception as e:
            print(e)

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
            push_to_talk_label = self.push_to_talk_label(x, y, 20, 340, 50, self.parent.push_to_talk_key, "white", border_color)

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
        if not self.parent.is_push_to_talk:
            text1 = "Voice Activity"
            voice_activity_button = self.create_colored_button(brighter_blue, brighter_blue, brighter_blue, buttons_x, starter_y, width_buttons,height_buttons, text1)
            text2 = "Push to Talk"
            second_button_y = starter_y + 60
            push_to_talk_button = self.create_colored_button(regular_blue, brighter_blue, regular_blue, buttons_x, second_button_y, width_buttons,height_buttons, text2)
            voice_activity_button.clicked.connect(self.change_input_mode)
            push_to_talk_button.clicked.connect(self.change_input_mode)
            selected_button_image = self.create_image_label(selected_path, icons_size, icons_size, buttons_x + 5, starter_y+10)
            not_selected_button_image = self.create_image_label(not_selected_path, icons_size, icons_size, buttons_x + 5, second_button_y + 10)
        else:
            text1 = "Voice Activity"
            voice_activity_button = self.create_colored_button(regular_blue, brighter_blue, regular_blue, buttons_x, starter_y, width_buttons,height_buttons, text1)
            text2 = "Push to Talk"
            second_button_y = starter_y + 60
            push_to_talk_button = self.create_colored_button(brighter_blue, brighter_blue, brighter_blue, buttons_x, second_button_y, width_buttons,height_buttons, text2)
            voice_activity_button.clicked.connect(self.change_input_mode)
            push_to_talk_button.clicked.connect(self.change_input_mode)
            selected_button_image = self.create_image_label(selected_path, icons_size, icons_size, buttons_x + 5, second_button_y + 10)
            not_selected_button_image = self.create_image_label(not_selected_path, icons_size, icons_size, buttons_x + 5, starter_y + 10)

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
                background-color: {self.parent.background_color};
                border: 2px solid #2980b9;
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
                background-color: #2980b9;
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
                border: 2px solid #2980b9;
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














