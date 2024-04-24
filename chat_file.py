from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QColor
from PyQt5.QtCore import pyqtSignal
from functools import partial
from discord_comms_protocol import client_net
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QGraphicsBlurEffect
from PyQt5.QtCore import Qt, QSize, QPoint, QCoreApplication, QTimer, QMetaObject, Q_ARG, QObject, pyqtSignal,  QSettings, QUrl, Qt, QUrl, QTime, QBuffer, QIODevice, QTemporaryFile
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter, QPainterPath
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5 import QtCore
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
import concurrent.futures
import warnings
import re
import pyaudio
import cv2
from datetime import datetime
from settings_page_widgets import create_slider


def insert_item_to_table(table, col, value, row_position):
    if col == 3:  # If it's the column for the photo
        item = QTableWidgetItem()
        pixmap = QPixmap()
        pixmap.loadFromData(value)
        item.setIcon(QIcon(pixmap))
        item.setSizeHint(QSize(100, 100))
    else:
        item = QTableWidgetItem(str(value))
    if col != 0:
        item.setTextAlignment(Qt.AlignCenter)
    table.setItem(row_position, col, item)


def remove_row(table, row_number):
    if row_number >= 0 and row_number < table.rowCount():
        table.removeRow(row_number)
        print(f"Row {row_number} removed successfully.")
    else:
        print("Invalid row number. Row not removed.")


def extract_number(s):
    # Use regular expression to find the number in the string
    match = re.search(r'\d+', s)
    if match:
        # Convert the matched number to an integer and return it
        return int(match.group())
    else:
        # If no number is found, return None or raise an exception, depending on your use case
        return None  # or raise ValueError("No number found in the string")


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
        # self.slider.
        # self.slider.setStyleSheet(
        #     f"""
        #     QSlider::handle {{
        #         width: 1px;  /* Set width of the handle */
        #         height: 1px; /* Set height of the handle */
        #         background-color: {self.parent.standard_hover_color}; /* Set the color of the handle */
        #     }}
        #     """
        # )
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
        self.media_player.setVolume(self.parent.volume)

        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.update_slider_position)

        # Start the position update timer with a short interval (e.g., 1 milliseconds)
        self.position_timer.start(1)

    def update_slider_position(self):
        # Update the slider position based on the current media player position
        position = self.media_player.position()
        self.slider.setValue(position)
        # Format the position and duration to MM:SS format
        position_time = QTime(0, 0).addMSecs(position).toString("mm:ss")
        duration_time = QTime(0, 0).addMSecs(self.media_player.duration()).toString("mm:ss")
        # Update the duration label text
        self.duration_label.setText(f"{position_time} / {duration_time}")
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


