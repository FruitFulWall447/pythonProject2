import sqlite3
import binascii
import os
import hashlib
import secrets
import json
from datetime import datetime
import base64
import string
import random

folder_name = "discord_app_files"
files_folder_path = folder_name
pepper = "c5b97dce"
basic_files_types = ["xlsx", "py", "docx", "pptx", "txt", "pdf", "video", "audio", "image"]
default_settings_dict = {
    "volume": 50,  # Default volume level
    "output_device": "Default",  # Default output device
    "input_device": "Default",  # Default input device
    "camera_device_index": 0,  # Default camera device
    "font_size": 12,  # Default font size
    "font": "Arial",  # Default font
    "theme_color": "Blue",  # Default theme color
    "censor_data": False,  # Default censor data setting
    "private_account": False,  # Default account privacy setting
    "push_to_talk_bind": None,  # Default push-to-talk key binding
    "2fa_enabled": False  # Default 2-factor authentication setting
}


def current_timestamp():
    time_now = datetime.now()
    return time_now.strftime('%Y-%m-%d %H:%M:%S')


def unpack_settings(variables_dict):
    return (
        variables_dict["volume"],
        variables_dict["output_device"],
        variables_dict["input_device"],
        variables_dict["camera_device_index"],
        variables_dict["font_size"],
        variables_dict["font"],
        variables_dict["theme_color"],
        variables_dict["censor_data"],
        variables_dict["private_account"],
        variables_dict["push_to_talk_bind"],
        variables_dict["two_factor_auth"]
    )


def save_bytes_to_file(data_bytes, file_path):
    with open(file_path, 'wb') as file:
        file.write(data_bytes)


def hash_sha2_bytes(bytes_data):
    # Create a new SHA-256 hash object
    sha256_hash = hashlib.sha256()

    sha256_hash.update(bytes_data)

    # Get the hexadecimal representation of the hash
    hashed_string = sha256_hash.hexdigest()

    return hashed_string


def file_to_bytes(file_path):
    """Read file bytes from the given file path."""
    try:
        with open(file_path, 'rb') as file:
            file_bytes = file.read()
        return file_bytes
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def generate_random_filename(length=24):
    """Generate a random filename."""
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def save_file(file_bytes, file_path):
    try:
        with open(file_path, 'wb') as file:
            file.write(file_bytes)
        print(f"File saved successfully at: {file_path}")
    except Exception as e:
        print(f"Error saving file: {e}")


