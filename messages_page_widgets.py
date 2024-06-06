from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from functools import partial
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QGraphicsBlurEffect
from PyQt5.QtCore import QSize, Qt, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter, QPainterPath, QFont
from PyQt5.QtMultimedia import QMediaContent
from io import BytesIO
import base64
import zlib
from PIL import Image
import tempfile
import os
import math
import subprocess
import random
import string
import pyaudio
import cv2
import hashlib
import re


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


def is_base64_encoded(s):
    try:
        # Attempt to decode the Base64 string
        decoded_bytes = base64.b64decode(s)
        return True
    except:
        # If decoding fails, it's not a valid Base64 string
        return False


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


def replace_non_space_with_star(string1):
    result = ''
    for char in string1:
        if char != ' ' and not char.isspace():
            result += '*'
        else:
            result += char
    return result


def generate_random_filename(extension):
    # Generate a random string of characters
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"file_{random_string}.{extension}"


def open_pptx_from_bytes(pptx_bytes):
    temp_file_path = save_bytes_to_temp_file(pptx_bytes, 'pptx')
    open_file_with_default_app(temp_file_path)


def open_docx_from_bytes(docx_bytes):
    temp_file_path = save_bytes_to_temp_file(docx_bytes, 'docx')
    open_file_with_default_app(temp_file_path)


def open_xlsx_from_bytes(xlsx_bytes):
    temp_file_path = save_bytes_to_temp_file(xlsx_bytes, 'xlsx')
    open_file_with_default_app(temp_file_path)


def open_py_from_bytes(py_bytes):
    temp_file_path = save_bytes_to_temp_file(py_bytes, 'py')
    open_file_with_default_app(temp_file_path)


def open_pdf_from_bytes(pdf_bytes):
    temp_file_path = save_bytes_to_temp_file(pdf_bytes, 'pdf')
    open_file_with_default_app(temp_file_path)


def is_bytes_exist_as_temp(bytes_sequence):
    try:
        file_hash = hashlib.sha256(bytes_sequence).hexdigest()
        # Get the temporary directory
        temp_dir = tempfile.gettempdir()
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            # Open and read the existing file
            try:
                file_bytes = file_to_bytes(file_path)
                if hashlib.sha256(file_bytes).hexdigest() == file_hash:
                    return file_path
            except:
                pass
        return False
    except Exception as e:
        print(e)
        return False


def save_bytes_to_temp_file(file_bytes, extension):
    # Calculate the hash of the file bytes
    path = is_bytes_exist_as_temp(file_bytes)
    if path:
        return path

    # If no matching file is found, create a new temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.' + extension, delete=False)
    temp_file.write(file_bytes)
    temp_file.close()

    return temp_file.name


def open_file_with_default_app(file_path):
    try:
        if os.name == 'nt':
            os.startfile(file_path)
        elif os.name == 'posix':
            subprocess.run(['xdg-open', file_path])
        else:
            print("Unsupported operating system.")
    except Exception as e:
        print(f"Error opening file: {e}")


def open_text_file_from_bytes(file_bytes):
    try:
        # Create a temporary file
        file_path = is_bytes_exist_as_temp(file_bytes)
        if not file_path:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')

            # Write the bytes to the temporary file
            temp_file.write(file_bytes)
            temp_file.flush()

            # Get the path to the temporary file
            file_path = temp_file.name

        # Open the temporary file using Notepad asynchronously
        subprocess.Popen(['notepad', file_path])
    except Exception as e:
        print(f"Error opening text file: {e}")


def download_file_from_bytes(file_bytes, file_extension, file_name):
    try:
        # Get the path to the user's downloads directory
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not file_name:
            file_name = generate_random_filename(file_extension)
        path = os.path.join(downloads_dir, file_name)

        if path:
            # Write the file bytes to disk
            with open(path, 'wb') as file:
                file.write(file_bytes)

            print(f"File downloaded successfully to '{path}'.")
        else:
            print("Download canceled by user.")
    except Exception as e:
        print(f"Error downloading file: {e}")


def play_mp3_from_bytes(mp3_bytes, media_player):
    try:
        # Save MP3 bytes to a temporary file
        if mp3_bytes is not None:
            media_player.stop()
            temp_file_path = save_bytes_to_temp_file(mp3_bytes, 'mp3')

            # Create QMediaContent object with the URL pointing to the temporary file
            media_content = QMediaContent(QUrl.fromLocalFile(temp_file_path))

            # Create QMediaPlayer instance and set the media content
            media_player.setMedia(media_content)

            # Play the media
            media_player.play()
        else:
            print("got None object instead of bytes can't play")
    except Exception as e:
        print(f"Error playing MP3: {e}")


def format_label_text_by_row(label, text, num_rows):
    try:
        # Calculate the total number of characters per row, including the possibility of a shorter last row
        chars_per_row = len(text) // num_rows
        extra_chars = len(text) % num_rows

        # Initialize variables for storing formatted text and the starting index
        formatted_text = ""
        start_index = 0

        # Iterate through each row
        for row in range(num_rows):
            # Calculate the end index for this row
            end_index = start_index + chars_per_row

            # Add an extra character to this row if needed
            if row < extra_chars:
                end_index += 1

            # Add the substring to the formatted text with a newline character
            formatted_text += text[start_index:end_index] + "\n"

            # Update the starting index for the next row
            start_index = end_index

        # Set the formatted text to the label
        label.setText(formatted_text)
    except Exception as e:
        print(f" error in creating formated label by rows: {e}")


def make_q_object_clear(object):
    object.setStyleSheet("background-color: transparent; border: none;")


def extract_first_frame(video_bytes):
    try:
        # Write video bytes to a temporary file
        file_path = is_bytes_exist_as_temp(video_bytes)
        is_exist = True

        if not file_path:
            is_exist = False
            temp_video_path = tempfile.NamedTemporaryFile(delete=False)
            temp_video_path.write(video_bytes)
            temp_video_path.close()
            file_path = temp_video_path.name

        # Open the temporary video file
        cap = cv2.VideoCapture(file_path)

        # Read the first frame
        ret, frame = cap.read()

        # Release the video capture object and delete the temporary file
        cap.release()
        cv2.destroyAllWindows()

        if not is_exist:
            temp_video_path.close()

        # Convert the first frame to bytes
        retval, buffer = cv2.imencode('.png', frame)
        if retval:
            return buffer.tobytes()
        else:
            return None

    except Exception as e:
        print(f"Error extracting first frame: {e}")
        return None