class PlaylistWidget(QWidget):
    def __init__(self, main_page_widget):
        super().__init__()
        self.parent = main_page_widget
        self.init_ui()

    def init_ui(self):

        # Create a table widget
        self.sliders_style_sheet = f"""
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
                           background: {self.parent.standard_hover_color}; /* Change this color to the desired color for the left side */
                       }}
                               """
        self.last_selected_row = None
        table_x, table_y = 0, 70
        table_width, table_height = int(self.parent.screen_width * 0.99), int(self.parent.screen_height * 0.075)
        self.search_table = self.create_table_widget(table_width, table_height, table_x, table_y, "")
        self.search_table.insertRow(0)
        self.search_table.clearSelection()
        self.search_table.setSelectionMode(QAbstractItemView.NoSelection)

        table_x, table_y = 0, self.parent.screen_height // 5.4
        table_width, table_height = int(self.parent.screen_width * 0.99), int(self.parent.screen_height * 0.648)
        self.table = self.create_table_widget(table_width, table_height, table_x, table_y, "playlist_table")

        self.search_song_entry = QLineEdit(self)
        search_song_entry_x, search_song_entry_y = int(self.parent.screen_width * 0.35), 0
        width, height = 450, 40
        self.search_song_entry.setGeometry(search_song_entry_x, search_song_entry_y, width, height)
        self.search_song_entry.setPlaceholderText("🔍 What do you want to play?")

        self.add_to_playlist_button = QPushButton("➕ Add song to Playlist", self)
        make_q_object_clear(self.add_to_playlist_button)
        size = QSize(int(0.072 * self.parent.screen_width), int(self.parent.screen_height * 0.028))
        self.add_to_playlist_button.setFixedSize(size)
        add_to_playlist_button_x, add_to_playlist_button_y = 0, int(self.parent.screen_height * 0.03)
        self.add_to_playlist_button.move(add_to_playlist_button_x, add_to_playlist_button_y)
        self.add_to_playlist_button.clicked.connect(self.parent.save_searched_song_to_playlist)

        self.try_searched_song_button = QPushButton("🎧 Check out the song", self)
        make_q_object_clear(self.try_searched_song_button)
        self.try_searched_song_button.setFixedSize(size)
        try_searched_song_button_x, try_searched_song_button_y = int(size.width() * 1.1), int(
            self.parent.screen_height * 0.03)
        self.try_searched_song_button.move(try_searched_song_button_x, try_searched_song_button_y)
        self.try_searched_song_button.clicked.connect(self.parent.play_search_result)

        self.remove_selected_song_button = QPushButton("❌ Remove selected song", self)
        make_q_object_clear(self.remove_selected_song_button)
        self.remove_selected_song_button.setFixedSize(size)
        remove_selected_song_button_x, remove_selected_song_button_y = 0, int(
            self.parent.screen_height * 0.15)
        self.remove_selected_song_button.move(remove_selected_song_button_x, remove_selected_song_button_y)
        self.remove_selected_song_button.clicked.connect(self.remove_song)
        self.playlist_duration_slider_current_time_label = QLabel(self)
        self.playlist_duration_slider_duration_label = QLabel(self)
        make_q_object_clear(self.playlist_duration_slider_current_time_label)
        make_q_object_clear(self.playlist_duration_slider_duration_label)
        playlist_duration_slide_x, playlist_duration_slide_y = int(self.parent.screen_width * 0.265), int(
            self.parent.screen_height * 0.15)
        playlist_slider_width, playlist_slider_height = 750, 25

        self.playlist_duration_slider = create_slider(self, 0, 0, 0, None
                                                      , playlist_duration_slide_x
                                                      , playlist_duration_slide_y, playlist_slider_width, playlist_slider_height, self.sliders_style_sheet)
        self.playlist_duration_slider.sliderMoved.connect(self.update_media_player_position)
        self.playlist_duration_slider_duration_label.move(int((playlist_duration_slide_x + playlist_slider_width)*1.01),
                                                          int(playlist_duration_slide_y*1.035))
        self.playlist_duration_slider_current_time_label.move(int(playlist_duration_slide_x*0.92),
                                                              int(playlist_duration_slide_y*1.035))
        self.playlist_duration_slider_current_time_label.setStyleSheet("color: white")
        self.playlist_duration_slider_duration_label.setStyleSheet("color: white")

        last_song_button = QPushButton(self)
        next_song_button = QPushButton(self)
        pause_and_play_button = QPushButton(self)
        self.shuffle_button = QPushButton(self)
        self.replay_song_button = QPushButton(self)
        last_song_button_icon_path = "discord_app_assets/last_song_icon.png"
        next_song_button_icon_path = "discord_app_assets/next_song_icon.png"
        pause_and_play_button_icon_path = "discord_app_assets/pause_and_play_icon.png"
        shuffle_button_icon_path = "discord_app_assets/suffle_icon.png"
        replay_song_button_icon_path = "discord_app_assets/replaying_icon.png"
        buttons_width, buttons_height = int(self.parent.screen_width*0.026), int(self.parent.screen_height*0.0462)
        set_button_icon(self.replay_song_button, replay_song_button_icon_path, buttons_width, buttons_height)
        set_button_icon(last_song_button, last_song_button_icon_path, buttons_width, buttons_height)
        set_button_icon(next_song_button, next_song_button_icon_path, buttons_width, buttons_height)
        set_button_icon(pause_and_play_button, pause_and_play_button_icon_path, buttons_width, buttons_height)
        set_button_icon(self.shuffle_button, shuffle_button_icon_path, buttons_width, buttons_height)
        first_button_x = int(self.parent.screen_width * 0.43)
        buttons_y = int(self.parent.screen_height * 0.842)
        playlist_volume_slider_x, playlist_volume_slider_y = int(buttons_width * 1.2), int(
            self.parent.screen_height * 0.854)
        playlist_volume_slider_width, playlist_volume_slider_height = 500, 25
        self.playlist_volume_slider_label = QLabel(self)
        make_q_object_clear(self.playlist_volume_slider_label)
        self.playlist_volume_slider = create_slider(self, 0, 100, self.parent.volume
                                                    , self.playlist_volume_update,
                                                    playlist_volume_slider_x, playlist_volume_slider_y, playlist_volume_slider_width, playlist_volume_slider_height, self.sliders_style_sheet
                                                    )
        self.playlist_volume_slider_label.move(int(playlist_volume_slider_x*0.4), int(playlist_volume_slider_y*0.995))
        self.set_icon_for_volume_label()
        # self.volume_slider.

        delta_between_button = int(self.parent.screen_width * 0.03125)
        self.replay_song_button.move(first_button_x+(delta_between_button*3), buttons_y)
        self.shuffle_button.move(first_button_x-delta_between_button, buttons_y)
        last_song_button.move(first_button_x, buttons_y)
        pause_and_play_button.move(first_button_x+delta_between_button, buttons_y)
        next_song_button.move(first_button_x+(delta_between_button*2), buttons_y)
        make_q_object_clear(last_song_button)
        make_q_object_clear(next_song_button)
        make_q_object_clear(pause_and_play_button)
        make_q_object_clear(self.shuffle_button)
        make_q_object_clear(self.replay_song_button)
        last_song_button.raise_()
        next_song_button.raise_()
        pause_and_play_button.raise_()
        pause_and_play_button.clicked.connect(self.parent.pause_and_unpause_playlist)
        last_song_button.clicked.connect(self.parent.go_to_last_song)
        next_song_button.clicked.connect(self.parent.go_to_next_song)
        self.shuffle_button.clicked.connect(self.toggle_shuffle)
        self.replay_song_button.clicked.connect(self.toggle_replay_song)

        self.update_music_page_style_sheet()
        # Ensure the data is visible

        self.table.show()

    def update_media_player_position(self, new_position):
        # Convert the new position to seconds
        try:
            if self.parent.playlist_media_player.state() == QMediaPlayer.PlayingState:
                is_playing = True
            else:
                is_playing = False
            self.parent.playlist_media_player.pause()
            new_position_seconds = new_position  # Convert milliseconds to seconds

            # Set the new position of the media player
            self.parent.playlist_media_player.setPosition(new_position_seconds)
            if is_playing:
                self.parent.playlist_media_player.play()
        except Exception as e:
            print(f"error with changing audio position {e}")

    def update_current_duration_text(self, text):
        self.playlist_duration_slider_current_time_label.setText(text)
        self.playlist_duration_slider_current_time_label.adjustSize()

    def update_duration_tex(self, text):
        self.playlist_duration_slider_duration_label.setText(text)
        self.playlist_duration_slider_duration_label.adjustSize()

    def set_icon_for_volume_label(self):
        muted_volume_path = "discord_app_assets/speaker_icon0.png"
        low_volume_path = "discord_app_assets/speaker_icon1.png"
        mid_volume_path = "discord_app_assets/speaker_icon2.png"
        high_volume_path = "discord_app_assets/speaker_icon3.png"
        if self.parent.playlist_volume == 0:
            set_icon_from_path_to_label(self.playlist_volume_slider_label, muted_volume_path)
        elif self.parent.playlist_volume < 30:
            set_icon_from_path_to_label(self.playlist_volume_slider_label, low_volume_path)
        elif self.parent.playlist_volume < 60:
            set_icon_from_path_to_label(self.playlist_volume_slider_label, mid_volume_path)
        else:
            set_icon_from_path_to_label(self.playlist_volume_slider_label, high_volume_path)

    def playlist_volume_update(self, value):
        self.playlist_volume_slider.setValue(value)
        self.parent.playlist_volume = value
        self.parent.playlist_media_player.setVolume(value)
        self.set_icon_for_volume_label()

    def toggle_shuffle(self):
        self.parent.toggle_shuffle()
        if self.parent.shuffle:
            self.shuffle_button.setStyleSheet(f"background-color: {self.parent.standard_hover_color}"
                                              f"; border-radius: 15px;")
        else:
            self.shuffle_button.setStyleSheet(f"background-color: transparent"
                                                  f"; border-radius: 15px;")

    def toggle_replay_song(self):
        try:
            if self.parent.replay_song:
                self.parent.replay_song = False
                self.replay_song_button.setStyleSheet("background-color: transparent; border-radius: 15px;")
            else:
                self.parent.replay_song = True
                self.replay_song_button.setStyleSheet(f"background-color: {self.parent.standard_hover_color}"
                                                      f"; border-radius: 15px;")
        except Exception as e:
            print(f"error with toggling replay song {e}")

    def remove_song(self):
        remove_row(self.table, self.parent.playlist_index)
        row_count = self.table.rowCount()
        self.parent.remove_song_from_playlist()

    def create_table_widget(self, table_width, table_height, table_x, table_y, table_name):
        row_height = int(self.parent.screen_height * 0.0462)
        table = QTableWidget(self)
        table.setFocusPolicy(Qt.NoFocus)
        table.verticalHeader().setDefaultSectionSize(row_height)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Title", "Date Added", "Duration", "Album Photo"])
        table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignLeft)

        # Set the number of rows in the table
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        table.setGeometry(table_x, table_y, table_width, table_height)

        if table_name == "playlist_table":
            table.cellPressed.connect(self.cell_pressed)
            table.itemSelectionChanged.connect(self.onSelectionChanged)

        table.setShowGrid(False)
        first_column_width = table_width * 0.4
        other_column_width = table_width * 0.18

        table.setColumnWidth(0, first_column_width)
        table.setColumnWidth(1, other_column_width)
        table.setColumnWidth(2, other_column_width)
        table.setColumnWidth(3, other_column_width)

        return table

    def update_music_page_style_sheet(self):
        self.apply_table_stylesheet(self.table)
        self.apply_table_stylesheet(self.search_table)
        self.apply_style_sheet_to_text_entry()
        self.apply_style_sheet_for_button()

    def apply_style_sheet_to_text_entry(self):
        if self.parent.background_color == "Black and White":
            text_entry_color = "black"
        else:
            text_entry_color = "white"
        self.search_song_entry.setStyleSheet(
            f"background-color: {self.parent.standard_hover_color}; "
            f"color: {text_entry_color}; padding: 10px; "
            f"border-radius: 5px; font-size: 14px;")

    def apply_style_sheet_for_button(self):
        if self.parent.background_color == "Black and White":
            text_entry_color = "black"
        else:
            text_entry_color = "white"
        style_sheet = f"background-color: {self.parent.standard_hover_color}; color: {text_entry_color}; border-radius: 15px;"
        self.add_to_playlist_button.setStyleSheet(style_sheet)
        self.try_searched_song_button.setStyleSheet(style_sheet)
        self.remove_selected_song_button.setStyleSheet(style_sheet)

    def apply_table_stylesheet(self, table):
        if self.parent.background_color == "Black and White":
            text_entry_color = "black"
        else:
            text_entry_color = "white"
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.parent.background_color_hex};
                border: 1px solid #d0d0d0;
                selection-background-color: {self.parent.standard_hover_color};
                color: {text_entry_color};  
            }}
            QTableWidget::item:hover {{
                background-color: {self.parent.standard_hover_color};
            }}
            QTableWidget QHeaderView::section {{
                color: {text_entry_color};
                border: 0; /* Remove border between column headers */
            }}
            QHeaderView::section {{
                color: {text_entry_color};  
                background-color: {self.parent.background_color_hex};
                border: 1px solid #d0d0d0;
                padding: 4px;
            }}
            QHeaderView::section:checked {{
                background-color: {self.parent.standard_hover_color};
            }}
            QTableWidget::item:selected {{
                background-color: {self.parent.standard_hover_color};
            }}
            QTableWidget QTableWidgetItem {{
                color: {text_entry_color};
                text-align: center; /* Align text in the middle */
                border: 0; /* Remove border between cells */
            }}
        """)

    def find_row_by_text(self, text):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)  # Assuming the first column (index 0)
            if item and (item.text() == text or item.text().startswith(text) or text in item.text()):
                return row
        return -1  # Return -1 if the text is not found in any row

    def insert_search_data(self, video_info_dict):
        try:
            row_position = 0
            # Extract data from the dictionary
            title = video_info_dict.get('title')
            thumbnail_bytes = video_info_dict.get('thumbnail_bytes')
            audio_bytes = video_info_dict.get('audio_bytes')
            audio_duration = video_info_dict.get('audio_duration')

            # Set the current date as the "Date Added"
            date_added = datetime.now().strftime('%Y-%m-%d')

            # Insert data into the table
            for col, value in enumerate([title, date_added, audio_duration, thumbnail_bytes]):
                insert_item_to_table(self.search_table, col, value, row_position)
        except Exception as e:
            print(e)

    def insert_playlist_songs(self, list_video_info_dict):
        try:
            row_position = 0
            for video_info_dict in list_video_info_dict:
                self.table.insertRow(row_position)
                # Extract data from the dictionary
                title = video_info_dict.get('title')
                thumbnail_bytes = video_info_dict.get('thumbnail_bytes')
                audio_duration = video_info_dict.get('audio_duration')
                date_added = video_info_dict.get('timestamp')

                # Insert data into the table
                for col, value in enumerate([title, date_added, audio_duration, thumbnail_bytes]):
                    insert_item_to_table(self.table, col, value, row_position)
                row_position += 1
            self.select_row(0)
        except Exception as e:
            print(e)

    def insert_new_song_to_playlist(self, song_dict):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        title = song_dict.get('title')
        thumbnail_bytes = song_dict.get('thumbnail_bytes')
        audio_bytes = song_dict.get('audio_bytes')
        audio_duration = song_dict.get('audio_duration')
        date_added = datetime.now().strftime('%Y-%m-%d')

        # Insert data into the table
        for col, value in enumerate([title, date_added, audio_duration, thumbnail_bytes]):
            insert_item_to_table(self.table, col, value, row_position)

    def cell_pressed(self, row, col):
        # Get the item text when a cell is pressed
        self.parent.set_new_playlist_index_and_listen(row)
        self.select_row(row)
        item = self.table.item(row, col)
        if item:
            print("Cell Pressed:", item.text())

    def select_row(self, row):
        # Clear any existing selections
        try:
            self.last_selected_row = row
            self.table.clearSelection()
            # Create a selection range for the entire row
            selection_range = QTableWidgetSelectionRange(row, 0, row, self.table.columnCount() - 1)

            # Select the range
            self.table.setRangeSelected(selection_range, True)
            #self.table.horizontalHeader().clearSelection()
        except Exception as e:
            print(f"error in inserting table {e}")

    def clear_selection(self):
        self.table.clearSelection()

    def onSelectionChanged(self):
        try:
            if self.last_selected_row is not None:
                selected_rows = self.table.selectionModel().selectedRows()
                if len(selected_rows) == 0:
                    # No rows are selected, so reselect the previously selected row
                    self.select_row(self.last_selected_row)
        except Exception as e:
            print(e)





























