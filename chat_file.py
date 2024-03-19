from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QColor
from PyQt5.QtCore import pyqtSignal
from functools import partial
from discord_comms_protocol import client_net
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit
from PyQt5.QtCore import Qt, QSize, QPoint, QCoreApplication, QTimer, QMetaObject, Q_ARG, QObject, pyqtSignal,  QSettings, QUrl, Qt, QUrl, QTime, QBuffer, QIODevice, QTemporaryFile
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter, QPainterPath
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PIL import Image
from io import BytesIO
import base64
import binascii
import zlib
import pygetwindow
import numpy as np
from PIL import Image, ImageDraw
import webbrowser
import io
import tempfile
import os
import math
import subprocess
import platform
import random
import string


def generate_random_filename(extension):
    # Generate a random string of characters
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"file_{random_string}.{extension}"


def download_file_from_bytes(file_bytes, file_extension, file_name):
    try:
        # Get the path to the user's downloads directory
        if platform.system() == 'Windows':
            downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        elif platform.system() == 'Darwin':
            downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        else:
            downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')


        # Generate a random file name with the same extension
        if not file_name:
            file_name = generate_random_filename(file_extension)


        # Prompt the user to choose a file name and location
        #file_path, _ = QFileDialog.getSaveFileName(None, "Save File", os.path.join(downloads_dir, file_name))
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
        media_player.stop()
        temp_file_path = save_bytes_to_temp_file(mp3_bytes, 'mp3')

        # Create QMediaContent object with the URL pointing to the temporary file
        media_content = QMediaContent(QUrl.fromLocalFile(temp_file_path))

        # Create QMediaPlayer instance and set the media content
        media_player.setMedia(media_content)

        # Play the media
        media_player.play()
    except Exception as e:
        print(f"Error playing MP3: {e}")


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


def save_bytes_to_temp_file(file_bytes, extension):
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
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            # Write the bytes to the temporary file
            temp_file.write(file_bytes)
            temp_file.flush()

            # Get the path to the temporary file
            file_path = temp_file.name

            # Open the temporary file using Notepad asynchronously
            subprocess.Popen(['notepad', file_path])

            # On macOS, you might use: subprocess.Popen(['open', file_path])
    except Exception as e:
        print(f"Error opening text file: {e}")


def create_link_label(text, click_function, parent=None):
    label = QLabel(text, parent)
    label.setTextInteractionFlags(Qt.TextBrowserInteraction)
    label.setOpenExternalLinks(False)  # Disable external links to capture linkActivated signal
    label.setStyleSheet("color: blue; font-size: 12px;")
    label.linkActivated.connect(click_function)
    return label


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
        temp_video_path = tempfile.NamedTemporaryFile(delete=False)
        temp_video_path.write(video_bytes)
        temp_video_path.close()

        # Open the temporary video file
        cap = cv2.VideoCapture(temp_video_path.name)

        # Read the first frame
        ret, frame = cap.read()

        # Release the video capture object and delete the temporary file
        cap.release()
        cv2.destroyAllWindows()
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
    """Opens an image from bytes using the default image viewer application.

    Args:
        image_bytes (bytes): The image data as bytes.

    Returns:
        bool: True if the image was opened successfully, False otherwise.
    """
    try:
        # Create a temporary file to save the image bytes
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(image_bytes)

            # Get the path of the temporary file
            temp_file_path = temp_file.name

        # Open the temporary file using the default image viewer application
        webbrowser.open(temp_file_path)

        return True

    except Exception as e:
        print(f"Error opening image: {e}")
        return False


def calculate_image_size_in_kb(image_bytes):
    try:
        # Create a BytesIO object from the image bytes
        image_stream = io.BytesIO(image_bytes)

        # Open the image using PIL
        with Image.open(image_stream) as img:
            # Get the size of the image in bytes
            image_size_bytes = img.tell()

            # Convert bytes to kilobytes
            image_size_kb = image_size_bytes / 1024

            return image_size_kb

    except Exception as e:
        print(f"Error: {e}")
        return None