def open_image_bytes(image_bytes):
    try:
        temp_file_path = save_bytes_to_temp_file(image_bytes, 'png')
        open_file_with_default_app(temp_file_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return False


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


def create_custom_circular_button(width, height, parent):
    button = QPushButton(parent)

    button_size = QSize(width, height)
    button.setFixedSize(button_size)

    button.setStyleSheet("""
        QLabel {
            border-radius: """ + str(height // 2) + """px; /* Set to half of the label height */
            background-color: transparent; /* Make the background color transparent */

        }
    """)

    return button


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


# works very well for a circular labels
def set_icon_from_bytes_to_label(label, image_bytes):
    # Load the image from bytes
    try:
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
    except Exception as e:
        print(f"error in loading image from bytes {e}")


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


def set_icon_from_bytes_to_button(button, image_bytes):
    try:
        # Load the image from bytes
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)

        # Get the size of the button
        button_size = button.size()
        button_width = button_size.width()
        button_height = button_size.height()

        # Calculate the aspect ratio of the image
        image_width = pixmap.width()
        image_height = pixmap.height()
        image_aspect_ratio = image_width / image_height

        # Determine how to scale the image based on its aspect ratio
        if image_aspect_ratio <= 0.5:
            scaled_pixmap = pixmap.scaledToWidth(button_width, Qt.SmoothTransformation)
        elif image_aspect_ratio >= 1.5:
            scaled_pixmap = pixmap.scaledToHeight(button_height, Qt.SmoothTransformation)
        else:
            scaled_pixmap = pixmap.scaled(button_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Set the scaled pixmap to the button
        button.setIcon(QIcon(scaled_pixmap))
        button.setIconSize(button_size)
        button.setStyleSheet("border: 0;")  # Optional: remove border
    except Exception as e:
        print(f"Error in loading image from bytes: {e}")


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
        if friends_list_length % 5 == 0:
            return friends_list_length // 5
        return (friends_list_length // 5) + 1


def gets_group_attributes_from_format(group_format):
    if "(" not in group_format:
        return group_format, None
    else:
        parts = group_format.split(")")
        id = parts[0][1]
        name = parts[1]
        return name, int(id)


class ChatBox(QWidget):

    def __init__(self, messages_list, Network, parent=None):
        super().__init__()
        try:
            screen = QDesktopWidget().screenGeometry()
            # Extract the screen width and height
            self.screen_width = screen.width()
            self.screen_height = screen.height()
            self.Network = Network
            self.parent = parent
            self.is_getting_called = self.parent.is_getting_called
            self.square_label = QLabel(self)
            self.width_of_chat_box = int(self.screen_width * 0.416)
            self.height_of_chat_box = int(self.screen_height * 0.926)
            self.file_dialog = QFileDialog(self)
            self.file_dialog.setFileMode(QFileDialog.ExistingFile)
            filter_str = "All files (*)"
            self.file_dialog.setNameFilter(filter_str)

            self.image_file_dialog = QFileDialog(self)
            self.image_file_dialog.setFileMode(QFileDialog.ExistingFile)

            # Filter for PNG and JPEG files
            filter_str = "Images (*.png *.jpg *.jpeg)"  # Include all common JPEG extensions
            self.image_file_dialog.setNameFilter(filter_str)

            self.file_name = ""
            self.image_height = int(self.screen_height * 0.277)
            self.image_width = int(self.screen_width * 0.1197)
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

            self.draw_message_start_x = int(self.screen_width * 0.323)
            self.friends_button_height = int(self.screen_height * 0.0462)

            self.create_group_open = QPushButton(self)

            # Load an image and set it as the button's icon
            icon = QIcon("discord_app_assets/add_image_button.png")
            self.create_group_open.setIcon(icon)

            # Set the desired size for the button

            width, height = int(self.screen_width * 0.013), int(self.screen_height * 0.023)
            button_size = QSize(width, height)  # Adjust this to your desired button size
            self.create_group_open.setFixedSize(button_size)

            # Scale the icon while keeping its aspect ratio
            icon_size = QSize(width, height)  # Set your desired icon size
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
            self.create_group_open_x = int(self.screen_width * 0.2968)
            self.create_group_open_y = int(self.screen_height * 0.132)
            self.create_group_open.move(self.create_group_open_x, self.create_group_open_y)
            self.create_group_open.clicked.connect(self.create_group_clicked)
            self.text_entry = QLineEdit(self)
            self.text_entry.hide()

            self.square_pos = (int(self.screen_width * 0.3125), 0)
            self.square_label.setGeometry(self.square_pos[0], self.square_pos[1], self.width_of_chat_box,
                                          self.height_of_chat_box)
            self.square_label.setStyleSheet(f"background-color: {self.parent.background_color_hex}; border: 5px solid {self.parent.standard_hover_color};")

            around_name_y = self.square_pos[1]
            around_name_x = self.square_pos[0]
            self.around_name = QLabel(self)
            self.around_name.setStyleSheet(f"background-color: {self.parent.background_color_hex}; border: 5px solid {self.parent.standard_hover_color};")
            start_height_of_around_name = int(self.screen_height * 0.0462)
            height_of_around_name = start_height_of_around_name
            self.around_name_delta = int(self.screen_height * 0.2037)
            if (self.parent.is_calling and self.parent.selected_chat == self.parent.calling_to) or \
                    (self.parent.is_in_a_call and self.parent.selected_chat == self.parent.in_call_with):
                height_of_around_name = start_height_of_around_name + self.around_name_delta

            self.call_profiles_list = []

            self.current_chat, self.current_group_id = gets_group_attributes_from_format(self.parent.selected_chat)
            if self.current_group_id:
                if self.parent.is_call_dict_exist_by_group_id(self.current_group_id):
                    height_of_around_name = start_height_of_around_name + self.around_name_delta

            self.around_name.setGeometry(self.square_pos[0], around_name_y, self.width_of_chat_box, height_of_around_name)
            self.around_name.move(around_name_x, around_name_y)
            self.around_name.raise_()

            self.call_profiles_list = []

            if self.parent.selected_chat != "":
                temp_widget_x, temp_widget_y = (int(self.screen_width * 0.3177), height_of_around_name)
                temp_widget_width = int(self.width_of_chat_box * 0.98)
                if height_of_around_name != start_height_of_around_name:
                    temp_widget_height = self.height_of_chat_box - int(self.screen_height * 0.12037) - self.around_name_delta
                else:
                    temp_widget_height = self.height_of_chat_box - int(self.screen_height * 0.12037)

                if self.parent.is_messages_need_update or self.parent.messages_content_saver is None:
                    temp_widget = MessagesBox(self, temp_widget_width, temp_widget_height, temp_widget_x, temp_widget_y)
                    self.parent.messages_content_saver = temp_widget
                    self.parent.is_messages_need_update = False
                else:
                    self.parent.messages_content_saver.update_scroll_area_parent(self)
                self.around_name.raise_()
                self.ringing_square_label = QLabel(self)

                self.send_image_button = QPushButton(self)

                # Load an image and set it as the button's icon
                icon = QIcon("discord_app_assets/add_image_button.png")
                self.send_image_button.setIcon(icon)

                # Set the desired size for the button
                width, height = int(self.screen_width * 0.018), int(self.screen_height * 0.032)

                button_size = QSize(width, height)  # Adjust this to your desired button size
                self.send_image_button.setFixedSize(button_size)

                # Scale the icon while keeping its aspect ratio
                icon_size = QSize(width, height)  # Set your desired icon size
                icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

                # Set the scaled icon size for the button
                self.send_image_button.setIconSize(scaled_size)
                self.send_image_y = int(self.screen_height * 0.859)
                self.send_image_x = int(self.screen_width * 0.3177)
                self.send_image_button.move(self.send_image_x, self.send_image_y)
                self.send_image_button.setStyleSheet(f"""            
                QPushButton:hover {{
                    background-color: {self.parent.standard_hover_color};
                }}
                 QPushButton {{
                    background-color: transparent;
                    }}
                QPushButton:pressed {{
                    background-color: #202225;
                    border-color: #72767d;
                }}
                """)
                self.send_image_button.clicked.connect(self.open_file_dialog)

                try:
                    if self.parent.is_calling and self.parent.selected_chat == self.parent.calling_to:
                        try:
                            y_of_label = int(self.screen_height * 0.087)
                            rings_to_x = int(self.screen_width * 0.479)
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
                            width, height = int(self.screen_width * 0.026), int(self.screen_width * 0.026)
                            button_size = QSize(width, height)  # Adjust this to your desired button size
                            self.stop_calling_button.setFixedSize(button_size)


                            icon = QIcon("discord_app_assets/reject_button.png")
                            self.stop_calling_button.setIcon(icon)
                            width, height = int(self.screen_width * 0.033), int(self.screen_width * 0.033)

                            icon_size = QSize(width, height)  # Set your desired icon size
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
                            stop_calling_button_x, stop_calling_button_y = rings_to_x + (text_1_width // 2) - int(self.screen_width * 0.008), y_of_label + int(self.screen_height * 0.101)
                            self.stop_calling_button.move(stop_calling_button_x, stop_calling_button_y)
                            self.stop_calling_button.clicked.connect(self.stop_calling)
                        except Exception as e:
                            print(f"error in showing calling {e}")

                    if self.parent.is_getting_called:
                        pop_up_x = int(self.screen_width * 0.4427)
                        pop_up_y = int(self.screen_height * 0.231)
                        pop_up_width = int(self.screen_width * 0.1041)
                        pop_up_height = int(self.screen_height * 0.2777)

                        text = f"Incoming Call..."
                        y_of_label = pop_up_y + int(self.screen_height * 0.1111)
                        self.incoming_call_label = QLabel(text, self)
                        self.incoming_call_label.setStyleSheet("color: gray; font-size: 14px; margin: 10px "
                                                               ";background-color: transparent;")
                        self.incoming_call_label.move(pop_up_x + int(self.screen_width * 0.0234), y_of_label)

                        text = f"{self.parent.getting_called_by}"
                        self.caller_label = QLabel(text, self)
                        start_point = int(len(text) - 4) * 1
                        font_size = calculate_font_size(text)
                        if start_point < 0:
                            start_point = pop_up_x + int(self.screen_width * 0.026)
                        else:
                            start_point = pop_up_x + int(self.screen_width * 0.026) - start_point

                        self.caller_label.setStyleSheet(f"color: white; font-size: {font_size}px; margin: 10px; "
                                                        "background-color: transparent;")
                        self.caller_label.move(start_point, y_of_label - int(self.screen_height * 0.02777))

                        self.pop_up_label = QLabel(self)
                        custom_color = QColor("#053d76")
                        self.pop_up_label.setStyleSheet(f"background-color: {custom_color.name()};")
                        self.pop_up_label.setGeometry(pop_up_x, pop_up_y, pop_up_width, pop_up_height)

                        self.accept_button = QPushButton(self)
                        self.reject_button = QPushButton(self)

                        # Set button styles
                        width, height = int(self.screen_width * 0.0182),int(self.screen_width * 0.0182)
                        button_size = QSize(width, height)  # Adjust this to your desired button size
                        self.accept_button.setFixedSize(button_size)
                        self.reject_button.setFixedSize(button_size)
                        # Set button icons (assuming you have phone icons available)

                        icon = QIcon("discord_app_assets/accept_button.png")
                        self.accept_button.setIcon(icon)

                        width, height = int(self.screen_width * 0.026), int(self.screen_width * 0.026)

                        icon_size = QSize(width, height)  # Set your desired icon size
                        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

                        self.accept_button.setIconSize(scaled_size)
                        self.accept_button.setStyleSheet(self.call_button_style_sheet)
                        icon = QIcon("discord_app_assets/reject_button.png")
                        self.reject_button.setIcon(icon)
                        icon_size = QSize(width, height)  # Set your desired icon size
                        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
                        self.reject_button.setIconSize(scaled_size)
                        # Set button positions
                        accept_button_x = pop_up_x + int(self.screen_width * 0.059)
                        reject_button_x = pop_up_x + int(self.screen_width * 0.026)

                        self.accept_button.move(accept_button_x, pop_up_y + int(self.screen_height * 0.185))
                        self.reject_button.move(reject_button_x, pop_up_y + int(self.screen_height * 0.185))
                        self.reject_button.setStyleSheet(self.call_button_style_sheet)
                        # Connect button signals to functions
                        self.accept_button.clicked.connect(self.accept_call)
                        self.reject_button.clicked.connect(self.reject_call)
                    if self.parent.is_in_a_call and self.parent.selected_chat == self.parent.in_call_with:
                        try:
                            share_camera_height = int(self.screen_height * 0.041666)
                            share_camera_button_width = int(self.screen_height * 0.041666)
                            share_camera_x = int(self.screen_width * 0.4375)
                            share_camera_y = int(self.screen_height * 0.199)
                            self.share_camera_off_icon = QIcon("discord_app_assets/no_camera_icon.png")
                            self.share_camera_on_icon = QIcon("discord_app_assets/camera_icon.png")
                            self.share_camera_button = self.create_custom_in_call_button(share_camera_height, share_camera_button_width, share_camera_x,
                                                                                share_camera_y, self.share_camera_and_unshare)
                            share_screen_height = int(self.screen_height * 0.041666)
                            share_screen_button_width = int(self.screen_height * 0.041666)
                            share_screen_x = int(self.screen_width * 0.4713)
                            share_screen_y = int(self.screen_height * 0.199)
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

                            deafen_button_height = int(self.screen_height * 0.041666)
                            deafen_button_width = int(self.screen_height * 0.041666)
                            self.deafened_icon = QIcon("discord_app_assets/deafened.png")
                            self.not_deafened_icon = QIcon("discord_app_assets/not_deafened.png")
                            deafen_x = share_screen_x + int(self.screen_width * 0.0338)
                            deafen_y = share_screen_y
                            self.deafen_button = self.create_custom_in_call_button(deafen_button_width, deafen_button_height, deafen_x, deafen_y, self.deafen_and_undeafen)
                            if self.parent.deafen:
                                set_button_icon(self.deafen_button, self.deafened_icon, deafen_button_width, deafen_button_height)
                            else:
                                set_button_icon(self.deafen_button, self.not_deafened_icon, deafen_button_width,
                                                     deafen_button_height)


                            mic_button_height = int(self.screen_height * 0.041666)
                            mic_button_width = int(self.screen_height * 0.041666)
                            self.unmuted_mic_icon = QIcon("discord_app_assets/mic_not_muted_icon.png")
                            self.muted_mic_icon = QIcon("discord_app_assets/mic_muted_icon.png")
                            mic_x = deafen_x + int(self.screen_width * 0.0338)
                            mic_button_y = share_screen_y
                            self.mic_button = self.create_custom_in_call_button(mic_button_width, mic_button_height, mic_x, mic_button_y, self.mute_and_unmute)
                            if self.parent.mute:
                                set_button_icon(self.mic_button, self.muted_mic_icon, mic_button_width, mic_button_height)
                            else:
                                set_button_icon(self.mic_button, self.unmuted_mic_icon, mic_button_width, mic_button_height)

                            self.end_call_button = QPushButton(self)

                            # Set button styles
                            call_button_height = int(self.screen_width * 0.0364)
                            call_button_width = int(self.screen_width * 0.0364)
                            button_size = QSize(call_button_width, call_button_height)  # Adjust this to your desired button size
                            self.end_call_button.setFixedSize(button_size)
                            set_button_icon(self.end_call_button, "discord_app_assets/reject_button.png", call_button_width, call_button_height)
                            self.end_call_button.setStyleSheet(self.call_button_style_sheet)
                            end_call_button_x = mic_x + int(self.screen_width * 0.028)
                            self.end_call_button.move(end_call_button_x,
                                                      share_screen_y-int(self.screen_height * 0.013888))
                            self.end_call_button.clicked.connect(self.end_current_call)

                            call_icons_widget = CallIconsWidget(self, self.current_group_id)
                            starts_x = 900
                            y_of_profiles = 60
                            call_icons_widget.move(starts_x, y_of_profiles)
                            scroll_area_widget_width = 400

                            call_icon_scroll_area = ScrollAreaWidget(self, starts_x, y_of_profiles, scroll_area_widget_width, 130, [call_icons_widget], False)
                        except Exception as e:
                            print(f"error in incall func {e}")
                except Exception as e:
                    print(f"error in first try in chatbox {e}")


                # Load an image and set it as the button's icon
                icon = QIcon("discord_app_assets/ringing_blue_icon.png")
                call_button_x = int(self.screen_width * 0.3125) + (self.width_of_chat_box // 2) + int(self.screen_width * 0.1777)
                call_button_y = int(self.screen_height * 0.0074)
                self.call_button = self.create_top_page_button(call_button_x, call_button_y, icon)
                self.call_button.clicked.connect(self.call_user)
                icon = QIcon("discord_app_assets/add_user.png")
                self.add_user_x = call_button_x - int(self.screen_width * 0.026)
                self.add_user_y = call_button_y
                self.add_user_button = self.create_top_page_button(self.add_user_x, self.add_user_y, icon)
                self.add_user_button.clicked.connect(self.add_user_to_group_pressed)

                if self.current_group_id:
                    group_manager = self.parent.get_group_manager_by_group_id(self.current_group_id)
                    if group_manager == self.parent.username:
                        icon = QIcon("discord_app_assets/edit_name.png")
                        rename_group_x = self.add_user_x - int(self.screen_width * 0.026)
                        rename_group_y = call_button_y
                        self.rename_group = self.create_top_page_button(rename_group_x, rename_group_y, icon)
                        self.rename_group.clicked.connect(self.parent.rename_group_pressed)
                        icon = QIcon("discord_app_assets/edit_image_icon.png")
                        edit_group_image_x = rename_group_x - int(self.screen_width * 0.026)
                        edit_group_image_y = rename_group_y
                        self.edit_group_image_button = self.create_top_page_button(edit_group_image_x, edit_group_image_y,
                                                                                   icon)
                        self.edit_group_image_button.clicked.connect(self.change_group_image)

                    # if in chat where there is a group call gives option to join
                    if self.current_group_id:
                        if self.parent.is_call_dict_exist_by_group_id(self.current_group_id) and not self.parent.is_in_a_call:

                            icon_size = int(self.screen_width * 0.03125)
                            y_of_label = int(self.screen_height * 0.0879)
                            rings_to_x = int(self.screen_width * 0.4791)
                            icon = QIcon("discord_app_assets/accept_button.png")

                            join_button_x = rings_to_x + int(self.screen_width * 0.016666)
                            join_button_y = y_of_label + int(self.screen_height * 0.101)
                            join_button_width_or_height = int(self.screen_width * 0.026)
                            self.join_call_button = self.create_custom_in_call_button(join_button_width_or_height, join_button_width_or_height,
                                                                                      join_button_x, join_button_y,  self.join_call)
                            set_button_icon(self.join_call_button, icon, icon_size, icon_size)
                            call_icons_widget = CallIconsWidget(self, self.current_group_id)
                            starts_x = 900
                            y_of_profiles = 60
                            call_icons_widget.move(starts_x, y_of_profiles)
                            scroll_area_widget_width = 400
                            call_icon_scroll_area = ScrollAreaWidget(self, starts_x, y_of_profiles, scroll_area_widget_width, 130, [call_icons_widget], False)
                    try:
                        starter_x_of_group_members, starter_y_of_group_members = temp_widget_x + self.width_of_chat_box, around_name_y
                        group_members = self.parent.get_group_members_by_group_id(self.current_group_id)
                        group_manager = self.parent.get_group_manager_by_group_id(self.current_group_id)
                        for member in group_members:
                            pos = (starter_x_of_group_members, starter_y_of_group_members)
                            if member == group_manager:
                                button = self.create_member_button(member, pos, True)
                            else:
                                button = self.create_member_button(member, pos, False)

                            starter_y_of_group_members += button.height()
                    except Exception as e:
                        print(f"error in drawing members {e}")

                self.text_entry = QLineEdit(self)
                if self.parent.background_color == "Black and White":
                    text_entry_color = "black"
                else:
                    text_entry_color = "white"
                text_entry_y = self.send_image_y-int(self.screen_height * 0.0046)
                text_entry_x = int(self.screen_width * 0.33854)
                text_entry_height = int(self.screen_height * 0.037)
                self.text_entry.setGeometry(text_entry_x, text_entry_y, self.width_of_chat_box-int(self.screen_width * 0.0364), text_entry_height)
                self.text_entry.setStyleSheet(f"background-color: {self.parent.standard_hover_color}; color: {text_entry_color}; padding: 10px; border: 1px solid #2980b9; border-radius: 5px; font-size: 14px;")
                text = self.current_chat.replace("/", "")
                place_holder_text = "Message" + " " + text
                self.text_entry.setPlaceholderText(place_holder_text)
                self.send_image_button.raise_()
            else:
                try:
                    if self.parent.is_getting_called:
                        pop_up_x = int(self.screen_width * 0.4427)
                        pop_up_y = int(self.screen_height * 0.2314)
                        pop_up_width = int(self.screen_width * 0.1041)
                        pop_up_height = int(self.screen_height * 0.277778)

                        text = f"Incoming Call..."
                        y_of_label = pop_up_y + int(self.screen_height * 0.111111)
                        self.incoming_call_label = QLabel(text, self)
                        self.incoming_call_label.setStyleSheet("color: gray; font-size: 14px; margin: 10px "
                                                               ";background-color: transparent;")
                        self.incoming_call_label.move(pop_up_x + int(self.screen_width * 0.02343), y_of_label)

                        text = f"{self.parent.getting_called_by}"
                        self.caller_label = QLabel(text, self)
                        start_point = int(len(text) - 4) * 1
                        font_size = calculate_font_size(text)
                        if start_point < 0:
                            start_point = pop_up_x + int(self.screen_width * 0.026)
                        else:
                            start_point = pop_up_x + int(self.screen_width * 0.026) - start_point

                        self.caller_label.setStyleSheet(f"color: white; font-size: {font_size}px; margin: 10px; "
                                                        "background-color: transparent;")
                        self.caller_label.move(start_point, y_of_label - int(self.screen_height * 0.0277778))

                        self.pop_up_label = QLabel(self)
                        custom_color = QColor("#053d76")
                        self.pop_up_label.setStyleSheet(f"background-color: {custom_color.name()};")
                        self.pop_up_label.setGeometry(pop_up_x, pop_up_y, pop_up_width, pop_up_height)

                        self.accept_button = QPushButton(self)
                        self.reject_button = QPushButton(self)

                        # Set button styles
                        button_size = QSize(int(self.screen_height * 0.0324), int(self.screen_height * 0.0324))  # Adjust this to your desired button size
                        self.accept_button.setFixedSize(button_size)
                        self.reject_button.setFixedSize(button_size)
                        # Set button icons (assuming you have phone icons available)

                        icon = QIcon("discord_app_assets/accept_button.png")
                        self.accept_button.setIcon(icon)
                        icon_size = QSize(int(self.screen_height * 0.0463), int(self.screen_height * 0.0463))  # Set your desired icon size
                        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)

                        self.accept_button.setIconSize(scaled_size)
                        self.accept_button.setStyleSheet(self.call_button_style_sheet)
                        icon = QIcon("discord_app_assets/reject_button.png")
                        self.reject_button.setIcon(icon)
                        icon_size = QSize(int(self.screen_height * 0.0463), int(self.screen_height * 0.0463))  # Set your desired icon size
                        icon_actual_size = icon.actualSize(icon.availableSizes()[0])
                        scaled_size = icon_actual_size.scaled(icon_size, Qt.KeepAspectRatio)
                        self.reject_button.setIconSize(scaled_size)
                        # Set button positions
                        accept_button_x = pop_up_x + int(self.screen_width * 0.05989)
                        reject_button_x = pop_up_x + int(self.screen_width * 0.026)

                        self.accept_button.move(accept_button_x, pop_up_y + int(self.screen_height * 0.1851))
                        self.reject_button.move(reject_button_x, pop_up_y + int(self.screen_height * 0.1851))
                        self.reject_button.setStyleSheet(self.call_button_style_sheet)
                        # Connect button signals to functions
                        self.accept_button.clicked.connect(self.accept_call)
                        self.reject_button.clicked.connect(self.reject_call)
                except Exception as e:
                    print(f"error in gettin g called {e}")

            # List to store message labels
            try:
                try:

                    self.chat_name_label = QLabel(self.current_chat.replace("/", ""), self)
                    self.chat_name_label.setStyleSheet("color: white; font-size: 20px; margin: 10px;")
                    # Set a fixed width for the label
                    self.chat_name_label.setFixedWidth(int(self.screen_width * 0.1041))
                    chat_name_label_x = int(self.screen_width * 0.3229)
                    self.chat_name_label.move(chat_name_label_x, int(self.screen_height * 0.00277778))
                    self.messages_list = messages_list
                    self.message_labels = []

                    self.filename_label = QLabel(self)
                    self.filename_label.move(int(self.screen_width * 0.3229), int(self.screen_height * 0.76852))
                    file_name_y = int(self.screen_height * 0.7963)
                    file_name_x = int(self.screen_width * 0.3229)
                    file_name_width = int(self.screen_width * 0.15625)
                    self.filename_label.setGeometry(file_name_x, file_name_y, file_name_width, int(self.screen_height * 0.0463))  # Adjust the size as needed
                    self.filename_label.setWordWrap(True)  # Enable word wrap
                    self.filename_label.raise_()
                    self.filename_label.setStyleSheet(
                        "background-color: #333333; color: white; font-size: 16px;"
                    )
                    self.filename_label.hide()
                    self.garbage_button = QPushButton(self)
                    garbage_icon_path = "discord_app_assets/garbage_icon.png"
                    garbage_icon_width, garbage_icon_height = (int(self.screen_height * 0.0324), int(self.screen_height * 0.0324))
                    set_button_icon(self.garbage_button, garbage_icon_path, garbage_icon_width, garbage_icon_height)
                    self.garbage_button.setGeometry(file_name_x + file_name_width - int(self.screen_width * 0.026), file_name_y+int(self.screen_height * 0.0074)
                                                    , garbage_icon_width, garbage_icon_height)
                    self.garbage_button.hide()
                    self.garbage_button.clicked.connect(self.garbage_button_clicked)
                    make_q_object_clear(self.garbage_button)

                    if self.parent.file_name != "":
                        self.filename_label.setText(self.parent.file_name + " is loaded")
                        self.filename_label.show()
                        self.garbage_button.show()
                    else:
                        self.filename_label.setText(self.parent.file_name)

                    self.image_too_big = QLabel(self)

                    self.image_too_big.setGeometry(int(self.screen_width * 0.32291), int(self.screen_height * 0.7685), int(self.screen_width * 0.1041), int(self.screen_height * 0.0463))  # Adjust the size as needed
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
                except Exception as e:
                    print(f"error in drawing filename and image_too_big {e}")

                try:
                    try:
                        self.chats_label = QLabel("DIRECT MESSAGES", self)
                        self.chats_label.setStyleSheet('''
                            color: white;
                            font-size: 12px;
                            padding: 5px;
                            margin-bottom: 2px;
                        ''')

                        friend_starter_y = int(self.screen_height * 0.1574)
                        friend_x = int(self.screen_width * 0.13)
                        self.chats_label.move(friend_x + int(self.screen_width * 0.0078), friend_starter_y - 28)
                        friends_button_y = 90
                        friends_button_height = self.friends_button_height
                        border_height = 912
                        border_width = 350
                        info_y = 902
                        self.border_label = QLabel(self)
                        self.border_label.setStyleSheet(f'''
                                        border: 2px solid {self.parent.standard_hover_color};
                                        border-radius: 5px;
                                        padding: 5px;
                                        margin-bottom: 2px;
                                    ''')
                        self.border_label.setGeometry(friend_x, 0, border_width, border_height)
                        self.border_label.lower()

                        self.border_label2 = QLabel(self)
                        self.border_label2.setStyleSheet(f'''
                                            padding: 5px;
                                            margin-bottom: 2px;
                                            border-top: 2px solid {self.parent.standard_hover_color}; /* Top border */
                                            border-left: 2px solid {self.parent.standard_hover_color}; /* Left border */
                                            border-right: 2px solid {self.parent.standard_hover_color}; /* Right border */
                                        ''')
                        self.border_label2.setGeometry(friend_x, 0, border_width, int(self.screen_height * 0.1574))
                        self.border_label2.lower()

                        find_contact_pos = (260, 20)
                        find_contact_size = (320, 40)
                        self.find_contact_text_entry = QLineEdit(self)
                    except Exception as e:
                        print(f"error in first part of creating direct mesages button")
                    try:
                        if self.parent.background_color == "Black and White":
                            text_entry_color = "black"
                        else:
                            text_entry_color = "white"
                        self.find_contact_text_entry.setPlaceholderText("Find a conversation")
                    except Exception as e:
                        print(f"error in if {e}")

                    try:
                        self.find_contact_text_entry.setStyleSheet(
                            f"background-color: {self.parent.standard_hover_color}; color: {text_entry_color}; padding: 10px; border: 1px solid #2980b9; border-radius: 5px; font-size: 14px;")
                        self.find_contact_text_entry.setGeometry(find_contact_pos[0], find_contact_pos[1], find_contact_size[0],
                                                                 find_contact_size[1])
                        self.find_contact_text_entry.textChanged.connect(self.on_text_changed_in_contact_search)

                        self.friends_button = QPushButton("  Social", self)
                        self.friends_button.setStyleSheet(f'''
                            QPushButton {{
                            color: white;
                            font-size: 15px;
                            border: none;  /* Remove the border */
                            border-radius: 5px;
                            padding: 5px;
                            margin-bottom: 2px;
                            text-align: left;  /* Align the text to the left */
                            alignment: left;   /* Align the icon and text to the left */
                            padding-left: 10px;   /* Adjust the starting position to the right */
                            }}
                            QPushButton:hover {{
                                background-color: {self.parent.standard_hover_color};
                            }}
                
                            QPushButton:pressed {{
                                background-color: #202225;
                                border-color: #72767d;
                            }}
                
                        ''')
                        icon = QIcon("discord_app_assets/friends_icon.png")  # Replace with the path to your icon image
                        self.friends_button.setIcon(icon)

                        # Set the position and size of the button
                        self.friends_button.setGeometry(friend_x + 5, friends_button_y - 10, border_width - int(self.screen_width * 0.0078),
                                                        friends_button_height)  # Adjust size as needed

                        # Set the text alignment to show both the icon and text

                        # Optional: Adjust the spacing between the icon and text
                        self.friends_button.setIconSize(QSize(int(self.screen_height * 0.0463), int(self.screen_height * 0.0463)))  # Adjust size as needed
                        self.friends_button.clicked.connect(self.parent.social_clicked)
                    except Exception as e:
                        print(f"error in second part of try {e}")
                except Exception as e:
                    print(f"error in creating direct mesages button and friends_button {e}")

                try:
                    friend_x = int(self.screen_width * 0.13)
                    x, y = int(self.screen_width * 0.13), int(self.screen_height * 0.1574)
                    width, height = int(self.screen_width * 0.1823), int(self.screen_height * 0.68512)
                    if not self.parent.current_chat_box_search:
                        chats_widget = FriendsChatListWidget(self, self.parent.chats_list)
                        chats_list_scroll_area = ScrollAreaWidget(self, x, y, width, height, [chats_widget], True, "chat_index")
                    else:
                        chats_widget = FriendsChatListWidget(self, self.parent.temp_search_list)
                        chats_list_scroll_area = ScrollAreaWidget(self, x, y, width, height, [chats_widget], True)
                except Exception as e:
                    print(f"error in showing chats list{e}")

                try:
                    username_label = QLabel(self.parent.username, self)
                    if text_entry_color == "black":
                        username_label_background_color = "black"
                    else:
                        username_label_background_color = self.parent.standard_hover_color

                    username_label_margin_bottom = int(self.parent.screen_width * 0.013)
                    username_label_padding = int(self.parent.screen_width * 0.035)
                    username_label.setStyleSheet(f'''
                        color: white;
                        font-size: 20px;
                        background-color: {username_label_background_color};
                        border: 2px solid {self.parent.standard_hover_color};  /* Use a slightly darker shade for the border */
                        border-radius: 5px;
                        padding: {username_label_padding}px;
                        margin-bottom: {username_label_margin_bottom}px;
                    ''')

                    username_label.setGeometry(friend_x, info_y, border_width, 90)

                    profile_image_label_position = int(friend_x + self.parent.screen_width * 0.005), int(info_y + self.parent.screen_height * 0.004)
                    width, height = (55, 55)
                    profile_image_label = create_custom_circular_label(width, height, self)
                    chat_image = self.parent.get_profile_pic_by_username(self.parent.username)
                    if chat_image is None:
                        icon_path = self.parent.regular_profile_image_path
                        set_icon_from_path_to_label(profile_image_label, icon_path)
                    else:
                        circular_pic_bytes = self.parent.get_circular_image_bytes_by_name(self.parent.username)
                        set_icon_from_bytes_to_label(profile_image_label, circular_pic_bytes)
                    profile_image_label.move(profile_image_label_position[0], profile_image_label_position[1])
                except Exception as e:
                    print(f"error in drawing profile pic in chatbox {e}")

                settings_button = QPushButton(self)
                settings_button.setFixedSize(int(self.screen_height * 0.0463), int(self.screen_height * 0.0463))  # Set the fixed size of the button
                # Set the icon for the chat button
                settings_button_icon = QIcon(QPixmap("discord_app_assets/Setting_logo.png"))
                settings_button.setIcon(settings_button_icon)
                settings_button.setIconSize(settings_button_icon.actualSize(QSize(int(self.screen_height * 0.0463), int(self.screen_height * 0.0463))))  # Adjust the size as needed
                settings_button.move(friend_x + 295, info_y + 10)
                settings_button.setStyleSheet('''
                    QPushButton {
                        background-color: transparent;
                    }
        
                ''')
                settings_button.clicked.connect(self.parent.settings_clicked)
                pause_mp3_files_button = QPushButton(self)
                mp3_pause_path = "discord_app_assets/pause_and_play_icon.png"
                set_button_icon(pause_mp3_files_button, mp3_pause_path, 40, 40)
                pause_mp3_files_button.move(friend_x + 240, info_y + 10)
                pause_mp3_files_button.setStyleSheet('''
                    QPushButton {
                        background-color: transparent;
                    }
        
                ''')
                pause_mp3_files_button.clicked.connect(self.parent.pause_or_unpause_mp3_files_player)

                music_page_button = QPushButton(self)
                mp3_pause_path = "discord_app_assets/music_icon.png"
                set_button_icon(music_page_button, mp3_pause_path, 40, 40)
                music_page_button.move(friend_x + 185, info_y + 10)
                music_page_button.setStyleSheet('''
                    QPushButton {
                        background-color: transparent;
                    }
        
                ''')
                music_page_button.clicked.connect(self.parent.music_button_clicked)
                try:
                    if self.parent.is_create_group_pressed:
                       create_group_box = CreateGroupBox(self, self.create_group_open_x, self.create_group_open_y, "create")
                       create_group_box.raise_()
                    elif self.parent.is_create_group_inside_chat_pressed:
                        if self.parent.is_current_chat_a_group:
                            create_group_box = CreateGroupBox(self, self.add_user_x, self.add_user_y, "add")
                        else:
                            create_group_box = CreateGroupBox(self, self.add_user_x, self.add_user_y, "create")
                        create_group_box.raise_()
                    chats_widget.raise_()
                    self.raise_needed_elements()
                except Exception as e:
                    print(f"error in creaing CreateGroupBox in chatbox {e}")
            except Exception as e:
                print(f"error in last level in creating chat box {e}")
        except Exception as e:
            print(f"error in creating chat box {e}")

    def add_user_to_group_pressed(self):
        if self.parent.is_create_group_inside_chat_pressed:
            self.parent.is_create_group_inside_chat_pressed = False
            self.parent.update_chat_page_without_messages()
        else:
            self.parent.is_create_group_pressed = False
            self.parent.is_create_group_inside_chat_pressed = True
            self.parent.update_chat_page_without_messages()

    def change_group_image(self):
        self.open_file_dialog_for_changing_group_image()

    # Layout
    def create_custom_in_call_button(self, width, height, x, y, click_function):
        button = QPushButton(self)

        button_size = QSize(width, height)
        button.setFixedSize(button_size)

        button.move(x, y)

        button.clicked.connect(click_function)

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #6fa8b6;
                background-repeat: no-repeat;
                background-position: center;
                border-radius: {height // 2}px;  /* Set to half of the button height */
            }}
            QPushButton:hover {{
                background-color: {self.parent.standard_hover_color};
            }}
        """)

        return button

    def put_call_icons_on_the_screen(self):
        try:
            if self.current_group_id:
                current_call_dict = self.parent.get_call_dict_by_group_id(self.current_group_id)
            else:
                current_call_dict = self.parent.get_call_dict_by_user(self.parent.username)
            numbers_of_users_in_call = len(current_call_dict.get("participants"))
            starts_x = 900+((numbers_of_users_in_call-2) * -70)
            y_of_profiles = 95

            if current_call_dict is not None:
                names = current_call_dict.get("participants")
                if self.parent.username in names:
                    for name in names:
                        self.create_profile_button(starts_x, y_of_profiles, name, current_call_dict, self)
                        if name in current_call_dict.get("screen_streamers") and name != self.parent.username:
                            stream_type = "ScreenStream"
                            self.create_watch_stream_button(starts_x+10, y_of_profiles-35, name, stream_type, self)
                        if name in current_call_dict.get("camera_streamers") and name != self.parent.username:
                            stream_type = "CameraStream"
                            self.create_watch_stream_button(starts_x+10, y_of_profiles-35, name, stream_type, self)
                        starts_x += 105
        except Exception as e:
            print(f"error is {e} in icon management")

    def create_watch_stream_button(self, x, y, name, stream_type, widgets_parent):
        width, height = (70, 30)
        if stream_type == "ScreenStream":
            button = QPushButton(widgets_parent)
            button_size = QSize(width, height)
            button.setFixedSize(button_size)
            image_icon = f"discord_app_assets/monitor_icon.png"
            set_button_icon(button, image_icon, width, height)  # Corrected function call
        else:
            y -= int(self.screen_height * 0.0463)
            button = QPushButton(widgets_parent)
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
        return button

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

    def create_profile_button(self, x, y, name, dict, widgets_parent):
        try:
            width, height = (90, 90)
            button = create_custom_circular_label(width, height, widgets_parent)

            status_button = QPushButton(widgets_parent)
            make_q_object_clear(status_button)
            width, height = (30, 30)
            button_size = QSize(width, height)
            status_button.setFixedSize(button_size)

            button.move(x, y)

            regular_icon_path = r"discord_app_assets/regular_profile.png"
            muted_icon = QIcon("discord_app_assets/mic_muted_icon.png")
            deafened_icon = QIcon("discord_app_assets/deafened.png")

            if name in dict.get("deafened"):
                set_button_icon(status_button, deafened_icon, width, height)
            elif name in dict.get("muted"):
                set_button_icon(status_button, muted_icon, width, height)

            profile_pic = self.parent.get_circular_image_bytes_by_name(name)
            try:
                if profile_pic is not None:
                    set_icon_from_bytes_to_label(button, profile_pic)
                else:
                    regular_icon_bytes = file_to_bytes(regular_icon_path)
                    set_icon_from_bytes_to_label(button, regular_icon_bytes)
            except Exception as e:
                print(f"error in setting image to profile button {e}")
            status_button.move(x + int(0.7 * button.width()), y + int(0.7 * button.height()))
            self.call_profiles_list.append(button)
            self.call_profiles_list.append(status_button)
            if name in self.parent.muted_users:
                text = f"unmute {name}"
                actions_list = [text]
            else:
                text = f"mute {name}"
                actions_list = [text]
            chat_name = name
            if name != self.parent.username:
                button.setContextMenuPolicy(Qt.CustomContextMenu)
                button.customContextMenuRequested.connect(
                    lambda pos, parent=widgets_parent, button=button, actions_list=actions_list,
                           chat_name=chat_name: self.parent.right_click_object_func(pos, parent, button,
                                                                                    actions_list, chat_name))
            button_layout = QVBoxLayout(button)  # Create a layout for the button
            button_layout.setAlignment(Qt.AlignBottom | Qt.AlignRight)
            button_layout.addWidget(status_button)
            return button
        except Exception as e:
            print(f"error in creating call icons {e}")
            return None

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
        self.parent.update_chat_page_without_messages()

        # Create Group button

    def toggle_checkbox(self, create_or_add_group_widget):
        sender = self.sender()
        if isinstance(sender, QPushButton):
            friend_name = sender.friend_name
            friend_checkbox = next(
                child for child in sender.parent().children()
                if isinstance(child, QCheckBox) and child.friend_name == friend_name
            )
            friend_checkbox.toggle()
            create_or_add_group_widget.update_labels_text()
            self.friend_checkbox_changed(friend_checkbox.isChecked())

    def handle_create_group_index(self, format):
        change = False
        try:
            if format == "down":
                if len(self.parent.friends_list) > (self.parent.create_group_index + 1) * 5:
                    self.parent.create_group_index += 1
                    change = True
            else:
                if self.parent.create_group_index > 0:
                    self.parent.create_group_index -= 1
                    change = True
        except Exception as e:
            print("error in hadnling index")
        if change:
            self.parent.update_chat_page_without_messages()
        else:
            print("no change")

    def create_dm_pressed(self):
        if len(self.parent.selected_group_members) != 0:
            self.Network.create_group(self.parent.selected_group_members)
            print("You a created new group")
            self.parent.is_create_group_pressed = False
            self.parent.is_create_group_inside_chat_pressed = False
            self.parent.selected_group_members.clear()
            self.parent.create_group_index = 0
            self.parent.update_chat_page_without_messages()

    def add_users_to_group(self):
        group_id = self.current_group_id
        if len(self.parent.selected_group_members) != 0:
            self.Network.add_user_to_group(group_id, self.parent.selected_group_members)
            print(f"Added user {self.parent.selected_group_members} to group of id {group_id}")
            self.parent.is_create_group_pressed = False
            self.parent.is_create_group_inside_chat_pressed = False
            self.parent.selected_group_members.clear()
            self.parent.create_group_index = 0
            self.parent.update_chat_page_without_messages()

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
            print(f"friend_checkbox_changed error :{e}")

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
                    self.parent.update_chat_page_without_messages()
                else:
                    try:
                        self.parent.current_chat_box_search = False
                        self.parent.temp_search_list = []
                        self.parent.update_chat_page_without_messages()
                    except Exception as e:
                        print(f"text_changed error :{e}")
        except Exception as e:
            print(f"text_changed error :{e}")

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
            print(f"return_search_list error :{e}")

    def raise_needed_elements(self):
        try:
            if self.parent.selected_chat != "":
                self.add_user_button.raise_()
                if self.current_group_id:
                    group_manager = self.parent.get_group_manager_by_group_id(self.current_group_id)
                    if group_manager == self.parent.username:
                        self.rename_group.raise_()
                        self.edit_group_image_button.raise_()
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

    def create_friend_button(self, label, position, parent):
        px_padding_of_button_text = 55
        chat_name = label
        text, id = gets_group_attributes_from_format(chat_name)
        if id:
            len_group = self.parent.get_number_of_members_by_group_id(id)
        button_text = text

        width, height = (35, 35)
        profile_image_label = create_custom_circular_label(width, height, parent)
        profile_image_x, profile_image_y = (position[0] + (px_padding_of_button_text * 0.25), position[1] + ((self.friends_button_height - height) * 0.5))

        if id:
            chat_image = self.parent.get_circular_image_bytes_by_group_id(id)
        else:
            chat_image = self.parent.get_profile_pic_by_username(chat_name)
        if chat_image is None:
            icon_path = self.parent.regular_profile_image_path
            set_icon_from_path_to_label(profile_image_label, icon_path)
        else:
            if id:
                circular_pic_bytes = chat_image
            else:
                circular_pic_bytes = self.parent.get_circular_image_bytes_by_name(chat_name)
            set_icon_from_bytes_to_label(profile_image_label, circular_pic_bytes)
        profile_image_label.move(profile_image_x, profile_image_y)
        profile_image_label.setAlignment(Qt.AlignCenter)

        button = QPushButton(parent)
        button.setText(button_text)
        button.move(position[0], position[1])
        button.setFixedHeight(self.friends_button_height)
        button.clicked.connect(partial(self.on_friend_button_clicked, label))
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        if not id:
            actions_list = ["remove_chat"]
            button.customContextMenuRequested.connect(
                lambda pos, parent=parent, button=button, actions_list=actions_list,
                       chat_name=chat_name: self.parent.right_click_object_func(pos, parent, button,
                                                                                actions_list, chat_name))
        else:
            actions_list = ["exit_group"]
            button.customContextMenuRequested.connect(
            lambda pos, parent=parent, button=button, actions_list=actions_list,
                   group_id=id: self.parent.right_click_object_func(pos, parent, button,
                                                                            actions_list, group_id=group_id))

        style = f'''
            color: white;
            font-size: 10px;
            margin-bottom: 2px;
            background-color: rgba(0,0,0,0);
            padding-left: {px_padding_of_button_text}px;
        '''

        if id:
            members_label = QLabel(f"{len_group} Members", parent)
            members_label.setStyleSheet(style)
            memeber_x = position[0] + px_padding_of_button_text
            members_label.move(memeber_x, position[1] + 28)


        padding_top = "padding-top: -7px;" if label.startswith("(") else ""  # Adjust the padding value as needed

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.parent.background_color_hex};
                border: 2px solid {self.parent.standard_hover_color};
                border-radius: 5px;
                padding: 8px 16px;
                padding-left: {px_padding_of_button_text}px;  /* Adjust the padding to move text to the right */
                {padding_top}
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
        profile_image_label.raise_()
        if id:
            members_label.raise_()
            members_label.setAlignment(Qt.AlignLeft)

            # Create a layout for the button and add the labels
            button_layout = QVBoxLayout(button)
            button_layout.addWidget(profile_image_label)
            button_layout.addWidget(members_label)
            button.setLayout(button_layout)
        else:
            button_layout = QVBoxLayout(button)
            button_layout.addWidget(profile_image_label)
            button.setLayout(button_layout)

        return button

    def create_member_button(self, label, position, is_manager):

        px_padding_of_button_text = 55
        chat_name = label
        if is_manager:
            button_text = chat_name + " 👑"
        else:
            button_text = chat_name

        width, height = (35, 35)
        profile_image_label = create_custom_circular_label(width, height, self)
        profile_image_x, profile_image_y = (position[0] + (px_padding_of_button_text * 0.25), position[1] + ((self.friends_button_height - height) * 0.5))

        chat_image = self.parent.get_profile_pic_by_username(chat_name)
        if chat_image is None:
            icon_path = self.parent.regular_profile_image_path
            set_icon_from_path_to_label(profile_image_label, icon_path)
        else:
            circular_pic_bytes = self.parent.get_circular_image_bytes_by_name(chat_name)
            set_icon_from_bytes_to_label(profile_image_label, circular_pic_bytes)
        profile_image_label.move(profile_image_x, profile_image_y)
        button = QPushButton(self)
        button.setText(button_text)
        button.move(position[0], position[1])
        button.setFixedHeight(self.friends_button_height)
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        manager = self.parent.get_group_manager_by_group_id(self.current_group_id)
        if chat_name != self.parent.username:
            if chat_name not in self.parent.friends_list:
                actions_list = ["add_friend", "message_user"]
                if manager == self.parent.username:
                    actions_list.append("remove_user_from_group")
                button.customContextMenuRequested.connect(
                    lambda pos, parent=self, button=button, actions_list=actions_list,
                           chat_name=chat_name, group_id=self.current_group_id: self.parent.right_click_object_func(pos, parent, button,
                                                                                    actions_list, chat_name, group_id))
            else:
                actions_list = ["message_user"]
                if manager == self.parent.username:
                    actions_list.append("remove_user_from_group")
                button.customContextMenuRequested.connect(
                    lambda pos, parent=self, button=button, actions_list=actions_list,
                           chat_name=chat_name, group_id=self.current_group_id: self.parent.right_click_object_func(pos, parent, button,
                                                                                    actions_list, chat_name, group_id))

        padding_top = "padding-top: -7px;" if label.startswith("(") else ""  # Adjust the padding value as needed
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.parent.background_color_hex};
                border: 2px solid {self.parent.standard_hover_color};
                border-radius: 5px;
                padding: 8px 16px;
                padding-left: {px_padding_of_button_text}px;  /* Adjust the padding to move text to the right */
                {padding_top}
                color: white;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                text-align: left;
            }}
        """)

        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedWidth(350)
        button.raise_()
        profile_image_label.raise_()

        return button

    def raise_around_name_label(self):
        self.around_name.raise_()

    def open_file_dialog_for_changing_group_image(self):
        if self.image_file_dialog.exec_():
            selected_files = self.image_file_dialog.selectedFiles()
            file_types = [os.path.splitext(file)[1][1:].lower() for file in selected_files]
            file_path = selected_files[0]  # Get the file path
            file_size = os.path.getsize(file_path)  # Get the file size in bytes

            # Check if the file size is greater than 10 MB (10 * 1024 * 1024 bytes)
            if file_size > 10 * 1024 * 1024:
                print("File size exceeds the limit (10 MB).")
                return
            if selected_files and file_types[0] in ["png", "jpg"]:
                image_bytes = file_to_bytes(selected_files[0])

                if is_valid_image(image_bytes):
                    self.Network.send_new_group_image_to_server(image_bytes, self.current_group_id)
                    print("sent new image to server")
                else:
                    print("couldn't load image")

    def open_file_dialog(self):
        basic_files_types = ["xlsx", "py", "docx", "pptx", "txt", "pdf"]
        if self.file_dialog.exec_():
            selected_files = self.file_dialog.selectedFiles()
            file_types = [os.path.splitext(file)[1][1:].lower() for file in selected_files]
            self.parent.file_name = selected_files[0].split("/")[-1]
            file_path = selected_files[0]  # Get the file path
            file_size = os.path.getsize(file_path)  # Get the file size in bytes

            # Check if the file size is greater than 10 MB (10 * 1024 * 1024 bytes)
            if file_size > 10 * 1024 * 1024:
                print("File size exceeds the limit (10 MB).")
                return
            if selected_files and file_types[0] in ["png", "jpg"]:
                image_bytes = file_to_bytes(selected_files[0])

                if is_valid_image(image_bytes):
                    self.parent.file_to_send = image_bytes
                    print("image to send defined")
                    self.filename_label.setText(self.parent.file_name + " is loaded")
                    self.filename_label.show()
                    self.parent.update_chat_page_without_messages()
                    self.parent.activateWindow()
                else:
                    print("couldn't load image")
            elif selected_files and file_types[0] in ["mp4", "mov"]:
                video_bytes = file_to_bytes(selected_files[0])
                self.parent.file_to_send = video_bytes
                self.filename_label.setText(self.parent.file_name + " is loaded")
                self.filename_label.show()
                self.parent.update_chat_page_without_messages()
                self.parent.activateWindow()
            elif selected_files and file_types[0] in ["mp3"]:
                audio_bytes = file_to_bytes(selected_files[0])
                self.parent.file_to_send = audio_bytes
                self.filename_label.setText(self.parent.file_name + " is loaded")
                self.filename_label.show()
                self.parent.update_chat_page_without_messages()
                self.parent.activateWindow()
            elif selected_files and file_types[0] in basic_files_types:
                file_bytes = file_to_bytes(selected_files[0])
                self.parent.file_to_send = file_bytes
                self.filename_label.setText(self.parent.file_name + " is loaded")
                self.filename_label.show()
                self.parent.update_chat_page_without_messages()
                self.parent.activateWindow()

    def file_to_bytes(self, file_path):
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
        try:
            print("trying to join call of current group")
            self.parent.is_joining_call = True
            self.parent.joining_to = self.parent.selected_chat
            self.Network.send_join_call_of_group_id(self.current_group_id)
        except Exception as e:
            print(f"error in joining call {e}")

    def end_current_call(self):
        self.parent.end_current_call()

    def mute_and_unmute(self):
        try:
            if self.parent.mute:
                media_content = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Discord_mute_sound_effect.mp3'))
                self.parent.play_sound_effect(media_content)
                print("mic is not muted")
                self.parent.mute = False
                self.mic_button.setIcon(self.unmuted_mic_icon)
                self.Network.toggle_mute_for_myself()
            else:
                media_content = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Discord_mute_sound_effect.mp3'))
                self.parent.play_sound_effect(media_content)
                print("mic is muted")
                self.parent.mute = True
                self.mic_button.setIcon(self.muted_mic_icon)
                self.Network.toggle_mute_for_myself()
        except Exception as e:
            print(f"error mute_and_unmute {e}")

    def deafen_and_undeafen(self):
        if self.parent.deafen:
            media_content = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Discord_mute_sound_effect.mp3'))
            self.parent.play_sound_effect(media_content)
            self.parent.deafen = False
            self.deafen_button.setIcon(self.not_deafened_icon)
            self.Network.toggle_deafen_for_myself()
        else:
            media_content = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Discord_mute_sound_effect.mp3'))
            self.parent.play_sound_effect(media_content)
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
        if not self.parent.getting_called_by.startswith("("):
            self.selected_chat_changed(self.parent.getting_called_by)
        else:
            group_id, group_name, group_caller = parse_group_caller_format(self.parent.getting_called_by)
            group_full_name = f"{group_id}{group_name}"
            self.selected_chat_changed(group_full_name

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
            print(f"error ringing_user {e}")

    def call_user(self):
        try:
            if not self.parent.is_getting_called and not self.parent.is_calling and not self.parent.is_in_a_call:
                if self.parent.selected_chat.startswith("("):
                    print(f"Calling Group...{self.parent.selected_chat}")  # Replace this with your actual functionality
                else:
                    print(f"Calling User...{self.parent.selected_chat}")  # Replace this with your actual functionality
                media_content = QMediaContent(QUrl.fromLocalFile('discord_app_assets/Phone_Internal_RingingCalling - Sound Effect.mp3'))
                self.parent.play_calling_sound_effect(media_content)
                self.Network.send_calling_user(self.parent.selected_chat)
                self.ringing_user(self.parent.selected_chat)
        except Exception as e:
            print(f"error call_user {e}")

    def on_friend_button_clicked(self, label):
        try:
            self.selected_chat_changed(label)
        except Exception as e:
            print(f"error on_friend_button_clicked {e}")

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
        image = QImage.fromData(image_bytes)

        if image.isNull() or image.width() == 0 or image.height() == 0:
            print("There is an error with image_bytes")
            return

        # Calculate the scaled size while maintaining the aspect ratio
        aspect_ratio = image.width() / image.height()
        target_width = self.image_width
        target_height = int(target_width / aspect_ratio)

        # Scale the image to the target size
        scaled_image = image.scaled(target_width, target_height, Qt.KeepAspectRatio)

        # Convert the QImage to QPixmap for displaying in the button
        pixmap = QPixmap.fromImage(scaled_image)

        # Set the button's icon
        button.setIconSize(pixmap.size())
        button.setIcon(QIcon(pixmap))
        button.setGeometry(100, 100, self.image_width, target_height)  # Adjust size as needed

    def show_context_menu(self, pos, button, file_bytes, type, file_name):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                color: white; /* Text color of menu items */
                border: 1px solid gray; /* Border style */
            }}
            QMenu::item:selected {{
                background-color: {self.parent.standard_hover_color}; /* Hover color when item is selected */
            }}
        """)
        download_action = menu.addAction("Download")
        download_action.triggered.connect(lambda: download_file_from_bytes(file_bytes, type, file_name))

        # Use the position of the button as the reference for menu placement
        global_pos = button.mapToGlobal(pos)

        # Show the context menu at the adjusted position
        menu.exec_(global_pos)

    def create_temp_message_label(self, message):
        try:
            label = QLabel(message, self)
            label.setStyleSheet(f"color: white")
            font = QFont(self.parent.font_text)
            font.setPixelSize(self.parent.font_size)
            label.setFont(font)
            number_of_rows = math.floor(len(message) / 160) + 1
            if len(message) > 0 and number_of_rows > 1:
                format_label_text_by_row(label, message, number_of_rows)
                label.adjustSize()
            return label
        except Exception as e:
            print(f"error in creating message label {e}")
            return None

    def check_editing_status(self):
        return self.text_entry.hasFocus()

    def garbage_button_clicked(self):
        self.parent.file_to_send = None
        self.parent.file_name = ""
        self.parent.update_chat_page_without_messages()

    def selected_chat_changed(self, name):
        if name != self.parent.selected_chat:
            self.parent.is_new_chat_clicked = True
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
                print(f"error selected_chat_changed {e}")
            self.parent.selected_chat = name
            self.parent.chat_start_index = None
            self.Network.updated_current_chat(name)
            self.image_too_big.hide()
            self.parent.size_error_label = False
            self.parent.file_to_send = None
            self.parent.change_chat_index = None
            self.parent.is_create_group_inside_chat_pressed = False
            self.parent.file_name = ""
            self.messages_list = []
            # self.parent.updated_chat()

    def is_mouse_on_chat_box(self, mouse_pos):
        box_geometry = self.square_label.geometry()
        return box_geometry.contains(mouse_pos)

    def change_chat_index(self, index):
        self.parent.chat_index = index


