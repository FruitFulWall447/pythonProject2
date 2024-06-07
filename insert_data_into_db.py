import faker
import database_func
import random
import copy
import os
import base64
from mutagen.mp3 import MP3


faker = faker.Faker()
CONST_PASSWORD = "kevin123"
CONST_EMAIL = "kollerkevin1@gmail.com"
USERS_LIST = []


def file_to_bytes(file_path):
    with open(file_path, "rb") as file:
        image_bytes = file.read()
        return image_bytes


def format_duration(seconds):
    minutes = seconds // 60
    seconds %= 60
    return f"{minutes}:{seconds:02d}"


def get_mp3_duration(mp3_path):
    try:
        audio = MP3(mp3_path)
        duration_in_seconds = int(audio.info.length)
        return format_duration(duration_in_seconds)
    except Exception as e:
        print(f"Error getting MP3 duration: {e}")
        return "00:00"


def get_random_file_from_folder(folder_path):
    try:
        # Get a list of all files in the folder
        files = [f for f in os.listdir(folder_path)
                 if os.path.isfile(os.path.join(folder_path, f)) and not f.lower().endswith('.ini')]

        # Check if the folder is empty
        if not files:
            print("The folder is empty.")
            return None

        # Select a random file from the list
        random_file = random.choice(files)
        return os.path.join(folder_path, random_file)

    except Exception as e:
        print(f"Error getting random file: {e}")
        return None


def get_file_type(file_name):
    if file_name.endswith(("png", "jpg")):
        return "image"
    elif file_name.endswith(("mp4", "mov")):
        return "video"
    elif file_name.endswith("mp3"):
        return "audio"
    elif file_name.endswith("txt"):
        return "txt"
    elif file_name.endswith("pdf"):
        return "pdf"
    elif file_name.endswith("pptx"):
        return "pptx"
    elif file_name.endswith("docx"):
        return "docx"
    elif file_name.endswith("py"):
        return "py"
    elif file_name.endswith("xlsx"):
        return "xlsx"
    else:
        return "unknown"


def insert_users_count(number_of_users):
    list_users = []
    for i in range(number_of_users):
        username = faker.user_name()
        database_func.insert_user(username, CONST_PASSWORD, CONST_EMAIL)
        list_users.append(username)
    return list_users


def send_friend_request_from_users_to_others(number_of_request):
    for i in range(number_of_request):
        temp_list = USERS_LIST.copy()
        friend_user = random.choice(temp_list)
        temp_list.remove(friend_user)
        user = random.choice(temp_list)
        if not database_func.is_active_request(friend_user, user) and not database_func.are_friends(user, friend_user):
            database_func.send_friend_request(user, friend_user)
            options_list = [0, 1]
            choice = random.choice(options_list)
            if choice == 0:
                database_func.handle_friend_request(user, friend_user, True)


def create_groups(numbers_groups):
    for i in range(numbers_groups):
        numbers_of_members = random.randint(3, 10)
        temp_list = USERS_LIST.copy()
        users_list = []
        for t in range(numbers_of_members):
            username = random.choice(temp_list)
            temp_list.remove(username)
            users_list.append(username)
        group_leader = random.choice(users_list)
        group_name = f"{group_leader}'s group"
        database_func.create_group(group_name, group_leader, users_list)


def make_chats_for_users():
    for user in USERS_LIST:
        users_groups = database_func.get_user_groups(user)
        if len(users_groups) > 0:
            for group_dict in users_groups:
                group_members = group_dict.get("group_members")
                group_members.remove(user)
                for group_user in group_members:
                    database_func.add_chat_to_user(user, group_user)
        else:
            pass


def generate_messages_for_chats(number_of_messages_per_chat):
    for user in USERS_LIST:
        user_chats_list = database_func.get_user_chats(user)
        for chat in user_chats_list:
            for i in range(number_of_messages_per_chat):
                options_list = [0, 1, 1, 1, 1]
                choice = random.choice(options_list)
                if choice == 1:
                    message_str = faker.text()
                    database_func.add_message(user, chat, message_str, "string", None)
                else:
                    folder_path = r"files_for_inserting\messages_files"
                    random_file = get_random_file_from_folder(folder_path)
                    file_bytes = file_to_bytes(random_file)
                    encoded_bytes = base64.b64encode(file_bytes).decode()
                    extension = random_file.split(".")[1]
                    file_name = faker.file_name(extension=extension)
                    message_type = get_file_type(random_file)
                    database_func.add_message(user, chat, encoded_bytes, message_type, file_name)


def put_pics_for_everyone():
    folder_path = r"files_for_inserting\profile_pics"
    for user in USERS_LIST:
        random_file = get_random_file_from_folder(folder_path)
        image_bytes = file_to_bytes(random_file)
        encoded_bytes = base64.b64encode(image_bytes).decode()
        database_func.update_profile_pic(user, encoded_bytes)


def put_songs_for_everyone():
    folder_path1 = r"files_for_inserting\songs"
    folder_path2 = r"files_for_inserting\profile_pics"
    for user in USERS_LIST:
        files = []
        for i in range(5):
            random_mp3_file = get_random_file_from_folder(folder_path1)
            while random_mp3_file in files:
                random_mp3_file = get_random_file_from_folder(folder_path1)
            files.append(random_mp3_file)
            random_thumbnail = get_random_file_from_folder(folder_path2)
            mp3_file_bytes = file_to_bytes(random_mp3_file)
            thumbnail_bytes = file_to_bytes(random_thumbnail)
            file_name = os.path.basename(random_mp3_file)
            duration = get_mp3_duration(random_mp3_file)
            database_func.add_song(file_name, mp3_file_bytes, user, duration, thumbnail_bytes)


def initiate_db_importer():
    global USERS_LIST
    numbers_of_users_to_insert = 50
    USERS_LIST = insert_users_count(numbers_of_users_to_insert)
    numbers_of_requests = 500
    send_friend_request_from_users_to_others(numbers_of_requests)
    number_of_groups = 50
    create_groups(number_of_groups)
    make_chats_for_users()
    message_per_chat = 20
    generate_messages_for_chats(message_per_chat)
    put_pics_for_everyone()
    put_songs_for_everyone()


initiate_db_importer()