def calculate_image_size_in_mb(image_bytes):
    try:
        # Create a BytesIO object from the image bytes
        image_stream = io.BytesIO(image_bytes)

        # Open the image using PIL
        with Image.open(image_stream) as img:
            # Get the size of the image in bytes
            image_size_bytes = img.tell()

            # Convert bytes to kilobytes
            image_size_kb = image_size_bytes / (1024 * 1000)

            return image_size_kb

    except Exception as e:
        print(f"Error: {e}")
        return None


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
        self.file_name = ""
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

        self.draw_message_start_x = int(self.screen_width * 0.323)

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


        self.square_pos = (600, 0)
        self.square_label.setGeometry(self.square_pos[0], self.square_pos[1], self.width_of_chat_box,
                                      self.height_of_chat_box)
        self.square_label.setStyleSheet(f"background-color: {self.parent.background_color_hex}; border: 5px solid {self.parent.standard_hover_color};")

        around_name_y = self.square_pos[1]
        around_name_x = self.square_pos[0]
        self.around_name = QLabel(self)
        self.around_name.setStyleSheet(f"background-color: {self.parent.background_color_hex}; border: 5px solid {self.parent.standard_hover_color};")
        start_height_of_around_name = 50
        height_of_around_name = start_height_of_around_name
        self.around_name_delta = 220
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
            temp_widget_x, temp_widget_y = (600, height_of_around_name)
            temp_widget_width = self.width_of_chat_box
            if height_of_around_name != start_height_of_around_name:
                temp_widget_height = self.height_of_chat_box - 130 - self.around_name_delta
            else:
                temp_widget_height = self.height_of_chat_box - 130

            if self.parent.is_messages_need_update:
                temp_widget = ScrollableWidget(self, temp_widget_width, temp_widget_height, temp_widget_x, temp_widget_y)
                self.parent.messages_content_saver = temp_widget
                self.parent.is_messages_need_update = False
            else:
                temp_widget = self.parent.messages_content_saver.update_scroll_area_parent(self)
                self.parent.messages_content_saver = temp_widget

            self.around_name.raise_()
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
            self.add_user_x = call_button_x - 50
            self.add_user_y = call_button_y
            self.add_user_button = self.create_top_page_button(self.add_user_x, self.add_user_y, icon)
            self.add_user_button.clicked.connect(self.add_user_to_group_pressed)

            if self.current_group_id:
                group_manager = self.parent.get_group_manager_by_group_id(self.current_group_id)
                if group_manager == self.parent.username:
                    icon = QIcon("discord_app_assets/edit_name.png")
                    rename_group_x = self.add_user_x - 50
                    rename_group_y = call_button_y
                    self.rename_group = self.create_top_page_button(rename_group_x, rename_group_y, icon)
                    icon = QIcon("discord_app_assets/edit_image_icon.png")
                    edit_group_image_x = rename_group_x - 50
                    edit_group_image_y = rename_group_y
                    self.edit_group_image_button = self.create_top_page_button(edit_group_image_x, edit_group_image_y,
                                                                               icon)
                    self.edit_group_image_button.clicked.connect(self.change_group_image)

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
            if self.parent.background_color == "Black and White":
                text_entry_color = "black"
            else:
                text_entry_color = "white"
            text_entry_y = self.send_image_y-5
            self.text_entry.setGeometry(650, text_entry_y, self.width_of_chat_box-70, 40)
            self.text_entry.setStyleSheet(f"background-color: {self.parent.standard_hover_color}; color: {text_entry_color}; padding: 10px; border: 1px solid #2980b9; border-radius: 5px; font-size: 14px;")
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
        file_name_y = 860
        file_name_x = 620
        file_name_width = 300
        self.filename_label.setGeometry(file_name_x, file_name_y, file_name_width, 50)  # Adjust the size as needed
        self.filename_label.setWordWrap(True)  # Enable word wrap
        self.filename_label.raise_()
        self.filename_label.setStyleSheet(
            "background-color: #333333; color: white; font-size: 16px;"
        )
        self.filename_label.hide()
        self.garbage_button = QPushButton(self)
        garbage_icon_path = "discord_app_assets/garbage_icon.png"
        garbage_icon_width, garbage_icon_height = (35, 35)
        set_button_icon(self.garbage_button, garbage_icon_path, garbage_icon_width, garbage_icon_height)
        self.garbage_button.setGeometry(file_name_x + file_name_width - 50, file_name_y+8, garbage_icon_width, garbage_icon_height)
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

        #self.show_messages_on_screen(self.messages_list)

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
        self.border_label2.setGeometry(friend_x, 0, border_width, 170)
        self.border_label2.lower()

        find_contact_pos = (260, 20)
        find_contact_size = (320, 40)
        self.find_contact_text_entry = QLineEdit(self)
        if self.parent.background_color == "Black and White":
            text_entry_color = "black"
        else:
            text_entry_color = "white"
        self.find_contact_text_entry.setPlaceholderText("Find a conversation")
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
        self.friends_button.setGeometry(friend_x + 5, friends_button_y - 10, border_width - 15,
                                        friends_button_height)  # Adjust size as needed

        # Set the text alignment to show both the icon and text

        # Optional: Adjust the spacing between the icon and text
        self.friends_button.setIconSize(QSize(50, 50))  # Adjust size as needed
        self.friends_button.clicked.connect(self.parent.Social_clicked)

        try:
            friend_starter_y = 170
            friend_x = 250
            if not self.parent.current_chat_box_search:
                self.drew_friends_buttons_on_screen_by_list(self.parent.chats_list)
                #chats_widget = ScrollableChats(self, 350, 900, friend_x, friend_starter_y, self.parent.chats_list)
            else:

                self.drew_friends_buttons_on_screen_by_list(self.parent.temp_search_list)
                #chats_widget = ScrollableChats(self, 350, 900, friend_x, friend_starter_y, self.parent.temp_search_list)
        except Exception as e:
            print(f"error in showing chats list{e}")

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

        ''')
        settings_button.clicked.connect(self.parent.Settings_clicked)

        if self.parent.is_create_group_pressed:
           create_group_box = CreateGroupBox(self, self.create_group_open_x, self.create_group_open_y, "create")
           create_group_box.raise_()
        elif self.parent.is_create_group_inside_chat_pressed:
            if self.parent.is_current_chat_a_group:
                create_group_box = CreateGroupBox(self, self.add_user_x, self.add_user_y, "add")
            else:
                create_group_box = CreateGroupBox(self, self.add_user_x, self.add_user_y, "create")
            create_group_box.raise_()
            #self.display_create_group_box()
        #chats_widget.raise_()
        self.raise_needed_elements()

    def add_user_to_group_pressed(self):
        if self.parent.is_create_group_inside_chat_pressed:
            self.parent.is_create_group_inside_chat_pressed = False
            self.parent.updated_chat()
        else:
            self.parent.is_create_group_pressed = False
            self.parent.is_create_group_inside_chat_pressed = True
            self.parent.updated_chat()

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
        width, height = (90, 90)
        button = create_custom_circular_label(width, height, self)

        status_button = QPushButton(self)
        make_q_object_clear(status_button)
        width, height = (30, 30)
        button_size = QSize(width, height)
        status_button.setFixedSize(button_size)

        button.move(x, y)

        regular_icon_path = r"discord_app_assets/regular_profile.png"
        muted_icon = QIcon("discord_app_assets/mic_muted_icon.png")
        deafened_icon = QIcon("discord_app_assets/deafened.png")
        regular_icon = QIcon(regular_icon_path)
        deafened = dict.get("deafened")
        muted = dict.get("muted")

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
                set_icon_from_bytes_to_label(button, profile_pic)
        except Exception as e:
            print(f"error in setting image to profile button {e}")
        status_button.move(x + int(0.7 * button.width()), y + int(0.7 * button.height()))
        self.call_profiles_list.append(button)
        self.call_profiles_list.append(status_button)
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

        style_sheet = f"""
        QPushButton {{
            color: white;
            font-size: 16px;
            background-color: rgba(0, 0, 0, 0); /* Transparent background */
            border: 2px solid {self.parent.standard_hover_color}; /* Use a slightly darker shade for the border */
            border-radius: 5px;
            }}
                        QPushButton:hover {{
                background-color: #2980b9;
            }}
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
                background-color: {self.parent.background_color_hex};
                border: 2px solid {self.parent.standard_hover_color};
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

        style_sheet = f"""
        QPushButton {{
            color: white;
            font-size: 16px;
            background-color: rgba(0, 0, 0, 0); /* Transparent background */
            border: 2px solid {self.parent.standard_hover_color}; /* Use a slightly darker shade for the border */
            border-radius: 5px;
            }}
                        QPushButton:hover {{
                background-color: #2980b9;
            }}
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
                friend_label.setStyleSheet(f'''
                    QPushButton {{
                        color: white;
                        font-size: 18px;
                        border: 2px solid {self.parent.standard_hover_color};
                        border-radius: 5px;
                        padding: 5px;
                        margin-bottom: 18px;
                        text-align: left; /* Align text to the left */
                    }}

                    QPushButton:hover {{
                        background-color: #3498db; /* Bluish hover color */
                    }}
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
                background-color: {self.parent.background_color_hex};
                border: 2px solid {self.parent.standard_hover_color};
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
        if len(self.parent.selected_group_members) != 0:
            self.Network.create_group(self.parent.selected_group_members)
            print("You a created new group")
            self.parent.is_create_group_pressed = False
            self.parent.is_create_group_inside_chat_pressed = False
            self.parent.selected_group_members.clear()
            self.parent.create_group_index = 0
            self.parent.updated_chat()

    def add_users_to_group(self):
        group_id = self.current_group_id
        if len(self.parent.selected_group_members) != 0:
            self.Network.add_user_to_group(group_id, self.parent.selected_group_members)
            print(f"Added user {self.parent.selected_group_members} to group of id {group_id}")
            self.parent.is_create_group_pressed = False
            self.parent.is_create_group_inside_chat_pressed = False
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
            print(f"friend_checkbox_changed error :{e}")
        #self.parent.updated_chat()

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

    def create_friend_button(self, label, parent, style_sheet, position):

        px_padding_of_button_text = 55
        chat_name = label
        text, id = gets_group_attributes_from_format(chat_name)
        if id:
            len_group = self.parent.get_number_of_members_by_group_id(id)
        button_text = text

        width, height = (35, 35)
        profile_image_label = create_custom_circular_label(width, height, self)
        profile_image_x, profile_image_y = (position[0] + (px_padding_of_button_text * 0.25), position[1] + ((self.friends_button_height - height) * 0.5))

        if id:
            chat_image = self.parent.get_circular_image_bytes_by_group_id(id)
        else:
            chat_image = self.parent.get_profile_pic_by_username(chat_name)
            #chat_image = self.parent.get_circular_image_bytes_by_name(chat_name)
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

        return button

    def raise_around_name_label(self):
        self.around_name.raise_()

    def open_file_dialog_for_changing_group_image(self):
        if self.file_dialog.exec_():
            selected_files = self.file_dialog.selectedFiles()
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
                    self.parent.updated_chat()
                    self.parent.activateWindow()
                else:
                    print("couldn't load image")
            elif selected_files and file_types[0] in ["mp4", "mov"]:
                video_bytes = file_to_bytes(selected_files[0])
                self.parent.file_to_send = video_bytes
                self.filename_label.setText(self.parent.file_name + " is loaded")
                self.filename_label.show()
                self.parent.updated_chat()
                self.parent.activateWindow()
            elif selected_files and file_types[0] in ["mp3"]:
                audio_bytes = file_to_bytes(selected_files[0])
                self.parent.file_to_send = audio_bytes
                self.filename_label.setText(self.parent.file_name + " is loaded")
                self.filename_label.show()
                self.parent.updated_chat()
                self.parent.activateWindow()
            elif selected_files and file_types[0] in basic_files_types:
                file_bytes = file_to_bytes(selected_files[0])
                self.parent.file_to_send = file_bytes
                self.filename_label.setText(self.parent.file_name + " is loaded")
                self.filename_label.show()
                self.parent.updated_chat()
                self.parent.activateWindow()


    def open_image_file_dialog(self):
        self.open_file_dialog()

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
            print(f"error mute_and_unmute {e}")

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
            print(f"error ringing_user {e}")

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
            print(f"error call_user {e}")

    def on_friend_button_clicked(self, label):
        try:
            self.selected_chat_changed(label)
        except Exception as e:
            print(f"error on_friend_button_clicked {e}")

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

    def show_messages_on_screen(self, list_messages):
        # can show up to 33 message in the chat
        # Delete existing message labels
        space_between_messages = self.parent.font_size + 13
        self.delete_message_labels()
        x_pos = 620
        starter = 845
        if self.filename_label.text() != "":
            starter_y_pos = starter
        else:
            starter_y_pos = starter + 50

        if (self.parent.is_calling and self.parent.selected_chat == self.parent.calling_to) or \
                (self.parent.is_in_a_call and self.parent.selected_chat == self.parent.in_call_with):
            end_y_pos = 50 + self.around_name_delta
        else:
            end_y_pos = 50
        y = starter_y_pos
        index = 0
        basic_files_types = ["xlsx", "py", "docx", "pptx", "txt", "pdf"]
        for i in list_messages:
            message_content = i.get("content")
            message_time = i.get("timestamp")
            message_sender = i.get("sender_id")
            message_type = i.get("message_type")
            file_name = i.get("file_name")
            if self.parent.chat_start_index <= index:
                if index == len(self.parent.list_messages) - 1:
                    self.parent.is_last_message_on_screen = True
                if not message_content or message_type == "string":

                    content_label = self.create_temp_message_label(message_content)
                    y -= (content_label.height()-30)
                    content_label.move(x_pos, y)
                    self.message_labels.append(content_label)

                    # second part = Name + timestamp
                    title_label = QLabel()
                    title_label = self.create_temp_message_label("")
                    title_label.setText(
                        f'<span style="font-size: {self.parent.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                        f'<span style="font-size: {self.parent.font_size - 3}px; color: gray;"> {message_time}</span>')
                    self.message_labels.append(title_label)

                    y -= title_label.height()
                    title_label.move(x_pos, y)
                    y -= title_label.height()
                    if index != len(self.parent.list_messages) - 1:
                        self.parent.is_last_message_on_screen = False
                elif message_type == "image":
                    try:
                        decoded_compressed_image_bytes = base64.b64decode(message_content)
                        image_bytes = zlib.decompress(decoded_compressed_image_bytes)

                        image_label = QPushButton(self)
                        image_label.setStyleSheet("background-color: transparent; border: none;")

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
                        y -= space_between_messages
                        message = ""
                        label = self.create_temp_message_label(message)
                        label.setText(f'<span style="font-size: {self.parent.font_size+2}px; color: white; font-weight: bold;">{message_sender}</span>'
                                      f'<span style="font-size: {self.parent.font_size-3}px; color: gray;"> {message_time}</span>')
                        label.move(x_pos, y)
                        self.message_labels.append(label)
                        y -= label.height()
                    except Exception as e:
                        print(f"error in show messages is:{e}")
                    if y < end_y_pos:
                        self.parent.is_chat_box_full = True
                        if index != self.parent.list_messages:
                            self.parent.is_last_message_on_screen = False
                elif message_type == "video":
                    try:
                        decoded_compressed_video_bytes = base64.b64decode(message_content)
                        video_bytes = zlib.decompress(decoded_compressed_video_bytes)

                        video_label = QPushButton(self)
                        video_label.setStyleSheet("background-color: transparent; border: none;")
                        first_video_frame_bytes = extract_first_frame(video_bytes)
                        self.load_image_from_bytes_to_button(first_video_frame_bytes, video_label)

                        video_label.clicked.connect(lambda _, video_bytes=video_bytes: self.parent.start_watching_video(video_bytes))
                        if y - video_label.height() - 10 < end_y_pos:
                            self.parent.is_chat_box_full = True
                            if index != len(self.parent.list_messages) - 1:
                                self.parent.is_last_message_on_screen = False
                        self.message_labels.append(video_label)
                        y -= video_label.height()
                        play_button = QPushButton(self)
                        play_button_icon_path = "discord_app_assets/play_video_icon.png"
                        play_button_size = (50, 50)
                        play_button.clicked.connect(
                            lambda _, video_bytes=video_bytes: self.parent.start_watching_video(video_bytes))
                        set_button_icon(play_button, play_button_icon_path, play_button_size[0], play_button_size[1])
                        self.message_labels.append(play_button)

                        make_q_object_clear(play_button)
                        video_label.move(x_pos, y)
                        play_button.move(x_pos + (0.5 * video_label.width() - 0.5 * play_button_size[0]), y + (0.5 * video_label.height() - 0.5 * play_button_size[1]))
                        video_label.raise_()
                        play_button.raise_()
                        y -= space_between_messages
                        message = ""
                        label = self.create_temp_message_label(message)
                        label.setText(
                            f'<span style="font-size: {self.parent.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                            f'<span style="font-size: {self.parent.font_size - 3}px; color: gray;"> {message_time}</span>')
                        label.move(x_pos, y)
                        self.message_labels.append(label)
                        y -= label.height()
                    except Exception as e:
                        print(f"error in show messages is:{e}")
                    if y < end_y_pos:
                        self.parent.is_chat_box_full = True
                        if index != self.parent.list_messages:
                            self.parent.is_last_message_on_screen = False
                elif message_type == "audio":
                    decoded_compressed_audio_bytes = base64.b64decode(message_content)
                    audio_bytes = zlib.decompress(decoded_compressed_audio_bytes)

                    audio_label = QPushButton(f"{file_name}", self)
                    audio_label.setStyleSheet(f"background-color: {self.parent.standard_hover_color}; border: none; color: white; font-size: {self.parent.font_size}px; padding-left: 50%;")



                    y -= audio_label.height()
                    play_button = QPushButton(self)
                    play_button_icon_path = "discord_app_assets/play_video_icon.png"
                    play_button_size = (25, 25)
                    set_button_icon(play_button, play_button_icon_path, play_button_size[0], play_button_size[1])
                    play_button.clicked.connect(
                        lambda _, audio_bytes=audio_bytes: play_mp3_from_bytes(audio_bytes, self.parent.mp3_message_media_player))
                    audio_label.setGeometry(x_pos, y, 300, 40)
                    make_q_object_clear(play_button)
                    play_button.move(x_pos + (0.1 * audio_label.width()),
                                     y + (0.5 * audio_label.height() - 0.5 * play_button_size[1]))

                    if y - audio_label.height() - 10 < end_y_pos:
                        self.parent.is_chat_box_full = True
                        if index != len(self.parent.list_messages) - 1:
                            self.parent.is_last_message_on_screen = False
                    self.message_labels.append(audio_label)
                    y -= space_between_messages
                    message = ""
                    label = self.create_temp_message_label(message)
                    label.setText(
                        f'<span style="font-size: {self.parent.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                        f'<span style="font-size: {self.parent.font_size - 3}px; color: gray;"> {message_time}</span>')
                    label.move(x_pos, y)
                    self.message_labels.append(label)
                    y -= label.height()
                elif message_type in basic_files_types:
                    try:
                        decoded_compressed_file_bytes = base64.b64decode(message_content)
                        file_bytes = zlib.decompress(decoded_compressed_file_bytes)

                        link_label = QPushButton(f"{file_name}", self)
                        link_label.setStyleSheet(f"background-color: {self.parent.standard_hover_color}; border: none; color: white; font-size: {self.parent.font_size}px; padding-left: 50%;")
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
                            lambda pos, file_bytes=file_bytes, button=link_label, type=message_type, name=file_name: self.show_context_menu(pos, button,
                                                                                                         file_bytes, type, name))
                        y -= link_label.height()
                        link_label.setGeometry(x_pos, y, 300, 40)
                        if y - link_label.height() - 10 < end_y_pos:
                            self.parent.is_chat_box_full = True
                            if index != len(self.parent.list_messages) - 1:
                                self.parent.is_last_message_on_screen = False
                        self.message_labels.append(link_label)
                        y -= space_between_messages
                        message = ""
                        label = self.create_temp_message_label(message)
                        label.setText(
                            f'<span style="font-size: {self.parent.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                            f'<span style="font-size: {self.parent.font_size - 3}px; color: gray;"> {message_time}</span>')
                        label.move(x_pos, y)
                        self.message_labels.append(label)
                        y -= label.height()
                    except Exception as e:
                        print(f"error in show messages is:{e}")
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

    def show_context_menu(self, pos, button, file_bytes, type, file_name):
        menu = QMenu(self)
        download_action = menu.addAction("Download")
        download_action.triggered.connect(lambda: download_file_from_bytes(file_bytes, type, file_name))

        # Use the position of the button as the reference for menu placement
        global_pos = button.mapToGlobal(pos)

        # Show the context menu at the adjusted position
        menu.exec_(global_pos)


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
        try:
            label = QLabel(message, self)
            label.setStyleSheet("color: white;")
            font = label.font()
            font.setPixelSize(self.parent.font_size)
            label.setFont(font)
            number_of_rows = math.floor(len(message) / 160) + 1
            if len(message) > 0 and number_of_rows > 1:
                format_label_text_by_row(label, message, number_of_rows)
                label.adjustSize()
            return label
        except Exception as e:
            print(f"error in creating message label {e}")

    def delete_message_labels(self):
        for label in self.message_labels:
            label.deleteLater()
        self.message_labels = []

    def check_editing_status(self):
        return self.text_entry.hasFocus()

    def updated_chatbox(self, updated_list):
        self.messages_list = updated_list

    def garbage_button_clicked(self):
        self.parent.file_to_send = None
        self.parent.file_name = ""
        self.parent.updated_chat()

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
            self.parent.is_create_group_inside_chat_pressed = False
            self.parent.file_name = ""
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
        self.block_friend_label = QLabel(self)
        self.remove_friend_label = QLabel(self)
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
                background-color: {self.parent.background_color_hex};  /* Use your desired blue color */
                border: 2px solid {self.parent.standard_hover_color};  /* Use a slightly darker shade for the border */
                border-radius: 5px;
                padding: 8px 16px;
                color: #b9c0c7;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }}

            QPushButton:hover {{
                background-color: {self.parent.standard_hover_color};
            }}

            QPushButton:pressed {{
                background-color: #202225;
                border-color: #72767d;
            }}
        """)

        selecting_button_pressed_stylesheet = (f"""
            QPushButton {{
                background-color: #3498db;  /* Use your desired color for pressed state */
                border: 2px solid {self.parent.standard_hover_color};  /* Use a slightly darker shade for the border */
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
                background-color: #2c3e50;  /* Use your desired color for pressed state */
                border-color: #34495e;  /* Use a slightly darker shade for the border in pressed state */
            }}
        """)

        border1_width = 725
        border1_height = self.friends_label.height() + 48
        self.border1_label = QLabel(self)
        self.border1_label.setStyleSheet(f'''
                        border: 2px solid {self.parent.standard_hover_color};
                        border-radius: 5px;
                        padding: 5px;
                        margin-bottom: 2px;
                    ''')
        self.border1_label.setGeometry(friend_x - 40, 0, border1_width, border1_height)
        self.border1_label.lower()

        border2_width = border1_width
        border3_height = self.friends_label.height() + 900
        self.border2_label = QLabel(self)
        self.border2_label.setStyleSheet(f'''
                        border: 2px solid {self.parent.standard_hover_color};
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
        self.border3_label.setStyleSheet(f'''
                        border: 2px solid {self.parent.standard_hover_color};
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
        self.search_box_color = "white"
        if self.parent.background_color == "Black and White":
            self.search_box_color = "black"

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
                f"background-color: {self.parent.standard_hover_color}; color: {self.search_box_color}; padding: 10px; border: 1px solid {self.parent.standard_hover_color}; border-radius: 5px; font-size: 14px;")
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
                line.setStyleSheet(f"background-color: {self.parent.standard_hover_color};")  # Set line color

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
                f"background-color: {self.parent.standard_hover_color}; color: {self.search_box_color}; padding: 10px; border: 1px solid {self.parent.standard_hover_color}; border-radius: 5px; font-size: 14px;")
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
                line.setStyleSheet(f"background-color: {self.parent.standard_hover_color};")  # Set line color

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
                    f"background-color: {self.parent.standard_hover_color}; color: {self.search_box_color}; padding: 10px; border: 1px solid {self.parent.standard_hover_color}; border-radius: 5px; font-size: 14px;")
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
                print(f"error pending page {e}")

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
                f"background-color: {self.parent.standard_hover_color}; color: {self.search_box_color}; padding: 10px; border: 1px solid {self.parent.standard_hover_color}; border-radius: 5px; font-size: 14px;")
            self.add_friend_entry.setFixedHeight(40)  # Increase height

        if self.parent.friends_box_page == "blocked":
            self.friend_labels = []
            friend_starter_y = 200 + (self.parent.friends_box_index * -50)
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
                f"background-color: {self.parent.standard_hover_color}; color: {self.search_box_color}; padding: 10px; border: 1px solid {self.parent.standard_hover_color}; border-radius: 5px; font-size: 14px;")
            self.search.setGeometry(search_x, search_y, search_width, search_height)
            self.search.textChanged.connect(self.on_text_changed_in_contact_search)

            friends_label_x = search_x
            for friend in friends_box_list:
                friend_label = QLabel(friend, self)
                friend_label.setStyleSheet(style_sheet)
                friend_label.move(friends_label_x + 25, friend_starter_y)
                friend_label.setFixedHeight(self.font_size)  # Increase height
                friend_label.adjustSize()  # Ensure the label size is adjusted to its content

                line = QFrame(self)
                line.setGeometry(friend_x - 40, friend_starter_y + self.font_size + 5, border2_width, 2)
                line.setStyleSheet(f"background-color: {self.parent.standard_hover_color};")  # Set line color


                unblock_friend_button_x = 1235

                unblock_friend_button = QPushButton(self)

                self.block_friend_label = QLabel("Block", self)
                self.raised_elements.append(self.block_friend_label)
                self.connect_button_label_pair(
                    unblock_friend_button,
                    self.block_friend_label,
                    "Unblock",
                    "discord_app_assets/block_icon.png",
                    self.unblock_friend,
                    unblock_friend_button_x - 60,
                    friend_starter_y + 10,
                    friend  # Pass the friend parameter here
                )

                if friend_starter_y > self.parent.height():
                    self.parent.is_friends_box_full = True
                    print("smaller then 0")
                    break

                friend_starter_y += 70
                self.friend_labels.append(friend_label)
                self.raise_all_element()
            if friend_starter_y < self.parent.height():
                self.parent.is_friends_box_full = False

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
        button.setStyleSheet(f"""           
            QPushButton:hover {{
                background-color: {self.parent.standard_hover_color};
            }}
            QPushButton {{
                background-color: transparent;
            }}
            QPushButton:pressed {{
                background-color: #202225;
                border-color: #72767d;
            }}""")

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
        elif self.parent.friends_box_page == "blocked":
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
        try:
            self.block_friend_label.raise_()
            self.remove_friend_label.raise_()
            self.chat_label.raise_()
        except Exception as e:
            x = 4
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
            print(f"error pending_button_pressed {e}")

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
            print(f"error add_friend_button_pressed {e}")

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
        self.Network.block_user(friend)
        print(f"blocking {friend}")

    def unblock_friend(self, friend):
        # Implement the logic to start a chat with the selected friend
        self.Network.unblock_user(friend)
        print(f"unblocked {friend}")


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
        self.file_dialog.setNameFilter("Image files (*.png *.jpg)")


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
        except Exception as e:
            print(f"error setting page {e}")

    def background_color_changed(self):
        new_background_color = self.color_combobox.currentText()
        self.parent.update_background_color(new_background_color)
        print(new_background_color)

    def font_updated(self):
        new_font = self.font_box.currentText()
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


class VideoPlayer(QWidget):
    def __init__(self, video_bytes, parent):
        super().__init__()
        self.parent = parent
        self.video_bytes = video_bytes
        self.setWindowTitle("Video Player")

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_widget = QVideoWidget(self)
        screen = QDesktopWidget().screenGeometry()
        # Extract the screen width and height
        screen_width = screen.width()
        screen_height = screen.height()
        self.video_widget.setGeometry(0, 0, screen_width, int(screen_height*0.83))

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.sliderReleased.connect(self.set_position)
        slider_x, slider_y, slider_width, slider_height = int(screen_width*0.1), int(screen_height*0.85), int(screen_width*0.8), int(screen_height*0.05)
        self.slider.setGeometry(slider_x, slider_y, slider_width, slider_height)

        exit_watch_button = QPushButton(self)
        exit_watch_button_x, exit_watch_button_y = (slider_x + slider_width + 20, slider_y + int(screen_height * 0.005))
        make_q_object_clear(exit_watch_button)
        exit_watch_button.clicked.connect(self.stop_watching)

        icon_path = "discord_app_assets/exit_button.png"
        button_size = (30, 30)
        set_button_icon(exit_watch_button, icon_path, button_size[0], button_size[1])
        exit_watch_button.setGeometry(exit_watch_button_x, exit_watch_button_y, button_size[0], button_size[1])

        self.duration_label = QLabel(self)
        self.duration_label.setStyleSheet("background-color: transparent; color: white;")
        duration_label_x, duration_label_y = int(screen_width*0.03), int(screen_height*0.865)
        self.duration_label.move(duration_label_x, duration_label_y)

        self.video_widget.mousePressEvent = self.toggle_play_pause

        # Set media player to use video widget
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.stateChanged.connect(self.handle_state_change)

        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.update_slider_position)

        # Start the position update timer with a short interval (e.g., 100 milliseconds)
        self.position_timer.start(1)

    def update_slider_position(self):
        # Update the slider position based on the current media player position
        position = self.media_player.position()
        self.slider.setValue(position)

    def toggle_play_pause(self, event):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.position_timer.stop()
        else:
            self.media_player.play()
            self.position_timer.start()

    def stop_watching(self):
        self.media_player.stop()
        self.parent.stop_watching_video()

    def play_video(self):
        try:
            # Create a temporary file in memory
            temp_file = QTemporaryFile()
            if temp_file.open():
                # Write the video bytes to the temporary file
                temp_file.write(self.video_bytes)
                # Flush the data to ensure it's written
                temp_file.flush()

                # Create a QMediaContent object with the QUrl pointing to the temporary file
                url = QUrl.fromLocalFile(temp_file.fileName())
                media_content = QMediaContent(url)

                # Set the media content to the media player and play
                self.media_player.setMedia(media_content)
                self.media_player.play()
            else:
                print("Failed to create temporary file")
        except Exception as e:
            print(f"play_video error :{e}")

    def update_duration(self, duration):
        self.slider.setMaximum(duration)
        self.duration_label.setText("Duration: " + QTime(0, 0).addMSecs(duration).toString("mm:ss"))

        self.duration_label.adjustSize()
        self.duration_label.raise_()

    def update_position(self, position):
        self.slider.setValue(position)
        # Format the position and duration to MM:SS format
        position_time = QTime(0, 0).addMSecs(position).toString("mm:ss")
        duration_time = QTime(0, 0).addMSecs(self.media_player.duration()).toString("mm:ss")
        # Update the duration label text
        self.duration_label.setText(f"{position_time} / {duration_time}")
        if position >= self.media_player.duration() - 10:  # Check if less than 100 milliseconds remain
            self.media_player.pause()
            self.media_player.setPosition(0)  # Rewind to the beginning for replay


    def handle_state_change(self, new_state):
        if new_state == QMediaPlayer.EndOfMedia:
            # If video reaches the end, pause instead of finishing
            self.play_video()
            self.media_player.pause()

    def set_position(self):
        position = self.slider.value()
        self.media_player.setPosition(position)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.pause()
                self.position_timer.stop()
            elif self.media_player.state() == QMediaPlayer.PausedState:
                self.media_player.play()
                self.position_timer.start()
        elif event.key() == Qt.Key_Escape:
            self.stop_watching()


class ScrollableWidget(QWidget):
    def __init__(self, parent, width, height, x, y):
        super().__init__()
        self.parent = parent
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.initUI()

    def initUI(self):
        # Create a scroll area
        try:
            self.scroll_area = QScrollArea(self.parent)
            self.scroll_area.setWidgetResizable(True)

            # Create a widget to contain labels and buttons
            inner_widget = QWidget()
            spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
            len_message_list = len(self.parent.parent.list_messages)

            # Set fixed width for inner widget to ensure proper layout
            #inner_widget.setFixedWidth(380)

            # Create a layout for the inner widget
            self.layout = QVBoxLayout(inner_widget)
            self.space_between_widgets = 10
            self.layout.setSpacing(self.space_between_widgets)  # Adjust this value as needed
            self.layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Align widgets to the left and top

            # Add labels and buttons to the layout
            self.load_all_message_func(reversed(self.parent.parent.list_messages))

            # Set the inner widget as the scroll area's widget
            self.scroll_area.setWidget(inner_widget)
            self.scroll_area.setGeometry(self.x, self.y, self.width, self.height)  # Set the geometry directly
            if self.parent.parent.is_new_chat_clicked:
                max = self.scroll_area.verticalScrollBar().maximum()
                self.scroll_area.verticalScrollBar().setValue(max)
                print(f"Scrolled to maximum {max}")
                self.scroll_value_changed(max)
                # Reset the flag
                self.parent.parent.is_new_chat_clicked = False
            else:
                if self.parent.parent.chat_start_index is not None:
                    self.scroll_area.verticalScrollBar().setValue(self.parent.parent.chat_start_index)
            self.scroll_area.verticalScrollBar().valueChanged.connect(self.scroll_value_changed)
        except Exception as e:
            print(f"Error in creating messages box {e}")

    def update_scroll_area_parent(self, new_parent):
        self.scroll_area.setParent(new_parent)

    def load_all_message_func(self, message_list):
        for i in message_list:
            self.add_message_to_layout(i)

    def add_message_to_layout(self, message):
        basic_files_types = ["xlsx", "py", "docx", "pptx", "txt", "pdf"]
        i = message
        message_content = i.get("content")
        message_time = i.get("timestamp")
        message_sender = i.get("sender_id")
        message_type = i.get("message_type")
        file_name = i.get("file_name")
        if not message_content or message_type == "string":

            content_label = self.parent.create_temp_message_label(message_content)

            # second part = Name + timestamp
            title_label = QLabel()
            title_label = self.parent.create_temp_message_label("")
            title_label.setText(
                f'<span style="font-size: {self.parent.parent.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                f'<span style="font-size: {self.parent.parent.font_size - 3}px; color: gray;"> {message_time}</span>')
            self.layout.addWidget(title_label)
            self.layout.addWidget(content_label)
        elif message_type == "image":
            try:
                decoded_compressed_image_bytes = base64.b64decode(message_content)
                image_bytes = zlib.decompress(decoded_compressed_image_bytes)

                image_label = QPushButton(self)
                image_label.setStyleSheet("background-color: transparent; border: none;")

                self.parent.load_image_from_bytes_to_button(image_bytes, image_label)
                image_label.setMaximumWidth(int(self.width / 3))  # Adjust the maximum width as needed

                image_label.clicked.connect(lambda _, image_bytes=image_bytes: open_image_bytes(image_bytes))

                message = ""
                title_label = self.parent.create_temp_message_label(message)
                title_label.setText(
                    f'<span style="font-size: {self.parent.parent.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                    f'<span style="font-size: {self.parent.parent.font_size - 3}px; color: gray;"> {message_time}</span>')

                self.layout.addWidget(title_label)
                self.layout.addWidget(image_label)
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


                video_label.clicked.connect(
                    lambda _, video_bytes=video_bytes: self.parent.parent.start_watching_video(video_bytes))

                play_button = QPushButton(video_label)
                play_button_icon_path = "discord_app_assets/play_video_icon.png"
                play_button_size = (50, 50)
                play_button.clicked.connect(
                    lambda _, video_bytes=video_bytes: self.parent.parent.start_watching_video(video_bytes))
                set_button_icon(play_button, play_button_icon_path, play_button_size[0], play_button_size[1])
                play_button.move(0 + (0.5 * video_label.width() - 0.5 * play_button_size[0]),
                                 0 + (0.5 * video_label.height() - 0.5 * play_button_size[1]))
                make_q_object_clear(play_button)

                # video_frame = VideoThumbnailWidget(self, video_label, play_button)
                message = ""
                title_label = self.parent.create_temp_message_label(message)
                title_label.setText(
                    f'<span style="font-size: {self.parent.parent.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                    f'<span style="font-size: {self.parent.parent.font_size - 3}px; color: gray;"> {message_time}</span>')
                self.layout.addWidget(title_label)
                self.layout.addWidget(video_label)
            except Exception as e:
                print(f"error in show messages is:{e}")
        elif message_type == "audio":
            try:
                decoded_compressed_audio_bytes = base64.b64decode(message_content)
                audio_bytes = zlib.decompress(decoded_compressed_audio_bytes)

                audio_label = QPushButton(f"{file_name}", self)
                audio_label.setStyleSheet(
                    f"background-color: {self.parent.parent.standard_hover_color}; border: none; color: white; font-size: {self.parent.parent.font_size}px; padding-left: 50%;")

                play_button = QPushButton(self)
                play_button_icon_path = "discord_app_assets/play_video_icon.png"
                play_button_size = (25, 25)
                set_button_icon(play_button, play_button_icon_path, play_button_size[0], play_button_size[1])
                play_button.clicked.connect(
                    lambda _, audio_bytes=audio_bytes: play_mp3_from_bytes(audio_bytes,
                                                                           self.parent.parent.mp3_message_media_player))
                # audio_label.setGeometry(x_pos, y, 300, 40)
                make_q_object_clear(play_button)

                message = ""
                title_label = self.parent.create_temp_message_label(message)
                title_label.setText(
                    f'<span style="font-size: {self.parent.parent.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                    f'<span style="font-size: {self.parent.parent.font_size - 3}px; color: gray;"> {message_time}</span>')

                self.layout.addWidget(title_label)
                self.layout.addWidget(audio_label)
            except Exception as e:
                print("error in audio file")
        elif message_type in basic_files_types:
            try:
                decoded_compressed_file_bytes = base64.b64decode(message_content)
                file_bytes = zlib.decompress(decoded_compressed_file_bytes)

                link_label = QPushButton(f"{file_name}", self)
                link_label.setStyleSheet(
                    f"background-color: {self.parent.parent.standard_hover_color}; border: none; color: white; font-size: {self.parent.parent.font_size}px; padding-left: 50%;")
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
                # link_label.setGeometry(x_pos, y, 300, 40)
                message = ""
                title_label = self.parent.create_temp_message_label(message)
                title_label.setText(
                    f'<span style="font-size: {self.parent.parent.font_size + 2}px; color: white; font-weight: bold;">{message_sender}</span>'
                    f'<span style="font-size: {self.parent.parent.font_size - 3}px; color: gray;"> {message_time}</span>')

                self.layout.addWidget(title_label)
                self.layout.addWidget(link_label)
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

    def scroll_up_by_N_widgets(self, N):
        total_height = 0
        for i in range(min(N * 2, self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                total_height += widget.sizeHint().height() + self.space_between_widgets
        print(f"total height is {total_height}")
        self.scroll_area.verticalScrollBar().setValue(total_height)
        self.scroll_value_changed(self.scroll_area.verticalScrollBar().value())

    def scroll_value_changed(self, value):
        # Update your variable with the current scroll value
        if value == 0 and not self.parent.parent.is_new_chat_clicked:
            if len(self.parent.parent.list_messages) >= 15:
                self.parent.parent.Network.ask_for_more_messages()
                print("asked for more messages")

        self.parent.parent.chat_start_index = value


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
        self.initUI()

    def initUI(self):
        try:
            if self.box_format == "create":
                submit_button_text = "Create DM"
            else:
                submit_button_text = "ADD"
            starter_x = self.x
            starter_y_of_border = self.y + 50
            adding_border_height = 400
            adding_border_width = 300

            border_of_adding = QLabel(self.parent)
            border_of_adding.setGeometry(starter_x, starter_y_of_border, adding_border_width, adding_border_height)
            border_of_adding.raise_()
            border_of_adding.setStyleSheet("""border: 2px solid black;  
            /* Use a slightly darker shade for the border */
                            border-radius: 5px;""")

            label = QLabel(f"Select friends", self.parent)
            label.setStyleSheet("""color: white;font-size: 20px;""")
            label.move(starter_x + 20, starter_y_of_border + 10)
            Page = 0
            if len(self.friends_list) > 0:
                Page = self.create_group_index + 1

            if self.parent.parent.is_create_group_inside_chat_pressed:
                if self.parent.current_group_id:
                    number_of_group_members = self.parent.parent.get_number_of_members_by_group_id(self.parent.current_group_id)
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
            self.page_plus_selected_label.move(starter_x + 20, starter_y_of_border + 45)



            self.amount_of_people_to_add_text_label = QLabel(page_plus_selected_text, self.parent)
            self.amount_of_people_to_add_text_label.setStyleSheet("""color: white;font-size: 12px;""")
            self.amount_of_people_to_add_text_label.move(starter_x + 40, starter_y_of_border + 75)

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
            scroll_up_button.move(starter_x + 230, starter_y_of_border + 25)
            scroll_up_button.setFixedWidth(50)
            scroll_up_button.setStyleSheet(style_sheet)

            scroll_down_button = QPushButton("↓", self.parent)
            scroll_down_button.move(starter_x + 230, starter_y_of_border + 55)
            scroll_down_button.setFixedWidth(50)
            scroll_down_button.setStyleSheet(style_sheet)

            starter_x = self.x
            starter_y = self.y + 150
            i = 0
            for friend in self.friends_list:
                if i >= self.create_group_index * 5:
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
                            group_members = self.parent.parent.get_group_members_by_group_id(self.parent.current_group_id)
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
                    height = friend_label.height() + 30
                    friend_label.setGeometry(starter_x + 10, starter_y, adding_border_width - 20, height)
                    friend_checkbox.move(starter_x + 260, starter_y + 15)
                    starter_y += friend_label.height() - 20
                    friend_label.raise_()
                    friend_checkbox.raise_()
                i += 1

            button = QPushButton(submit_button_text, self.parent)
            button.move(starter_x + 15, starter_y_of_border + adding_border_height - 80)
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
            button.setFixedWidth(adding_border_width - 30)
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



class VideoThumbnailWidget(QWidget):
    def __init__(self, parent, video_button, play_button):
        super().__init__()
        try:
            self.parent = parent

            # Set the video_button as the parent widget of the play_button
            play_button.setParent(video_button)

            # Calculate the position to center the play_button inside the video_button
            play_width = play_button.width()
            play_height = play_button.height()
            video_width = video_button.width()
            video_height = video_button.height()
            play_x = (video_width - play_width) // 2
            play_y = (video_height - play_height) // 2

            # Move the play_button to the center of the video_button
            play_button.move(play_x, play_y)

        except Exception as e:
            print(f"Error in creating thumbnail: {e}")






