class MessagesBox(QWidget):
    def __init__(self, parent, width, height, x, y):
        super().__init__()
        self.parent = parent
        self.width = width
        self.height = height
        self.main_page_object = parent.parent
        self.x = x
        self.y = y
        self.init_ui()

    def init_ui(self):
        # Create a scroll area
        try:
            self.scroll_area = QScrollArea(self.parent)
            self.scroll_area.setStyleSheet("""
                QScrollArea {
                    border: none;
                }
                QScrollBar:vertical {
                    border: none;
                }
                QScrollBar:horizontal {
                    border: none;
                }
            """)
            self.scroll_area.setWidgetResizable(True)

            # Create a widget to contain labels and buttons
            inner_widget = QWidget()

            # Create a layout for the inner widget
            self.layout = QVBoxLayout(inner_widget)
            self.space_between_widgets = int(self.parent.screen_height * 0.00925925925)
            self.layout.setSpacing(self.space_between_widgets)  # Adjust this value as needed
            self.layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Align widgets to the left and top

            # Add labels and buttons to the layout
            self.load_all_message_func(reversed(self.parent.parent.list_messages))

            # Set the inner widget as the scroll area's widget
            self.scroll_area.setWidget(inner_widget)
            self.scroll_area.setGeometry(self.x, self.y, self.width, self.height)  # Set the geometry directly
            if self.parent.parent.is_new_chat_clicked:
                maximum = self.scroll_area.verticalScrollBar().maximum()
                self.scroll_area.verticalScrollBar().setValue(maximum)
                print(f"Scrolled to maximum {maximum}")
                self.scroll_value_changed(maximum)
                # Reset the flag
                self.parent.parent.is_new_chat_clicked = False
            else:
                if self.parent.parent.chat_start_index is not None:
                    self.scroll_area.verticalScrollBar().setValue(self.parent.parent.chat_start_index)
            self.scroll_area.verticalScrollBar().valueChanged.connect(self.scroll_value_changed)
        except Exception as e:
            print(f"Error in creating messages box {e}")

    def scroll_maximum(self):
        maximum = self.scroll_area.verticalScrollBar().maximum()
        self.scroll_area.verticalScrollBar().setValue(maximum)

    def update_scroll_area_parent(self, new_parent):
        self.setParent(new_parent)
        self.parent = new_parent
        self.scroll_area.setParent(new_parent)

    def load_all_message_func(self, message_list):
        for i in message_list:
            self.add_message_to_layout(i)

    def add_message_to_layout(self, message):
        self.add_or_insert_message_to_layout(message, False)

    def insert_message_to_layout(self, message):
        self.add_or_insert_message_to_layout(message, True)

    def insert_messages_list_to_layout(self, message_list):
        for i in message_list:
            self.insert_message_to_layout(i)

    def add_new_message_at_start(self, message_dict):
        self.add_message_to_layout(message_dict)

    def add_or_insert_message_to_layout(self, message, is_insert):
        basic_files_types = ["xlsx", "py", "docx", "pptx", "txt", "pdf"]
        i = message
        message_content = i.get("content")
        message_time = i.get("timestamp")
        message_sender = i.get("sender_id")
        message_type = i.get("message_type")
        file_name = i.get("file_name")
        if not message_content or message_type == "string":
            if message_sender != self.main_page_object.username:
                if self.main_page_object.censor_data_from_strangers:
                    if (message_sender not in self.main_page_object.friends_list):
                        message_content = replace_non_space_with_star(message_content)
                if message_sender in self.main_page_object.blocked_list or (
                        self.main_page_object.is_private_account and message_sender not in self.main_page_object.friends_list):
                    message_content = replace_non_space_with_star(message_content)
            content_label = self.parent.create_temp_message_label(message_content)

            # second part = Name + timestamp
            title_label = self.parent.create_temp_message_label("")
            title_label.setText(
                f'<span style="font-size: {self.main_page_object.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                f'<span style="font-size: {self.main_page_object.font_size - 3}px; color: gray;"> {message_time}</span>')
            if not is_insert:
                self.layout.addWidget(title_label)
                self.layout.addWidget(content_label)
            else:
                self.layout.insertWidget(0, content_label)
                self.layout.insertWidget(0, title_label)
        elif message_type == "image":
            try:
                decoded_compressed_image_bytes = base64.b64decode(message_content)
                image_bytes = zlib.decompress(decoded_compressed_image_bytes)

                image_label = QPushButton(self)
                image_label.setStyleSheet("background-color: transparent; border: none;")

                self.parent.load_image_from_bytes_to_button(image_bytes, image_label)
                image_label.setMaximumWidth(int(self.width / 3))  # Adjust the maximum width as needed

                image_label.clicked.connect(lambda _, image_bytes=image_bytes: open_image_bytes(image_bytes))
                if message_sender != self.main_page_object.username:
                    if self.main_page_object.censor_data_from_strangers:
                        if message_sender not in self.main_page_object.friends_list:
                            image_label.setGraphicsEffect(QGraphicsBlurEffect(self.main_page_object.blur_effect))
                    if message_sender in self.main_page_object.blocked_list or (self.main_page_object.is_private_account and message_sender not in self.main_page_object.friends_list):
                        image_label.setGraphicsEffect(QGraphicsBlurEffect(self.main_page_object.blur_effect))
                image_label.setContextMenuPolicy(Qt.CustomContextMenu)
                image_label.customContextMenuRequested.connect(
                    lambda pos, file_bytes=image_bytes, button=image_label, type=message_type,
                           name=file_name: self.parent.show_context_menu(pos, button,
                                                                         file_bytes, type, name))
                message = ""
                title_label = self.parent.create_temp_message_label(message)
                title_label.setText(
                    f'<span style="font-size: {self.main_page_object.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                    f'<span style="font-size: {self.main_page_object.font_size - 3}px; color: gray;"> {message_time}</span>')

                if not is_insert:
                    self.layout.addWidget(title_label)
                    self.layout.addWidget(image_label)
                else:
                    self.layout.insertWidget(0, image_label)
                    self.layout.insertWidget(0, title_label)
            except Exception as e:
                print(f"error in show messages is:{e}")
        elif message_type == "video":
            try:
                decoded_compressed_video_bytes = base64.b64decode(message_content)
                video_bytes = zlib.decompress(decoded_compressed_video_bytes)

                video_label = QPushButton(self)
                video_label.setStyleSheet("background-color: transparent; border: none;")
                first_video_frame_bytes = extract_first_frame(video_bytes)
                self.parent.load_image_from_bytes_to_button(first_video_frame_bytes, video_label)
                video_label.setMaximumWidth(int(self.width / 3))  # Adjust the maximum width as needed
                if message_sender != self.main_page_object.username:
                    if self.main_page_object.censor_data_from_strangers:
                        if message_sender not in self.main_page_object.friends_list:
                            video_label.setGraphicsEffect(QGraphicsBlurEffect(self.main_page_object.blur_effect))
                    if message_sender in self.main_page_object.blocked_list or (self.main_page_object.is_private_account and message_sender not in self.main_page_object.friends_list):
                        video_label.setGraphicsEffect(QGraphicsBlurEffect(self.main_page_object.blur_effect))

                video_label.clicked.connect(
                    lambda _, video_bytes=video_bytes: self.parent.parent.start_watching_video(video_bytes))

                play_button = QPushButton(video_label)
                play_button_icon_path = "discord_app_assets/play_video_icon.png"
                play_button_size = (int(self.parent.screen_height * 0.0463), int(self.parent.screen_height * 0.0463))
                play_button.clicked.connect(
                    lambda _, video_bytes=video_bytes: self.parent.parent.start_watching_video(video_bytes))
                set_button_icon(play_button, play_button_icon_path, play_button_size[0], play_button_size[1])
                make_q_object_clear(play_button)
                layout = QHBoxLayout(video_label)
                layout.addWidget(play_button)  # Add the play button to the layout

                # Set the alignment and margins explicitly
                layout.setAlignment(Qt.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)  # Ensure no spacing between widgets

                # Set the layout to the audio label
                video_label.setLayout(layout)
                video_label.setContextMenuPolicy(Qt.CustomContextMenu)
                video_label.customContextMenuRequested.connect(
                    lambda pos, file_bytes=video_bytes, button=video_label, type=message_type,
                           name=file_name: self.parent.show_context_menu(pos, button,
                                                                         file_bytes, type, name))

                message = ""
                title_label = self.parent.create_temp_message_label(message)
                title_label.setText(
                    f'<span style="font-size: {self.main_page_object.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                    f'<span style="font-size: {self.main_page_object.font_size - 3}px; color: gray;"> {message_time}</span>')
                if not is_insert:
                    self.layout.addWidget(title_label)
                    self.layout.addWidget(video_label)
                else:
                    self.layout.insertWidget(0, video_label)
                    self.layout.insertWidget(0, title_label)
            except Exception as e:
                print(f"error in show messages is:{e}")
        elif message_type == "audio":
            try:
                decoded_compressed_audio_bytes = base64.b64decode(message_content)
                audio_bytes = zlib.decompress(decoded_compressed_audio_bytes)

                audio_label = QPushButton(f"{file_name}", self)
                audio_label.setStyleSheet(
                    f"background-color: {self.main_page_object.standard_hover_color}; border: none; color: white; font-size: {self.main_page_object.font_size}px; padding-left: 10%; margin: 0;")
                audio_label.setFixedHeight(int(self.parent.screen_height * 0.02777777777))
                play_button = QPushButton(audio_label)
                play_button_icon_path = "discord_app_assets/play_video_icon.png"
                play_button_size = (int(self.parent.screen_height * 0.02314814814), int(self.parent.screen_height * 0.02314814814))
                set_button_icon(play_button, play_button_icon_path, play_button_size[0], play_button_size[1])
                play_button.clicked.connect(
                    lambda _, audio_bytes=audio_bytes: play_mp3_from_bytes(audio_bytes,
                                                                           self.parent.parent.mp3_message_media_player))
                layout = QHBoxLayout(audio_label)
                layout.addWidget(play_button)  # Add the play button to the layout

                # Set the alignment and margins explicitly
                layout.setAlignment(Qt.AlignLeft)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)  # Ensure no spacing between widgets

                # Set the layout to the audio label
                audio_label.setLayout(layout)
                # audio_label.setGeometry(x_pos, y, 300, 40)
                make_q_object_clear(play_button)
                audio_label.setContextMenuPolicy(Qt.CustomContextMenu)
                audio_label.customContextMenuRequested.connect(
                    lambda pos, file_bytes=audio_bytes, button=audio_label, type=message_type,
                           name=file_name: self.parent.show_context_menu(pos, button,
                                                                         file_bytes, type, name))

                message = ""
                title_label = self.parent.create_temp_message_label(message)
                title_label.setText(
                    f'<span style="font-size: {self.main_page_object.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                    f'<span style="font-size: {self.main_page_object.font_size - 3}px; color: gray;"> {message_time}</span>')

                if not is_insert:
                    self.layout.addWidget(title_label)
                    self.layout.addWidget(audio_label)
                else:
                    self.layout.insertWidget(0, audio_label)
                    self.layout.insertWidget(0, title_label)
            except Exception as e:
                print("error in audio file")
        elif message_type in basic_files_types:
            try:
                decoded_compressed_file_bytes = base64.b64decode(message_content)
                file_bytes = zlib.decompress(decoded_compressed_file_bytes)

                link_label = QPushButton(f"{file_name}", self)
                link_label.setStyleSheet(
                    f"background-color: {self.main_page_object.standard_hover_color}; border: none; color: white; font-size: {self.main_page_object.font_size}px; padding-left: 50%;")
                if message_type == "txt":
                    link_label.clicked.connect(lambda _, file_bytes=file_bytes: open_text_file_from_bytes(file_bytes))
                elif message_type == "pptx":
                    link_label.clicked.connect(
                        lambda _, file_bytes=file_bytes: open_pptx_from_bytes(file_bytes))
                elif message_type == "py":
                    link_label.clicked.connect(
                        lambda _, file_bytes=file_bytes: open_py_from_bytes(file_bytes))
                elif message_type == "docx":
                    link_label.clicked.connect(
                        lambda _, file_bytes=file_bytes: open_docx_from_bytes(file_bytes))
                elif message_type == "xlsx":
                    link_label.clicked.connect(
                        lambda _, file_bytes=file_bytes: open_xlsx_from_bytes(file_bytes))
                elif message_type == "pdf":
                    link_label.clicked.connect(
                        lambda _, file_bytes=file_bytes: open_pdf_from_bytes(file_bytes))
                link_label.setContextMenuPolicy(Qt.CustomContextMenu)
                link_label.customContextMenuRequested.connect(
                    lambda pos, file_bytes=file_bytes, button=link_label, type=message_type,
                           name=file_name: self.parent.show_context_menu(pos, button,
                                                                         file_bytes, type, name))
                link_label.setFixedHeight(30)

                # link_label.setGeometry(x_pos, y, 300, 40)
                message = ""
                title_label = self.parent.create_temp_message_label(message)
                title_label.setText(
                    f'<span style="font-size: {self.main_page_object.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                    f'<span style="font-size: {self.main_page_object.font_size - 3}px; color: gray;"> {message_time}</span>')

                if not is_insert:
                    self.layout.addWidget(title_label)
                    self.layout.addWidget(link_label)
                else:
                    self.layout.insertWidget(0, link_label)
                    self.layout.insertWidget(0, title_label)
            except Exception as e:
                print(f"error in show messages is:{e}")

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def update_messages_layout(self):
        self.initUI()

    def scroll_to_index(self, index):
        # Get the vertical scroll bar of the scroll area
        scroll_bar = self.scroll_area.verticalScrollBar()

        # Set the scroll bar value to scroll to the specified index
        scroll_bar.setValue(index)

    def scroll_up_by_n_widgets(self, n):
        total_height = 0
        for i in range(min(n * 2, self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                total_height += widget.sizeHint().height() + self.space_between_widgets
        print(f"total height is {total_height}")
        self.scroll_area.verticalScrollBar().setValue(total_height)
        self.scroll_value_changed(self.scroll_area.verticalScrollBar().value())

    def scroll_value_changed(self, value):
        # I don't want to ask for more message when I just load the messages in
        if value == 0 and not self.parent.parent.is_new_chat_clicked:
            if len(self.main_page_object.list_messages) >= 15:
                self.main_page_object.Network.ask_for_more_messages()
                print("asked for more messages")

        self.main_page_object.chat_start_index = value


class CreateGroupBox(QWidget):
    def __init__(self, parent, x, y, box_format):
        super().__init__()
        self.parent = parent
        try:
            self.x = x
            self.y = y
            self.box_format = box_format
            self.create_group_open_x = self.parent.create_group_open_x
            self.create_group_open_y = self.parent.create_group_open_y
            self.selected_group_members = self.parent.parent.selected_group_members
            self.group_max_members = self.parent.parent.group_max_members
            self.friends_list = self.parent.parent.friends_list
            self.standard_hover_color = self.parent.parent.standard_hover_color
            self.create_group_index = self.parent.parent.create_group_index
        except Exception as e:
            print(f"error in initiating create group box {e}")
        self.init_ui()

    def init_ui(self):
        try:
            if self.box_format == "create":
                submit_button_text = "Create DM"
            else:
                submit_button_text = "ADD"
            starter_x = self.x
            starter_y_of_border = self.y + int(self.parent.screen_height * 0.0463)
            adding_border_height = int(self.parent.screen_height * 0.37037)
            adding_border_width = int(self.parent.screen_width * 0.15625)

            border_of_adding = QLabel(self.parent)
            border_of_adding.setGeometry(starter_x, starter_y_of_border, adding_border_width, adding_border_height)
            border_of_adding.raise_()
            border_of_adding.setStyleSheet("""border: 2px solid black;  
            /* Use a slightly darker shade for the border */
                            border-radius: 5px;""")

            label = QLabel(f"Select friends", self.parent)
            label.setStyleSheet("""color: white;font-size: 20px;""")
            label.move(starter_x + int(self.parent.screen_width * 0.0104), starter_y_of_border + int(self.parent.screen_height * 0.00925925925))
            Page = 0
            if len(self.friends_list) > 0:
                Page = self.create_group_index + 1

            if self.parent.parent.is_create_group_inside_chat_pressed:
                if self.parent.current_group_id:
                    number_of_group_members = self.parent.parent.get_number_of_members_by_group_id(
                        self.parent.current_group_id)
                    page_plus_selected_label_text = f"You can add {self.group_max_members - number_of_group_members - len(self.selected_group_members)} more friends"
                    page_plus_selected_text = f"Page({Page}/{calculate_division_value(len(self.friends_list))}) Selected({len(self.selected_group_members)})"
                else:
                    page_plus_selected_label_text = f"You can add {(self.group_max_members - 2) - len(self.selected_group_members)} more friends"
                    page_plus_selected_text = f"Page({Page}/{calculate_division_value(len(self.friends_list))}) Selected({len(self.selected_group_members)})"
            else:
                page_plus_selected_label_text = f"You can add {(self.group_max_members - 1) - len(self.selected_group_members)} more friends"
                page_plus_selected_text = f"Page({Page}/{calculate_division_value(len(self.friends_list))}) Selected({len(self.selected_group_members)})"
            self.page_plus_selected_label = QLabel(page_plus_selected_label_text, self.parent)
            self.page_plus_selected_label.setStyleSheet("""color: white;font-size: 14px;""")
            self.page_plus_selected_label.move(starter_x + int(self.parent.screen_width * 0.0104), starter_y_of_border + int(self.parent.screen_height * 0.04166666666))

            self.amount_of_people_to_add_text_label = QLabel(page_plus_selected_text, self.parent)
            self.amount_of_people_to_add_text_label.setStyleSheet("""color: white;font-size: 12px;""")
            self.amount_of_people_to_add_text_label.move(starter_x + int(self.parent.screen_width * 0.02083333333), starter_y_of_border + int(self.parent.screen_height * 0.06944444444))

            style_sheet = f"""
            QPushButton {{
                color: white;
                font-size: 16px;
                background-color: rgba(0, 0, 0, 0); /* Transparent background */
                border: 2px solid {self.standard_hover_color}; /* Use a slightly darker shade for the border */
                border-radius: 5px;
                }}
                            QPushButton:hover {{
                    background-color: #2980b9;
                }}
            """
            scroll_up_button = QPushButton("↑", self.parent)
            scroll_up_button.move(starter_x + int(self.parent.screen_width * 0.12), starter_y_of_border + int(self.parent.screen_height * 0.02314814814))
            scroll_up_button.setFixedWidth(int(self.parent.screen_width * 0.02604))
            scroll_up_button.setStyleSheet(style_sheet)
            scroll_up_button.clicked.connect(partial(self.parent.handle_create_group_index, "up"))

            scroll_down_button = QPushButton("↓", self.parent)
            scroll_down_button.move(starter_x + int(self.parent.screen_width * 0.12), starter_y_of_border + int(self.parent.screen_height * 0.05092592592))
            scroll_down_button.setFixedWidth(int(self.parent.screen_width * 0.02604))
            scroll_down_button.setStyleSheet(style_sheet)
            scroll_down_button.clicked.connect(partial(self.parent.handle_create_group_index, "down"))

            starter_x = self.x
            starter_y = self.y + int(self.parent.screen_height * 0.13888888888)
            i = 0
            for friend in self.friends_list:
                if self.create_group_index * 5 <= i < (self.create_group_index + 1) * 5:
                    friend_label = QPushButton(friend, self.parent)
                    friend_label.friend_name = friend
                    friend_label.setStyleSheet(f'''
                        QPushButton {{
                            color: white;
                            font-size: 18px;
                            border: 2px solid {self.standard_hover_color};
                            border-radius: 5px;
                            padding: 5px;
                            margin-bottom: 18px;
                            text-align: left; /* Align text to the left */
                        }}

                        QPushButton:hover {{
                            background-color: #3498db; /* Bluish hover color */
                        }}
                    ''')
                    friend_checkbox = QCheckBox(self.parent)
                    if self.parent.parent.is_create_group_inside_chat_pressed:
                        if self.parent.current_group_id:
                            group_members = self.parent.parent.get_group_members_by_group_id(
                                self.parent.current_group_id)
                            if friend in group_members:
                                friend_checkbox.setChecked(True)
                            else:
                                friend_label.clicked.connect(partial(self.parent.toggle_checkbox, self))
                        else:
                            if self.parent.parent.selected_chat == friend:
                                friend_checkbox.setChecked(True)
                            else:
                                friend_label.clicked.connect(partial(self.parent.toggle_checkbox, self))
                    else:
                        friend_label.clicked.connect(partial(self.parent.toggle_checkbox, self))
                    if friend in self.selected_group_members:
                        friend_checkbox.setChecked(True)
                    friend_checkbox.friend_name = friend  # Store friend's name as an attribute
                    friend_checkbox.stateChanged.connect(self.parent.friend_checkbox_changed)
                    height = friend_label.height() + int(self.parent.screen_height * 0.02777777777)
                    friend_label.setGeometry(starter_x + int(self.parent.screen_width * 0.00520833333), starter_y, adding_border_width - int(self.parent.screen_width * 0.0104), height)
                    friend_checkbox.move(starter_x + int(self.parent.screen_width * 0.13541666666), starter_y + int(self.parent.screen_height * 0.01388))
                    starter_y += friend_label.height() - int(self.parent.screen_height * 0.01851851851)
                    friend_label.raise_()
                    friend_checkbox.raise_()
                i += 1

            button = QPushButton(submit_button_text, self.parent)
            button.move(starter_x + int(self.parent.screen_height * 0.01388), starter_y_of_border + adding_border_height - int(self.parent.screen_height * 0.07407407407))
            button.setFixedHeight(self.parent.friends_button_height)
            if self.box_format == "create":
                button.clicked.connect(self.parent.create_dm_pressed)
            else:
                button.clicked.connect(self.parent.add_users_to_group)

            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.parent.parent.background_color_hex};
                    border: 2px solid {self.parent.parent.standard_hover_color};
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
            button.setFixedWidth(adding_border_width - int(self.parent.screen_width * 0.015625))
        except Exception as e:
            print(f"error in creating group box {e}")

    def update_labels_text(self):
        Page = 0
        if len(self.friends_list) > 0:
            Page = self.create_group_index + 1
        if self.parent.parent.is_create_group_inside_chat_pressed:
            if self.parent.current_group_id:
                number_of_group_members = self.parent.parent.get_number_of_members_by_group_id(
                    self.parent.current_group_id)
                page_plus_selected_label_text = f"You can add {self.group_max_members - number_of_group_members - len(self.selected_group_members)} more friends"
                page_plus_selected_text = f"Page({Page}/{calculate_division_value(len(self.friends_list))}) Selected({len(self.selected_group_members)})"
            else:
                page_plus_selected_label_text = f"You can add {(self.group_max_members - 2) - len(self.selected_group_members)} more friends"
                page_plus_selected_text = f"Page({Page}/{calculate_division_value(len(self.friends_list))}) Selected({len(self.selected_group_members)})"
        else:
            page_plus_selected_label_text = f"You can add {(self.group_max_members - 1) - len(self.selected_group_members)} more friends"
            page_plus_selected_text = f"Page({Page}/{calculate_division_value(len(self.friends_list))}) Selected({len(self.selected_group_members)})"
        self.page_plus_selected_label.setText(page_plus_selected_label_text)
        self.amount_of_people_to_add_text_label.setText(page_plus_selected_text)


class FriendsChatListWidget(QWidget):
    def __init__(self, chat_box_object, chats_list):
        super().__init__()
        self.setParent(chat_box_object)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.chat_box_object = chat_box_object
        self.friends_button_height = int(self.chat_box_object.screen_height * 0.0463)
        self.draw_friends_buttons(chats_list)
        self.adjustSize()

    def draw_friends_buttons(self, friend_list):
        friend_starter_y = 0
        friend_x = 0
        if friend_list is not None:
            for friend in friend_list:
                try:
                    button = self.chat_box_object.create_friend_button(friend, (friend_x, friend_starter_y), self)
                    button.move(friend_x, friend_starter_y)  # Use move to set the position within the container widget
                    friend_starter_y += self.chat_box_object.friends_button_height
                    self.layout.addWidget(button)
                except Exception as e:
                    print(f"Error in drawing friends button: {e}")

    def update_parent(self, new_parent):
        self.setParent(new_parent)


class ScrollAreaWidget(QWidget):
    def __init__(self, parent, x, y, width, height, items_list, is_vertical, variable_to_change=None):
        try:
            super().__init__(parent)

            # Create the internal scroll area widget
            self.setGeometry(x, y, width, height)
            self.variable_to_change = variable_to_change
            self.parent = parent
            self.scroll_area = QScrollArea(self.parent)
            if not is_vertical:
                self.scroll_area.setStyleSheet("""
                    QScrollArea {
                        border: transparent;
                    }
                    QScrollBar:vertical {
                        border: transparent;
                    }
                    QScrollBar:horizontal {
                        border: transparent;
                    }
                """)
            else:
                self.scroll_area.setStyleSheet(f"""
                     QScrollArea {{
                         border: 2px solid {self.parent.parent.standard_hover_color};
                    }}
                     QScrollBar:vertical {{
                         border: 2px solid {self.parent.parent.standard_hover_color};
                    }}
                 QScrollBar:horizontal {{
                        border: 2px solid {self.parent.parent.standard_hover_color};
                    }}
                 """)
            self.scroll_area.setGeometry(x, y, width, height)

            self.scroll_area.setWidgetResizable(True)

            self.scroll_area_widget_contents = QWidget()
            self.scroll_area_widget_contents.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            # Set the layout for this widget
            self.layout = QVBoxLayout(self.scroll_area_widget_contents) if is_vertical else QHBoxLayout(self.scroll_area_widget_contents)
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.layout.setSpacing(0)
            if is_vertical:
                self.layout.setAlignment(Qt.AlignTop)
            else:
                self.layout.setAlignment(Qt.AlignLeft)

            for item in items_list:
                self.layout.addWidget(item)
            self.scroll_area.setWidget(self.scroll_area_widget_contents)
            self.scroll_area.verticalScrollBar().valueChanged.connect(self.scroll_value_changed)
            if self.variable_to_change == "chat_index":
                if self.parent.parent.chat_index is not None:
                    try:
                        self.scroll_area.verticalScrollBar().setValue(self.parent.parent.chat_index)
                    except Exception as e:
                        pass
            elif self.variable_to_change == "friends_box_index":
                if self.parent.parent.friends_box_index is not None:
                    try:
                        self.scroll_area.verticalScrollBar().setValue(self.parent.parent.friends_box_index)
                    except Exception as e:
                        pass
        except Exception as e:
            print(f"error in scrollable widget {e}")
            print(items_list)

    def scroll_value_changed(self, value):
        if self.variable_to_change is not None:
            if self.variable_to_change == "chat_index":
                self.parent.change_chat_index(value)
            elif self.variable_to_change == "friends_box_index":
                self.parent.parent.friends_box_index = value


class CallIconsWidget(QWidget):
    def __init__(self, parent, current_group_id=None):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.main_page_object = self.parent.parent
        self.current_group_id = current_group_id
        self.put_call_icons_on_the_screen()

    def put_call_icons_on_the_screen(self):
        try:
            if self.current_group_id:
                current_call_dict = self.main_page_object.get_call_dict_by_group_id(self.current_group_id)
            else:
                current_call_dict = self.main_page_object.get_call_dict_by_user(self.main_page_object.username)
            starts_x = 0
            y_of_profiles = 35

            if current_call_dict is not None:
                names = current_call_dict.get("participants")
                if self.main_page_object.username in names:
                    for name in names:
                        is_cam_on = False

                        # Create a vertical layout for each participant
                        participant_layout = QVBoxLayout()

                        if name in current_call_dict.get("screen_streamers") and name != self.main_page_object.username:
                            stream_type = "ScreenStream"
                            stream_button1 = self.parent.create_watch_stream_button(starts_x + 10, y_of_profiles - 35,
                                                                                    name, stream_type, self)
                            participant_layout.addWidget(stream_button1)
                            is_cam_on = True

                        if name in current_call_dict.get("camera_streamers") and name != self.main_page_object.username:
                            stream_type = "CameraStream"
                            stream_button2 = self.parent.create_watch_stream_button(starts_x + 10, y_of_profiles - 35,
                                                                                    name, stream_type, self)
                            participant_layout.addWidget(stream_button2)
                            is_cam_on = True

                        profile_button = self.parent.create_profile_button(starts_x, y_of_profiles, name,
                                                                           current_call_dict, self)
                        participant_layout.addWidget(profile_button)

                        # Add the participant layout to the main layout
                        self.layout.addLayout(participant_layout)
                        self.layout.addSpacing(10)  # Adjust the value to set the desired spacing

                        starts_x += 105
        except Exception as e:
            print(f"error is {e} in icon management")