def create_user_settings(user_id):
    # Connect to the database
    connection = connect_to_kevindb()

    # Create a cursor object to execute SQL queries
    cursor = connection.cursor()

    # Prepare the SQL query to insert a new row into settings_table
    insert_query = """
    INSERT INTO settings_table 
    (user_id, volume, output_device, input_device, camera_device_index, 
    font_size, font, theme_color, censor_data, private_account, 
    push_to_talk_bind, two_factor_auth) 
    VALUES 
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    # Extract default settings values from the default_settings_dict
    default_settings_values = [default_settings_dict[key] for key in default_settings_dict]

    # Insert the new row with user_id and default settings
    cursor.execute(insert_query, (user_id,) + tuple(default_settings_values))

    # Commit the transaction
    connection.commit()

    # Close the cursor and database connection
    cursor.close()
    connection.close()


def remove_song(title, owner_username):
    try:
        # Connect to your MySQL database
        owner_id = get_id_from_username(owner_username)
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        select_query = """
            SELECT mp3_file_path, thumbnail_path FROM songs
            WHERE title = ? AND owner_id = ?
        """
        cursor.execute(select_query, (title, owner_id))
        result = cursor.fetchone()
        if result:
            mp3_file_path, thumbnail_path = result

            # Construct the SQL query to delete a song from the table
            delete_query = """
                DELETE FROM songs
                WHERE title = ? AND owner_id = ?
            """

            # Execute the SQL query with the song data
            cursor.execute(delete_query, (title, owner_id))

            # Commit the transaction
            connection.commit()

            print("Song removed successfully!")

            # Delete the associated song files
            if mp3_file_path and not check_path_exists_in_db(mp3_file_path):
                os.remove(mp3_file_path)
                print("Song file deleted successfully.")
            if thumbnail_path and not check_path_exists_in_db(thumbnail_path):
                os.remove(thumbnail_path)
                print("Thumbnail file deleted successfully.")
        else:
            print("Song not found.")

    except Exception as error:
        print("Error while removing song from the table:", error)


def check_path_exists_in_db(path):
    try:
        # Connect to the database
        conn = connect_to_kevindb()
        cursor = conn.cursor()

        # Define the tables and columns to check
        tables_columns = [
            ('sign_up_table', 'profile_pic_path'),
            ('songs', 'mp3_file_path'),
            ('messages', 'message_content_path'),
            ('songs', 'thumbnail_path'),
            ('my_groups', 'group_image_path')
        ]

        # Iterate over each table and column
        for table, column in tables_columns:
            # Execute a SQL query to check if the path exists in the specified column
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = ?", (path,))
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"Path '{path}' exists in table '{table}' column '{column}'")
                return True

        # If the path does not exist in any column of any table
        print(f"Path '{path}' does not exist in any table column")
        return False

    except sqlite3.Error as e:
        print("Error checking path in database:", e)
        return None

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()


def get_path_by_hash(file_hash):
    # List of tables and columns to check
    tables_columns = [
        ('sign_up_table', 'profile_pic_path', 'profile_pic_hash'),
        ('songs', 'mp3_file_path', 'mp3_file_hash'),
        ('messages', 'message_content_path', 'message_content_hash'),
        ('songs', 'thumbnail_path', 'thumbnail_hash'),
        ('my_groups', 'group_image_path', 'group_image_hash')
    ]

    try:
        # Connect to the database
        conn = connect_to_kevindb()
        cursor = conn.cursor()

        # Iterate over each table and column to find the file hash
        for table, path_column, hash_column in tables_columns:
            query = f"SELECT {path_column} FROM {table} WHERE {hash_column} = ?"
            cursor.execute(query, (file_hash,))
            row = cursor.fetchone()
            if row:
                return row[0]

        # If no match is found, return None
        return None

    except sqlite3.Error as e:
        print("Error checking file hash in database:", e)
        return None

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()


def add_song(title, mp3_file_bytes, owner_username, duration, thumbnail_photo_bytes):
    try:
        # Connect to your MySQL database
        owner_id = get_id_from_username(owner_username)
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        insert_query = """
            INSERT INTO songs (title, mp3_file_path, mp3_file_hash, owner_id, duration, timestamp, thumbnail_path, thumbnail_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        # Generate unique filenames
        folder_path = files_folder_path
        mp3_file_name = generate_random_filename(24)
        mp3_file_path = os.path.join(folder_path, mp3_file_name)

        thumbnail_photo_name = generate_random_filename(24)
        thumbnail_photo_path = os.path.join(folder_path, thumbnail_photo_name)

        # Save files
        save_bytes_to_file(mp3_file_bytes, mp3_file_path)
        mp3_file_hash = hash_sha2_bytes(mp3_file_bytes)
        if thumbnail_photo_bytes is not None:
            save_bytes_to_file(thumbnail_photo_bytes, thumbnail_photo_path)
            thumbnail_photo_hash = hash_sha2_bytes(thumbnail_photo_bytes)
        else:
            thumbnail_photo_path = None
            thumbnail_photo_hash = None

        # Execute the SQL query with the song data
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M'))
        cursor.execute(insert_query, (title, mp3_file_path, mp3_file_hash, owner_id, duration, timestamp, thumbnail_photo_path, thumbnail_photo_hash))

        # Commit the transaction
        connection.commit()

        print("Song added successfully!")

    except Exception as error:
        print("Error while adding song to the table:", error)


def get_songs_by_owner(owner):
    try:
        # Connect to your MySQL database
        owner_id = get_id_from_username(owner)
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        # Construct the SQL query to select songs by owner_id
        select_query = """
            SELECT title, mp3_file_path, duration, timestamp, thumbnail_path
            FROM songs
            WHERE owner_id = ?
        """

        # Execute the SQL query with the owner_id parameter
        cursor.execute(select_query, (owner_id,))

        # Fetch all rows
        songs_data = cursor.fetchall()

        # Prepare a list to store song information dictionaries
        songs = []

        # Iterate over the fetched rows
        for song_data in songs_data:
            # Extract song data from the row
            title, mp3_file_path, duration, timestamp, thumbnail_path = song_data
            timestamp_datetime = datetime.fromisoformat(timestamp)

            # Create a dictionary to store song information
            thumbnail_bytes = file_to_bytes(thumbnail_path)
            song_info = {
                "title": title,
                "audio_duration": duration,
                "timestamp": timestamp_datetime.strftime("%Y-%m-%d"),  # Convert timestamp to string
                "thumbnail_bytes": thumbnail_bytes
            }

            # Append the song information dictionary to the list
            songs.append(song_info)

        return songs

    except Exception as error:
        print("Error while retrieving songs by owner_id:", error)
        return []


def get_song_by_index_and_owner(owner, index):
    try:
        # Connect to your MySQL database
        owner_id = get_id_from_username(owner)
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        select_query = """
            SELECT title, mp3_file_path, duration, timestamp, thumbnail_path
            FROM songs
            WHERE owner_id = ?
            LIMIT 1 OFFSET ?
        """

        # Execute the SQL query with the owner_id and index parameters
        cursor.execute(select_query, (owner_id, index))

        # Fetch the row
        song_data = cursor.fetchone()

        if song_data:
            # Extract song data from the row
            title, mp3_file_path, duration, timestamp, thumbnail_path = song_data
            timestamp = datetime.fromisoformat(timestamp)
            # Create a dictionary to store song information
            mp3_bytes = file_to_bytes(mp3_file_path)
            thumbnail_bytes = file_to_bytes(thumbnail_path)
            song_info = {
                "title": title,
                "audio_bytes": mp3_bytes,
                "audio_duration": duration,
                "timestamp": timestamp.strftime("%Y-%m-%d"),  # Convert timestamp to string
                "thumbnail_bytes": thumbnail_bytes
            }

            return song_info
        else:
            # No song found at the specified index for the owner_id
            return None

    except Exception as error:
        print("Error while retrieving song by index and owner_id:", error)
        return None


def get_song_by_title(title):
    try:
        # Connect to your MySQL database
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        select_query = """
            SELECT title, mp3_file_path, duration, timestamp, thumbnail_path
            FROM songs
            WHERE title = ?
        """

        # Execute the SQL query with the owner_id and title parameters
        cursor.execute(select_query, (title,))

        # Fetch the row
        song_data = cursor.fetchone()

        if song_data:
            # Extract song data from the row
            title, mp3_file_path, duration, timestamp, thumbnail_path = song_data
            timestamp = datetime.fromisoformat(timestamp)
            # Create a dictionary to store song information
            mp3_bytes = file_to_bytes(mp3_file_path)
            thumbnail_bytes = file_to_bytes(thumbnail_path)
            song_info = {
                "title": title,
                "audio_bytes": mp3_bytes,
                "audio_duration": duration,
                "timestamp": timestamp.strftime("%Y-%m-%d"),  # Convert timestamp to string
                "thumbnail_bytes": thumbnail_bytes
            }

            return song_info
        else:
            # No song found with the specified title for the owner_id
            return None

    except Exception as error:
        print("Error while retrieving song by user and title:", error)
        return None


def get_user_settings(username):
    try:
        # Connect to the database
        user_id = get_id_from_username(username)
        db_connection = connect_to_kevindb()

        # Create a cursor object to execute SQL queries
        cursor = db_connection.cursor()
        # cursor.row_factory = sqlite3.Row
        # Define the table name
        table_name = "settings_table"

        # Define the SQL SELECT statement to retrieve settings for the given user_id
        select_query = f"SELECT volume, output_device, input_device, camera_device_index, font_size" \
                       f", font, theme_color, censor_data, private_account, push_to_talk_bind, two_factor_auth FROM {table_name} WHERE user_id = ?"

        # Execute the SELECT statement with parameterized values
        cursor.execute(select_query, (user_id,))

        # Fetch all settings rows for the given user_id
        user_settings = cursor.fetchall()[0]



        # Close the cursor and database connection
        cursor.close()
        db_connection.close()

        if user_settings:
            # Extract column names from the cursor description
            column_names = [description[0] for description in cursor.description]

            # Create a dictionary mapping column names to row values
            user_settings_dict = {column_names[i]: user_settings[i] for i in range(len(column_names))}

            return user_settings_dict
        else:
            return None



    except Exception as e:
        print(f"Error: {e}")
        return None


# settings names: volume, output_device, input_device, camera_device_index
# font_size, font, theme_color, censor_data, private_account, push_to_talk_key, two_factor_auth


def change_user_setting(user_id, setting_name, new_value):
    try:
        # Connect to the database
        db_connection = connect_to_kevindb()
        # Create a cursor object to execute SQL queries
        cursor = db_connection.cursor()

        # Define the table name
        table_name = "settings_table"

        # Define the SQL UPDATE statement to change the setting for the given user_id
        update_query = f"UPDATE {table_name} SET {setting_name} = ? WHERE user_id = ?"

        # Execute the UPDATE statement with parameterized values
        cursor.execute(update_query, (new_value, user_id))

        # Commit the transaction
        db_connection.commit()

        # Close the cursor and database connection
        cursor.close()
        db_connection.close()

    except sqlite3.Error as e:
        print(f"Error: {e}")
        print("Failed to change setting.")


def get_id_from_username(username):
    # Connect to the MySQL database
    conn = connect_to_kevindb()
    cursor = conn.cursor()

    try:
        # Execute a query to retrieve the ID based on the username
        cursor.execute("SELECT id FROM sign_up_table WHERE username = ?", (username,))
        row = cursor.fetchone()  # Fetch the first row

        if row:
            # If a row is found, return the ID
            return row[0]
        else:
            # If no row is found, return None
            return None
    except sqlite3.Error as e:
        # Handle any errors that occur during the execution of the query
        print("Error retrieving ID:", e)
        return None
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()


def get_email_by_username(username):
    try:
        # Establish a connection to the database
        connection = connect_to_kevindb()

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        # Define the SQL query to retrieve the email by username
        query = "SELECT email FROM sign_up_table WHERE username = ?"

        # Execute the query with the provided username as a parameter
        cursor.execute(query, (username,))

        # Fetch the result (email) from the query
        result = cursor.fetchone()

        if result:
            email = result[0]  # Extract the email from the result tuple
            return email
        else:
            return None  # Username not found or email is NULL

    except sqlite3.Error as error:
        print(f"Error retrieving email for username '{username}': {error}")
        return None

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()


def get_username_from_id(user_id):
    try:
        # Connect to the MySQL database
        conn = connect_to_kevindb()
        cursor = conn.cursor()

        # Execute a query to retrieve the username based on the user ID
        cursor.execute("SELECT username FROM sign_up_table WHERE id = ?", (user_id,))
        row = cursor.fetchone()  # Fetch the first row

        if row:
            # If a row is found, return the username
            return row[0]
        else:
            # If no row is found, return None
            return None
    except sqlite3.Error as e:
        # Handle any errors that occur during the execution of the query
        print("Error retrieving username:", e)
        return None
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()


def update_settings_by_dict(username, settings_dict):
    user_id = get_id_from_username(username)
    volume, output_device_name, input_device_name, camera_index, font_size, font_text, background_color, censor_data, is_private_account, push_to_talk_key, two_factor_authentication = unpack_settings(
        settings_dict)
    change_volume(user_id, volume)
    change_output_device(user_id, output_device_name)
    change_input_device(user_id, input_device_name)
    change_camera_device_index(user_id, camera_index)
    change_font_size(user_id, font_size)
    change_font(user_id, font_text)
    change_theme_color(user_id, background_color)
    change_censor_data(user_id, censor_data)
    change_private_account(user_id, is_private_account)
    change_push_to_talk_bind(user_id, push_to_talk_key)
    change_2fa_enabled(user_id, two_factor_authentication)
    print(f"updated whole settings for user_id {user_id}")


def change_volume(user_id, new_volume):
    change_user_setting(user_id, "volume", new_volume)


def change_output_device(user_id, new_output_device):
    change_user_setting(user_id, "output_device", new_output_device)


def change_input_device(user_id, new_input_device):
    change_user_setting(user_id, "input_device", new_input_device)


def change_camera_device_index(user_id, new_camera_device_index):
    change_user_setting(user_id, "camera_device_index", new_camera_device_index)


def change_font_size(user_id, new_font_size):
    change_user_setting(user_id, "font_size", new_font_size)


def change_font(user_id, new_font):
    change_user_setting(user_id, "font", new_font)


def change_theme_color(user_id, new_theme_color):
    change_user_setting(user_id, "theme_color", new_theme_color)


def change_censor_data(user_id, new_censor_data):
    change_user_setting(user_id, "censor_data", new_censor_data)


def change_private_account(user_id, new_private_account):
    change_user_setting(user_id, "private_account", new_private_account)


def change_push_to_talk_bind(user_id, new_push_to_talk_bind):
    change_user_setting(user_id, "push_to_talk_bind", new_push_to_talk_bind)


def change_2fa_enabled(user_id, new_2fa_value):
    change_user_setting(user_id, "two_factor_auth", new_2fa_value)


def decode_base64(message):
    message_content = base64.b64decode(message)
    return message_content


def generate_random_salt(length=8):
    salt = binascii.hexlify(os.urandom(length)).decode('utf-8')
    return salt


def generate_token(length=16):
    """
    Generate a secure random token.

    Parameters:
    - length (int): Length of the token (default is 32 characters).

    Returns:
    - str: The generated token.
    """
    return secrets.token_hex(length // 2)


def hash_sha2(string):
    # Create a new SHA-256 hash object
    sha256_hash = hashlib.sha256()

    # Update the hash object with the bytes of the string
    sha256_hash.update(string.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    hashed_string = sha256_hash.hexdigest()

    return hashed_string


def retrieve_salt_by_username(username):
    try:
        # Establish a connection to the database
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Execute the SELECT query to retrieve the salt
        query = f"SELECT salt FROM sign_up_table WHERE username = '{username}'"
        cursor.execute(query)

        # Fetch the salt
        result = cursor.fetchone()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        # Return the salt (or None if user not found)
        return result[0] if result else None

    except sqlite3.Error as e:
        print(f"Error: {e}")
        return None


def retrieve_user_id_by_username(username):
    try:
        # Establish a connection to the database
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Execute the SELECT query to retrieve the salt
        query = f"SELECT id FROM sign_up_table WHERE username = '{username}'"
        cursor.execute(query)

        # Fetch the salt
        result = cursor.fetchone()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        # Return the salt (or None if user not found)
        return result[0] if result else None

    except sqlite3.Error as e:
        print(f"Error: {e}")
        return None


def login(username, password):
    try:
        # Create a connection
        connection = connect_to_kevindb()
        salt_by_user = retrieve_salt_by_username(username)
        if salt_by_user is None:
            return False
        hashed_password_salt = hash_sha2(password + salt_by_user)
        hashed_password_salt_pepper = hashed_password_salt + pepper
        # Create a cursor
        cursor = connection.cursor()

        # Define the table name
        table_name = "sign_up_table"

        # Define the SQL SELECT statement to check login credentials with case sensitivity
        select_query = f"""
            SELECT * FROM {table_name}
            WHERE  username = ? AND  password = ?
        """

        # Execute the SELECT statement with the provided username and password
        cursor.execute(select_query, (username, hashed_password_salt_pepper))

        # Fetch the result (fetchone() returns None if no matching row is found)
        result = cursor.fetchone()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        # Return True if the login credentials are valid, False if they are not
        return result is not None

    except sqlite3.Error as e:
        print(f"Error: {e}")
        return False


def username_exists(username):
    try:
        # Create a connection
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Define the table name
        table_name = "sign_up_table"

        # Define the SQL SELECT statement to check if the username exists
        select_query = f"SELECT * FROM {table_name} WHERE  username = ?"

        # Execute the SELECT statement with the username value
        cursor.execute(select_query, (username,))

        # Fetch the result (fetchone() returns None if no matching row is found)
        result = cursor.fetchone()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        # Return True if the username exists, False if it doesn't
        return result is not None

    except sqlite3.Error as e:
        print(f"Error: {e}")
        return False


def user_exists_with_email(username, email):
    try:
        # Create a connection
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Define the table name
        table_name = "sign_up_table"

        # Define the SQL SELECT statement to check if the username and email exist
        select_query = f"SELECT * FROM {table_name} WHERE  username = ? AND email = ?"

        # Execute the SELECT statement with the username and email values
        cursor.execute(select_query, (username, email))

        # Fetch the result (fetchone() returns None if no matching row is found)
        result = cursor.fetchone()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        # Return True if the username and email exist, False if they don't
        return result is not None
    except Exception as e:
        # Handle exceptions (print, log, or raise as needed)
        print(f"Error: {e}")
        return False


def check_security_token(token):
    try:
        # Establish a connection to the database
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        # Define the table name
        table_name = "sign_up_table"

        # Define the SQL SELECT statement to check if the token exists
        select_query = f"SELECT username FROM {table_name} WHERE security_token = ?"

        # Execute the SELECT statement with the parameterized value
        cursor.execute(select_query, (token,))

        # Fetch the result
        result = cursor.fetchone()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        if result:
            # Token exists, return the associated username
            return result[0]
        else:
            # Token doesn't exist, return False
            return False

    except sqlite3.Error as e:
        print(f"Error: {e}")
        return False


def get_security_token(username):
    try:
        # Establish a connection to the database
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        # Define the table name
        table_name = "sign_up_table"

        # Define the SQL SELECT statement to get the security token by username
        select_query = f"SELECT security_token FROM {table_name} WHERE username = ?"

        # Execute the SELECT statement with the parameterized value
        cursor.execute(select_query, (username,))

        # Fetch the result
        result = cursor.fetchone()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        if result:
            # Return the security token
            return result[0]
        else:
            # If username not found, return None or any other suitable value
            return None

    except sqlite3.Error as e:
        print(f"Error: {e}")
        return None


def update_security_token(username):
    try:
        # Establish a connection to the database
        connection = connect_to_kevindb()
        cursor = connection.cursor()
        new_token = generate_token()
        # Define the table name
        table_name = "sign_up_table"

        # Define the SQL UPDATE statement to update the security token by username
        update_query = f"UPDATE {table_name} SET security_token = ? WHERE username = ?"

        # Execute the UPDATE statement with the parameterized values
        cursor.execute(update_query, (new_token, username))

        # Commit the changes
        connection.commit()

        # Check if the update was successful
        if cursor.rowcount == 0:
            print(f"No user found with username: {username}")
            return False

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        # Return True if the update was successful
        return True

    except sqlite3.Error as e:
        print(f"Error: {e}")
        return False


def insert_user(username, password, email):
    try:
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        # Generate a random salt and hash the password with the salt
        salt = generate_random_salt()
        password_with_salt = password + salt
        hashed_password_with_salt = hash_sha2(password_with_salt)

        # Generate a security token
        security_token = generate_token()

        # Define the table name
        table_name = "sign_up_table"

        # Define the SQL INSERT statement with parameterized queries
        insert_query = f"INSERT INTO {table_name} (username, password, email, salt, security_token) VALUES (?, ?, ?, ?, ?)"

        # Execute the INSERT statement with parameterized values
        cursor.execute(insert_query, (username, hashed_password_with_salt + pepper, email, salt, security_token))

        # Commit the changes to the database
        user_id = cursor.lastrowid
        connection.commit()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        print("User inserted successfully.")

        create_user_settings(user_id)

    except sqlite3.Error as e:
        print(f"Error: {e}")
        print("Failed to insert user.")


def update_profile_pic(username, profile_pic_encoded):
    try:
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        if profile_pic_encoded is not None:
            profile_pic = decode_base64(profile_pic_encoded)
        else:
            profile_pic = None

        table_name = "sign_up_table"

        update_query = f"SELECT profile_pic_path FROM {table_name} WHERE username = ?"

        # Execute the SELECT statement with the parameterized value
        cursor.execute(update_query, (username,))

        # Fetch the result
        result = cursor.fetchone()

        file_path = result[0]  # Extract the file path from the tuple

        table_name = "sign_up_table"

        if profile_pic is not None:
            folder_path = files_folder_path
            file_name = generate_random_filename(24)
            profile_pic_path = os.path.join(folder_path, file_name)
            save_bytes_to_file(profile_pic, profile_pic_path)
            profile_pic_hash = hash_sha2_bytes(profile_pic)
            update_query = f"UPDATE {table_name} SET profile_pic_path = ?, profile_pic_hash = ? WHERE username = ?"
        else:
            profile_pic_path = None
            profile_pic_hash = None
            update_query = f"UPDATE {table_name} SET profile_pic_path = ?, profile_pic_hash = ? WHERE username = ?"

        # Execute the INSERT statement with parameterized values
        cursor.execute(update_query, (profile_pic_path, profile_pic_hash, username))

        # Commit the changes to the database
        connection.commit()

        if file_path is not None and not check_path_exists_in_db(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"couldn't find file path {e}")

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

    except sqlite3.Error as e:
        print(f"Error: {e}")
        print("Failed to insert user.")


def get_profile_pic_by_name(username):
    try:
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        table_name = "sign_up_table"

        update_query = f"SELECT profile_pic_path FROM {table_name} WHERE username = ?"

        # Execute the SELECT statement with the parameterized value
        cursor.execute(update_query, (username,))

        # Fetch the result
        result = cursor.fetchone()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        if result:
            profile_pic_path = result[0]
            if profile_pic_path is None:
                return None
            else:
                profile_pic_bytes = file_to_bytes(profile_pic_path)
                return profile_pic_bytes
        else:
            # If username not found, return None or any other suitable value
            return None

    except sqlite3.Error as e:
        print(f"Error: {e}")


def change_password(username, new_password):
    try:
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        # Generate a new salt for the user
        new_salt = generate_random_salt()

        # Hash the new password with the new salt
        hashed_new_password = hash_sha2(new_password + new_salt)

        # Update the user's password and salt in the database
        update_password_query = "UPDATE sign_up_table SET password = ?, salt = ? WHERE username = ?"
        cursor.execute(update_password_query, (hashed_new_password + pepper, new_salt, username))

        # Commit the changes to the database
        connection.commit()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

    except sqlite3.Error as e:
        print(f"Error: {e}")
        print("Failed to change password.")


def is_table_exist(table_name):
    connection = connect_to_kevindb()

    cursor = connection.cursor()
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")

    # Fetch the result
    result = cursor.fetchone()

    # Return True if the table exists, False if it doesn't
    return result is not None


def add_message(sender_name, receiver_name, message_content, message_type, file_original_name):
    try:
        # Establish a connection to the MySQL server
        sender_id = get_id_from_username(sender_name)
        if receiver_name.startswith("("):
            group_name, receiver_id = gets_group_attributes_from_format(receiver_name)
            receiver_id = int(receiver_id) * -1
        else:
            receiver_id = get_id_from_username(receiver_name)
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        # SQL query to insert a message into the 'messages' table
        if message_type in basic_files_types:
            encoded_base64_bytes = message_content
            message_content = base64.b64decode(encoded_base64_bytes)
            folder_path = files_folder_path
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            file_name = generate_random_filename(24)
            file_path = os.path.join(folder_path, file_name)
            if os.path.exists(file_path):
                while os.path.exists(file_path):
                    file_name = generate_random_filename(24)
                    file_path = os.path.join(folder_path, file_name)
            save_file(message_content, file_path)
            sql_query = "INSERT INTO messages (sender_id, receiver_id, message_content_path, message_content_hash, type, file_name, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)"
            timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M'))
            file_hash = hash_sha2_bytes(message_content)
            data = (sender_id, receiver_id, file_path, file_hash, message_type, file_original_name, timestamp)
        else:
            sql_query = "INSERT INTO messages (sender_id, receiver_id, message_content, type, timestamp) VALUES (?, ?, ?, ?, ?)"
            timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M'))
            data = (sender_id, receiver_id, message_content, message_type, timestamp)

        # Execute the query
        cursor.execute(sql_query, data)

        # Commit changes to the database
        connection.commit()
    except Exception as e:
        print("Error in adding message:", e)

    finally:
        # Close the database connection
        cursor.close()
        connection.close()


def gets_group_attributes_from_format(group_format):
    if "(" not in group_format:
        return group_format, None
    else:
        parts = group_format.split(")")
        id = parts[0][1:]
        name = parts[1]
        return name, id


def get_last_amount_of_messages(sender_name, receiver_name, first_message_index, last_message_index):
    try:
        if first_message_index > last_message_index:
            print("wrong parameters")
            return []
        is_group_chat = receiver_name.startswith('(')

        if is_group_chat:
            _, group_id = gets_group_attributes_from_format(receiver_name)
            receiver_id = int(group_id) * -1
        else:
            sender_id = get_id_from_username(sender_name)
            receiver_id = get_id_from_username(receiver_name)

        # Connect to the database using a context manager
        connection = connect_to_kevindb()

        cursor = connection.cursor()

        limit = last_message_index - first_message_index + 1
        offset = first_message_index

        if is_group_chat:
            query = """
                SELECT IFNULL(message_content, message_content_path) AS content,
                       sender_id, timestamp, type, file_name 
                FROM messages 
                WHERE receiver_id = ? ORDER BY message_id DESC LIMIT ? OFFSET ? 
            """
            cursor.execute(query, (receiver_id, limit, offset))
        else:
            query = """
                SELECT IFNULL(message_content, message_content_path) AS content,
                       sender_id, timestamp, type, file_name 
                FROM messages 
                WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?) ORDER BY message_id DESC LIMIT ? OFFSET ?
            """
            cursor.execute(query, (sender_id, receiver_id, receiver_id, sender_id, limit, offset))

        # Fetch all messages within the specified range
        messages_new_to_old = cursor.fetchall()

        # messages = messages_new_to_old[first_message_index:last_message_index + 1]
        formatted_messages = format_messages(messages_new_to_old)
        return formatted_messages

    except sqlite3.Error as err:
        print(f"Error retrieving messages: {err}")
        return []


def get_username_for_senders(message_list):
    sender_ids = set(message['sender_id'] for message in message_list)
    sender_id_list = list(sender_ids)

    # Fetch usernames for all unique sender_ids in one query
    sender_id_to_name = {}
    if sender_id_list:
        try:
            conn = connect_to_kevindb()
            cursor = conn.cursor()

            # Construct the query to fetch usernames for sender_ids
            placeholders = ','.join('?' for _ in sender_id_list)
            query = f"SELECT id, username FROM sign_up_table WHERE id IN ({placeholders})"
            cursor.execute(query, sender_id_list)
            result = cursor.fetchall()

            for row in result:
                sender_id_to_name[row[0]] = row[1]

        except sqlite3.Error as err:
            print(f"Error retrieving sender usernames: {err}")

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return sender_id_to_name


def format_messages(messages):
    # sender_id_to_name = get_username_for_senders(messages)
    formatted_messages = []

    for message in messages:
        content, sender_id, timestamp, message_type, file_name = message

        if message_type != "string":
            content_bytes = file_to_bytes(content)
            content = base64.b64encode(content_bytes).decode('utf-8')
        sender_name = get_username_from_id(sender_id)
        formatted_message = {
            "content": content,
            "sender_id": sender_name,
            "timestamp": timestamp,
            "message_type": message_type,
            "file_name": file_name
        }
        formatted_messages.append(formatted_message)

    return formatted_messages


def are_friends(username, friend_username):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    username_id = get_id_from_username(username)
    friend_username_id = get_id_from_username(friend_username)
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if the users are already friends
    query = f"SELECT friendship_status FROM friends WHERE (user_id = '{username_id}' AND friend_user_id = '{friend_username_id}') OR (user_id = '{friend_username_id}' AND friend_user_id = '{username_id}')"
    cursor.execute(query)
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    # Return True if they are friends, False otherwise
    return result and result[0] == 'accepted'


def is_active_request(username, friend_username):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    username_id = get_id_from_username(username)
    friend_username_id = get_id_from_username(friend_username)
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if the users are already friends
    query = f"SELECT friendship_status FROM friends WHERE (user_id = '{username_id}' AND friend_user_id = '{friend_username_id}')"
    cursor.execute(query)
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    # Return True if they are pending, False otherwise
    return result and result[0] == 'pending'


def send_friend_request(username, friend_username):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    username_id = get_id_from_username(username)
    friend_username_id = get_id_from_username(friend_username)
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if a friend request already exists
    query = f"SELECT id FROM friends WHERE user_id = '{username_id}' AND friend_user_id = '{friend_username_id}' AND friendship_status = 'pending'"
    cursor.execute(query)
    existing_request = cursor.fetchone()

    if existing_request:
        print("Friend request already sent.")
    else:
        # Send a new friend request
        insert_query = f"INSERT INTO friends (user_id, friend_user_id, friendship_status) VALUES ('{username_id}', '{friend_username_id}', 'pending')"
        cursor.execute(insert_query)
        connection.commit()
        print("Friend request sent successfully.")

    cursor.close()
    connection.close()


def handle_friend_request(username, friend_username, accept):

    username_id = get_id_from_username(username)
    friend_username_id = get_id_from_username(friend_username)
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if the friend request exists
    query = f"SELECT id FROM friends WHERE (user_id = '{username_id}' AND friend_user_id = '{friend_username_id}') " \
            f"OR (user_id = '{friend_username_id}' AND friend_user_id = '{username_id}') AND friendship_status = 'pending'"
    cursor.execute(query)
    request_id = cursor.fetchone()

    if request_id:
        # Update the friendship status based on the 'accept' parameter
        new_status = 'accepted' if accept else 'rejected'
        update_query = f"UPDATE friends SET friendship_status = '{new_status}' WHERE id = {request_id[0]}"
        cursor.execute(update_query)
        connection.commit()
    else:
        print("Friend request not found.")

    cursor.close()
    connection.close()


def remove_friend(username, friend_username):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    username_id = get_id_from_username(username)
    friend_username_id = get_id_from_username(friend_username)
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if the friendship exists
    query = f"SELECT id FROM friends WHERE (user_id = '{username_id}' AND friend_user_id = '{friend_username_id}') OR (user_id = '{friend_username_id}' AND friend_user_id = '{username_id}') AND friendship_status = 'accepted'"
    cursor.execute(query)
    friendship_id = cursor.fetchone()

    if friendship_id:
        # Delete the row corresponding to the friendship
        delete_query = f"DELETE FROM friends WHERE id = {friendship_id[0]}"
        cursor.execute(delete_query)
        connection.commit()
        print("Friend removed successfully.")
    else:
        print("Friendship not found.")

    cursor.close()
    connection.close()


def remove_friend_request(username, friend_username):
    username_id = get_id_from_username(username)
    friend_username_id = get_id_from_username(friend_username)
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if the friendship exists
    query = f"SELECT id FROM friends WHERE (user_id = '{username_id}' AND friend_user_id = '{friend_username_id}') OR (user_id = '{friend_username_id}' AND friend_user_id = '{username_id}')"
    cursor.execute(query)
    friendship_id = cursor.fetchone()

    if friendship_id:
        # Delete the row corresponding to the friendship
        delete_query = f"DELETE FROM friends WHERE id = {friendship_id[0]}"
        cursor.execute(delete_query)
        connection.commit()
        print("Friend removed successfully.")
    else:
        print("Friendship not found.")

    cursor.close()
    connection.close()


def get_friend_requests(username):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    username_id = get_id_from_username(username)
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Retrieve friend requests for the given username
    query = f"SELECT user_id FROM friends WHERE friend_user_id = '{username_id}' AND friendship_status = 'pending'"
    cursor.execute(query)
    friend_requests = cursor.fetchall()

    cursor.close()
    connection.close()

    # Extract the usernames from the result
    friend_requests_list_id = [request[0] for request in friend_requests]
    friend_requests_list = []
    for friend_id in friend_requests_list_id:
        friend_requests_list.append(get_username_from_id(friend_id))
    return friend_requests_list


def get_user_friends(username):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    username_id = get_id_from_username(username)
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Retrieve friends for the given username
    query = """
        SELECT 
            CASE
                WHEN friend_user_id = ? THEN user_id
                ELSE friend_user_id
            END AS user_or_friend_id
        FROM friends
        WHERE 
            (user_id = ? OR friend_user_id = ?)
            AND friendship_status = 'accepted';
    """
    cursor.execute(query, (username_id, username_id, username_id))
    friends = cursor.fetchall()

    cursor.close()
    connection.close()

    # Extract the friend usernames from the result
    friends_list_of_id = [friend[0] for friend in friends]
    friends_list = []
    for friend_id in friends_list_of_id:
        friends_list.append(get_username_from_id(friend_id))
    return friends_list


def add_chat_to_user(username, new_chat_name):
    try:
        # Connect to your MySQL database (replace with your own connection details)
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the current chats_list for the user
        cursor.execute("SELECT chats_list FROM sign_up_table WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result:
            current_chats_list_json = result[0]

            # If the current_chats_list_json is None, set it to an empty list
            current_chats_list = json.loads(current_chats_list_json) if current_chats_list_json else []
            if not new_chat_name.startswith("("):
                new_chat_name_id = get_id_from_username(new_chat_name)
                if new_chat_name_id not in current_chats_list:
                    current_chats_list.append(new_chat_name_id)
            else:
                current_chats_list.append(new_chat_name)

            # Convert the updated_chats_list to JSON format
            updated_chats_list_json = json.dumps(current_chats_list)

            # Update the chats_list for the user
            cursor.execute("UPDATE sign_up_table SET chats_list = ? WHERE username = ?",
                           (updated_chats_list_json, username))

            # Commit the changes
            connection.commit()

            print(f"Added '{new_chat_name}' to the chats_list for user '{username}'.")
        else:
            print(f"No user found with username '{username}'.")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def update_group_image(group_id, image_bytes):
    try:
        # Establish a connection to the MySQL database
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        table_name = "my_groups"

        get_path = f"SELECT group_image_path FROM {table_name} WHERE group_id = ?"

        # Execute the SELECT statement with the parameterized value
        cursor.execute(get_path, (group_id,))

        # Fetch the result
        result = cursor.fetchone()

        if result:
            image_path = result[0]  # Extract the file path from the tuple

        if image_bytes is None:
            group_pic_path = None
            group_pic_hash = None
        else:
            folder_path = files_folder_path
            file_name = generate_random_filename(24)
            group_pic_path = os.path.join(folder_path, file_name)
            save_bytes_to_file(image_bytes, group_pic_path)
            group_pic_hash = hash_sha2_bytes(image_bytes)
            print("saved bytes to image")

        # Prepare the UPDATE query
        update_query = """
            UPDATE my_groups
            SET group_image_path = ?, group_image_hash = ?
            WHERE group_id = ?
        """

        # Execute the query
        cursor.execute(update_query, (group_pic_path, group_pic_hash, group_id))
        connection.commit()

        if result:
            if image_path and not check_path_exists_in_db(image_path):
                os.remove(image_path)

        print(f"Group image updated successfully for group ID: {group_id}")

    except Exception as e:
        print(f"Error updating group image: {e}")


def get_group_image_by_id(group_id):
    try:
        # Establish a connection to the MySQL database
        connection = connect_to_kevindb()

        select_query = """
            SELECT group_image_path
            FROM my_groups
            WHERE group_id = ?
        """

        # Execute the query
        cursor = connection.cursor()
        cursor.execute(select_query, (group_id,))
        result = cursor.fetchone()

        if result:
            path = result[0]
            if path is None:
                return None
            else:
                image_bytes = file_to_bytes(path)
                return image_bytes
    except Exception as e:
        print(f"Error getting group image: {e}")

    finally:
        # Close the database connection

        cursor.close()
        connection.close()


def get_user_chats(username):
    try:
        # Connect to your MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the current chats_list for the user
        cursor.execute("SELECT chats_list FROM sign_up_table WHERE username = ?", (username,))
        result = cursor.fetchone()

        # If the result is None or empty, return an empty list
        if not result or not result[0]:
            return []

        # Convert the chats_list JSON to a Python list
        current_chats_list = json.loads(result[0])
        chat_list_names = []
        for chat in current_chats_list:
            if isinstance(chat, int):
                chat_list_names.append(get_username_from_id(chat))
            else:
                _, group_id = gets_group_attributes_from_format(chat)
                group_name = get_group_name_by_id(int(group_id))
                chat_list_names.append(f"({group_id}){group_name}")
        sorted_chats_list = sort_chat_list(chat_list_names, username)
        return sorted_chats_list

    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def sort_chat_list(chats_list, username):
    # Connect to the MySQL database
    conn = connect_to_kevindb()

    cursor = conn.cursor()

    try:
        # Iterate over each chat in the chat list
        chat_timestamps = {}
        for index, chat in enumerate(chats_list):
            # Retrieve the timestamp of the last message in the conversation
            if chat.startswith("("):
                _, group_id = gets_group_attributes_from_format(chat)
                receiver_id = int(group_id) * -1
                cursor.execute("""
                    SELECT MAX(timestamp) AS last_message_timestamp
                    FROM messages
                    WHERE sender_id = ? OR receiver_id = ?
                """, (receiver_id, receiver_id))
            else:
                username_id = get_id_from_username(username)
                chat_id = get_id_from_username(chat)
                cursor.execute("""
                    SELECT MAX(timestamp) AS last_message_timestamp
                    FROM messages
                    WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
                """, (chat_id, username_id, username_id, chat_id))
            row = cursor.fetchone()
            if row and row[0]:
                last_message_timestamp = datetime.fromisoformat(row[0])  # Convert SQLite timestamp to datetime

            else:
                # If no message is found, set last_message_timestamp to a default value
                last_message_timestamp = datetime(1970, 1, 1)  # Or any other default value you prefer

            chat_timestamps[chat] = last_message_timestamp

        # Sort the chat list based on the timestamp of the last message in each conversation
        sorted_chats = sorted(chat_timestamps, key=chat_timestamps.get, reverse=True)

        return sorted_chats
    except sqlite3.Error as e:
        # Handle any errors that occur during the execution of the query
        print("Error sorting chat list:", e)
        return None
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()


def remove_chat_from_user(username, chat_to_remove):
    try:
        # Connect to your MySQL database (replace with your own connection details)
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the current chats_list for the user
        cursor.execute("SELECT chats_list FROM sign_up_table WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result:
            current_chats_list_json = result[0]

            # If the current_chats_list_json is None, set it to an empty list
            current_chats_list = json.loads(current_chats_list_json) if current_chats_list_json else []

            # Remove the specified chat from the current_chats_list
            if not chat_to_remove.startswith("("):
                chat_to_remove_id = get_id_from_username(chat_to_remove)
                if chat_to_remove_id in current_chats_list:
                    current_chats_list.remove(chat_to_remove_id)

                    # Convert the updated_chats_list to JSON format
                    updated_chats_list_json = json.dumps(current_chats_list)

                    # Update the chats_list for the user
                    cursor.execute("UPDATE sign_up_table SET chats_list = ? WHERE username = ?",
                                   (updated_chats_list_json, username))

                    # Commit the changes
                    connection.commit()

                    print(f"Removed '{chat_to_remove}' from the chats_list for user '{username}'.")
                else:
                    print(f"Chat '{chat_to_remove}' not found in the chats_list for user '{username}'.")
            else:
                # means chat is group
                group_to_remove_id = int(chat_to_remove.split(")")[0][1:])
                for chat in current_chats_list:
                    if isinstance(chat, str):
                        group_id = int(chat.split(")")[0][1:])
                        if group_id == group_to_remove_id:
                            current_chats_list.remove(chat)

                            updated_chats_list_json = json.dumps(current_chats_list)
                            cursor.execute("UPDATE sign_up_table SET chats_list = ? WHERE username = ?",
                                           (updated_chats_list_json, username))

                            # Commit the changes
                            connection.commit()
                            print(f"Removed '{chat}' from the chats_list for user '{username}'.")
                            break
        else:
            print(f"No user found with username '{username}'.")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_blocked_users(username):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object
        cursor = connection.cursor()

        # Retrieve the blocked_list for the user
        cursor.execute("SELECT blocked_list FROM sign_up_table WHERE username = ?", (username,))
        result = cursor.fetchone()

        # If no result or blocked_list is empty, return an empty list
        if not result or not result[0]:
            return []

        # Convert the blocked_list JSON to a Python list
        blocked_users_id = json.loads(result[0])
        blocked_users = []
        for user_id in blocked_users_id:
            blocked_users.append(get_username_from_id(user_id))

        return blocked_users

    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def block_user(username, user_to_block):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object
        cursor = connection.cursor()

        # Retrieve the current blocked_list for the user
        cursor.execute("SELECT blocked_list FROM sign_up_table WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result:
            blocked_list_json = result[0]

            # If the blocked_list_json is None, set it to an empty list
            blocked_list = json.loads(blocked_list_json) if blocked_list_json else []

            # Add the user_to_block to the blocked_list
            user_to_block_id = get_id_from_username(user_to_block)
            blocked_list.append(user_to_block_id)

            # Convert the updated blocked_list to JSON format
            updated_blocked_list_json = json.dumps(blocked_list)

            # Update the blocked_list for the user
            cursor.execute("UPDATE sign_up_table SET blocked_list = ? WHERE username = ?",
                           (updated_blocked_list_json, username))

            # Commit the changes
            connection.commit()

            print(f"Blocked user '{user_to_block}' for user '{username}'.")
        else:
            print(f"No user found with username '{username}'.")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def unblock_user(username, user_to_unblock):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object
        cursor = connection.cursor()

        # Retrieve the current blocked_list for the user
        cursor.execute("SELECT blocked_list FROM sign_up_table WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result:
            blocked_list_json = result[0]

            # If the blocked_list_json is None, set it to an empty list
            blocked_list = json.loads(blocked_list_json) if blocked_list_json else []

            # Remove the user_to_unblock from the blocked_list if it exists
            user_to_unblock_id = get_id_from_username(user_to_unblock)
            if user_to_unblock_id in blocked_list:
                blocked_list.remove(user_to_unblock_id)

                # Convert the updated blocked_list to JSON format
                updated_blocked_list_json = json.dumps(blocked_list)

                # Update the blocked_list for the user
                cursor.execute("UPDATE sign_up_table SET blocked_list = ? WHERE username = ?",
                               (updated_blocked_list_json, username))

                # Commit the changes
                connection.commit()

                print(f"Unblocked user '{user_to_unblock}' for user '{username}'.")
            else:
                print(f"User '{user_to_unblock}' not found in the blocked list for user '{username}'.")

        else:
            print(f"No user found with username '{username}'.")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def create_group(group_name, group_manager, group_members_list=None):
    new_chat_name = ""
    group_id = None

    try:
        # Connect to the SQLite database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Convert group_members_list to a JSON-formatted string
        group_members_id_list = []
        for member in group_members_list:
            group_members_id_list.append(get_id_from_username(member))
        group_members_json = json.dumps(group_members_id_list) if group_members_list else None

        # Insert the group into the 'my_groups' table
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M'))
        group_manager_id = get_id_from_username(group_manager)
        cursor.execute("INSERT INTO my_groups (group_name, group_manager, group_members_list, creation_date) VALUES (?, ?, ?, ?)",
                       (group_name, group_manager_id, group_members_json, timestamp))

        # Get the last inserted row id (equivalent to LAST_INSERT_ID() in MySQL)
        group_id = cursor.lastrowid
        new_chat_name = f"({group_id}){group_name}"

        # Commit the changes
        connection.commit()

        print(f"Group '{group_name}' created successfully!")

        # Add the new chat to each member's chat list
        if group_members_list:
            for member in group_members_list:
                add_chat_to_user(member, new_chat_name)

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

        # Return the new chat name and group ID
        return new_chat_name, group_id


def change_group_manager(group_id, new_manager):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        new_manager_id = get_id_from_username(new_manager)
        # Update the manager for the specified group
        cursor.execute("UPDATE my_groups SET group_manager = ? WHERE group_id = ?", (new_manager_id, group_id))

        # Commit the changes
        connection.commit()

        print(f"Manager for group (ID: {group_id}) changed to '{new_manager}' successfully!")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_group_name_by_id(group_id):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the group_name for the specified group_id
        cursor.execute("SELECT group_name FROM my_groups WHERE group_id = ?", (group_id,))
        group_name_result = cursor.fetchone()

        # Check if the group exists
        if group_name_result:
            group_name = group_name_result[0]
            return group_name
        else:
            print(f"Group with ID {group_id} not found.")
            return None

    except sqlite3.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def remove_group_member(group_id, group_member):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the current group_members_list for the specified group_id
        cursor.execute("SELECT group_members_list FROM my_groups WHERE group_id = ?", (group_id,))
        row = cursor.fetchone()[0]
        current_members_list = json.loads(row) if row else []

        # Remove the group member from the list
        group_member_id = get_id_from_username(group_member)
        if group_member_id in current_members_list:
            current_members_list.remove(group_member_id)

            # Update the group_members_list for the specified group_id
            cursor.execute("UPDATE my_groups SET group_members_list = ? WHERE group_id = ?",
                           (json.dumps(current_members_list), group_id))

            # Commit the changes
            connection.commit()

            print(f"Group member '{group_member}' removed from group (ID: {group_id}) successfully!")
        else:
            print(f"Group member '{group_member}' not found in group (ID: {group_id}). No changes made.")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_group_members(group_id):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the group_members_list for the specified group_id
        cursor.execute("SELECT group_members_list FROM my_groups WHERE group_id = ?", (group_id,))
        members_list_json = cursor.fetchone()

        # Check if the group exists and has members
        if members_list_json:
            members_list_id = json.loads(members_list_json[0])
            members_list = []
            for id in members_list_id:
                members_list.append(get_username_from_id(id))
            return members_list
        else:
            print(f"Group with ID {group_id} not found or has no members.")
            return []

    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def append_group_member(group_id, group_member):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the current group_members_list for the specified group_id
        cursor.execute("SELECT group_members_list FROM my_groups WHERE group_id = ?", (group_id,))
        row = cursor.fetchone()
        current_members_list = json.loads(row[0]) if row else []

        # Append the new group member to the list
        group_member_id = get_id_from_username(group_member)
        current_members_list.append(group_member_id)

        # Update the group_members_list for the specified group_id
        cursor.execute("UPDATE my_groups SET group_members_list = ? WHERE group_id = ?",
                       (json.dumps(current_members_list), group_id))

        # Commit the changes
        connection.commit()

        print(f"Group member '{group_member}' appended to group (ID: {group_id}) successfully!")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def rename_group(group_id, new_group_name):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()
        # Update the group_name for the specified group_id
        cursor.execute("UPDATE my_groups SET group_name = ? WHERE group_id = ?",
                       (new_group_name, group_id))

        # Commit the changes
        connection.commit()

        print(f"Group (ID: {group_id}) renamed to '{new_group_name}' successfully!")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_user_groups(username):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the groups where the specified username is a group member
        cursor.execute("SELECT group_id, group_name, group_members_list, group_manager, creation_date, "
                       "group_image_path FROM my_groups")

        user_groups = []
        for row in cursor.fetchall():
            group_members_id_list = json.loads(row[2]) if row[2] else []
            group_members_list = []
            for member_id in group_members_id_list:
                group_members_list.append(get_username_from_id(member_id))
            group_image_bytes = file_to_bytes(row[5]) if row[5] else None
            # Check if the specified username is a group member or the manager
            if row[4]:
                timestamp_datetime = datetime.fromisoformat(row[4])

            group_manager = get_username_from_id(row[3])
            if username in group_members_list or username == row[3]:
                user_groups.append({
                    "group_id": row[0],
                    "group_name": row[1],
                    "group_members": group_members_list,
                    "group_manager": group_manager,
                    "creation_date": timestamp_datetime.strftime("%Y-%m-%d") if row[4] else None,  # Format the date if not None
                    "group_b64_encoded_image": base64.b64encode(group_image_bytes).decode(
                        "utf-8") if group_image_bytes else None
                })

        return user_groups

    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_group_by_id(group_id):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the group with the specified group_id
        cursor.execute("SELECT group_id, group_name, group_members_list, group_manager, creation_date, "
                       "group_image_path FROM my_groups WHERE group_id = ?", (group_id,))

        group_data = cursor.fetchone()

        if group_data:
            group_members_id_list = json.loads(group_data[2]) if group_data[2] else []
            group_members_list = []

            for chat_id in group_members_id_list:
                group_members_list.append(get_username_from_id(chat_id))
            group_image_bytes = file_to_bytes(group_data[5]) if group_data[5] else None
            timestamp_datetime = datetime.fromisoformat(group_data[4])

            group_manager = get_username_from_id(group_data[3])
            group_info = {
                "group_id": group_data[0],
                "group_name": group_data[1],
                "group_members": group_members_list,
                "group_manager": group_manager,
                "creation_date": timestamp_datetime.strftime("%Y-%m-%d") if group_data[4] else None,
                "group_b64_encoded_image": base64.b64encode(group_image_bytes).decode(
                    "utf-8") if group_image_bytes else None
            }
            return group_info
        else:
            return None

    except sqlite3.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def create_database():
    try:
        # Connect to the SQLite database (or create it if it doesn't exist)
        connection = sqlite3.connect('connectify_db.sqlite')
        connection.commit()
        connection.close()
        print("Database 'connectify_db' created successfully!")
    except sqlite3.Error as error:
        print(f"Error creating database: {error}")


def create_messages_table():
    try:
        # Establish a connection
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Execute the SQL code to create the table (SQLite syntax)
        create_table_query = """
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT ,
                sender_id INTEGER,
                receiver_id INTEGER,
                message_content TEXT,
                message_content_path TEXT,
                message_content_hash TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type TEXT,
                file_name TEXT
            )
        """
        cursor.execute(create_table_query)
        print("Table 'messages' created successfully.")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
            print("Connection closed.")


def create_friends_table():
    try:
        # Establish a connection
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Execute the SQL code to create the table
        create_table_query = """
                    CREATE TABLE friends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id VARCHAR(255),
                        friend_user_id VARCHAR(255),
                        friendship_status TEXT CHECK(friendship_status IN ('pending', 'accepted', 'rejected'))
                    );
        """
        cursor.execute(create_table_query)
        print("Table 'friends' created successfully.")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
            print("Connection closed.")


def create_groups_table():
    try:
        # Establish a connection
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Execute the SQL code to create the table
        create_table_query = """
            CREATE TABLE IF NOT EXISTS my_groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT ,
                group_name VARCHAR(255),
                group_manager VARCHAR(255),
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                group_members_list TEXT,
                group_image_path VARCHAR(255),
                group_image_hash TEXT,
            )
        """
        cursor.execute(create_table_query)
        print("Table 'my_groups' created successfully.")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
            print("Connection closed.")


def create_settings_table():
    try:
        # Establish a connection
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Execute the SQL code to create the table
        create_table_query = """
            CREATE TABLE IF NOT EXISTS settings_table (
                user_id INTEGER,
                volume INTEGER,
                output_device VARCHAR(255),
                input_device VARCHAR(255),
                camera_device_index INTEGER,
                font_size INTEGER,
                font VARCHAR(255),
                theme_color VARCHAR(255),
                censor_data INTEGER CHECK(two_factor_auth IN (0, 1)),
                private_account INTEGER CHECK(two_factor_auth IN (0, 1)),
                push_to_talk_bind VARCHAR(255),
                two_factor_auth INTEGER CHECK(two_factor_auth IN (0, 1))
            )
        """
        cursor.execute(create_table_query)
        print("Table 'settings_table' created successfully.")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
            print("Connection closed.")


def create_sign_up_table():
    try:
        # Establish a connection
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Execute the SQL code to create the table
        create_table_query = """
            CREATE TABLE IF NOT EXISTS sign_up_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(255),
                password VARCHAR(255),
                email VARCHAR(255),
                salt VARCHAR(255),
                security_token VARCHAR(255),
                chats_list TEXT,
                blocked_list TEXT,
                profile_pic_path VARCHAR(255),
                profile_pic_hash TEXT
            )
        """
        cursor.execute(create_table_query)
        print("Table 'sign_up_table' created successfully.")

    except sqlite3.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
            print("Connection closed.")


def create_songs_table():
    try:
        # Establish a connection
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(255) NOT NULL,
                mp3_file_path VARCHAR(255) NOT NULL,
                mp3_file_hash TEXT,
                thumbnail_path VARCHAR(255),
                thumbnail_hash TEXT,
                owner_id INTEGER,
                duration VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        cursor.execute(create_table_query)
        print("Table 'songs' created successfully.")

    except sqlite3.Error as err:
        print(f"Error in creating songs table: {err}")

    finally:
        # Close the cursor and connection
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
            print("Connection closed.")


def create_tables():
    create_sign_up_table()
    create_groups_table()
    create_friends_table()
    create_messages_table()
    create_settings_table()
    create_songs_table()


def clear_sqlite_table(table_name):
    try:
        # Connect to the SQLite database
        conn = connect_to_kevindb()
        cursor = conn.cursor()

        # Construct and execute the DELETE statement
        delete_query = f"DELETE FROM {table_name}"
        cursor.execute(delete_query)

        # Commit the transaction
        conn.commit()
        print(f"All rows deleted from table '{table_name}'.")

    except sqlite3.Error as e:
        print(f"Error occurred: {e}")

    finally:
        # Close the connection
        if conn:
            conn.close()


def connect_to_kevindb():
    try:
        # Connect to the existing SQLite database
        connection = sqlite3.connect('connectify_db.sqlite')
        return connection
    except sqlite3.Error as error:
        print(f"Error connecting to database: {error}")
        return None


create_database()
create_tables()



