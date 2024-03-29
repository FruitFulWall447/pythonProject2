import mysql.connector
import binascii
import os
import hashlib
import secrets
import json
from datetime import datetime
import base64

pepper = "c5b97dce"
basic_files_types = ["xlsx", "py", "docx", "pptx", "txt", "pdf", "video", "audio", "image"]
default_settings_dict = {
    "volume": 50,  # Default volume level
    "output_device": "default",  # Default output device
    "input_device": "default",  # Default input device
    "camera_device_index": 0,  # Default camera device
    "font_size": 12,  # Default font size
    "font": "Arial",  # Default font
    "theme_color": "Blue",  # Default theme color
    "censor_data": False,  # Default censor data setting
    "private_account": False,  # Default account privacy setting
    "push_to_talk_bind": None,  # Default push-to-talk key binding
    "2fa_enabled": False  # Default 2-factor authentication setting
}


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
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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


def get_user_settings(user_id):
    try:
        # Connect to the database
        db_connection = connect_to_kevindb()

        # Create a cursor object to execute SQL queries
        cursor = db_connection.cursor(dictionary=True)

        # Define the table name
        table_name = "settings_table"

        # Define the SQL SELECT statement to retrieve settings for the given user_id
        select_query = f"SELECT * FROM {table_name} WHERE user_id = %s"

        # Execute the SELECT statement with parameterized values
        cursor.execute(select_query, (user_id,))

        # Fetch all settings rows for the given user_id
        user_settings = cursor.fetchall()

        # Close the cursor and database connection
        cursor.close()
        db_connection.close()

        return user_settings

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
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
        update_query = f"UPDATE {table_name} SET {setting_name} = %s WHERE user_id = %s"

        # Execute the UPDATE statement with parameterized values
        cursor.execute(update_query, (new_value, user_id))

        # Commit the transaction
        db_connection.commit()

        # Close the cursor and database connection
        cursor.close()
        db_connection.close()

        print(f"Setting '{setting_name}' changed successfully.")

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        print("Failed to change setting.")


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

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
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

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return None


def login(username, password):
    try:
        # Create a connection
        connection = connect_to_kevindb()
        salt_by_user = retrieve_salt_by_username(username)
        if salt_by_user is None:
            return False
        hashed_password_salt = hash_sha2(password+salt_by_user)
        hashed_password_salt_pepper = hashed_password_salt+pepper
        # Create a cursor
        cursor = connection.cursor()

        # Define the table name
        table_name = "sign_up_table"

        # Define the SQL SELECT statement to check login credentials with case sensitivity
        select_query = f"""
            SELECT * FROM {table_name}
            WHERE BINARY username = %s AND BINARY password = %s
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

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return False


def username_exists(username):
    try:
        # Create a connection
        connection = connect_to_kevindb()


        # Create a cursor
        cursor = connection.cursor()

        # Define the table name
        table_name = "Sign_Up_Table"

        # Define the SQL SELECT statement to check if the username exists
        select_query = f"SELECT * FROM {table_name} WHERE BINARY username = %s"

        # Execute the SELECT statement with the username value
        cursor.execute(select_query, (username,))

        # Fetch the result (fetchone() returns None if no matching row is found)
        result = cursor.fetchone()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        # Return True if the username exists, False if it doesn't
        return result is not None

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return False


def user_exists_with_email(username, email):
    try:
        # Create a connection
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Define the table name
        table_name = "Sign_Up_Table"

        # Define the SQL SELECT statement to check if the username and email exist
        select_query = f"SELECT * FROM {table_name} WHERE BINARY username = %s AND email = %s"

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
        table_name = "Sign_Up_Table"

        # Define the SQL SELECT statement to check if the token exists
        select_query = f"SELECT username FROM {table_name} WHERE security_token = %s"

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

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return False


def get_security_token(username):
    try:
        # Establish a connection to the database
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        # Define the table name
        table_name = "Sign_Up_Table"

        # Define the SQL SELECT statement to get the security token by username
        select_query = f"SELECT security_token FROM {table_name} WHERE username = %s"

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

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return None


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
        table_name = "Sign_Up_Table"

        # Define the SQL INSERT statement with parameterized queries
        insert_query = f"INSERT INTO {table_name} (username, password, email, salt, security_token) VALUES (%s, %s, %s, %s, %s)"

        # Execute the INSERT statement with parameterized values
        cursor.execute(insert_query, (username, hashed_password_with_salt+pepper, email, salt, security_token))

        # Commit the changes to the database
        user_id = cursor.lastrowid
        connection.commit()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        print("User inserted successfully.")

        create_user_settings(user_id)

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        print("Failed to insert user.")


def update_profile_pic(username, profile_pic_encoded):
    try:
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        if profile_pic_encoded is not None:
            profile_pic = decode_base64(profile_pic_encoded)
        else:
            profile_pic = None

        table_name = "Sign_Up_Table"

        update_query = f"UPDATE {table_name} SET profile_pic_bytes = %s WHERE username = %s"

        # Execute the INSERT statement with parameterized values
        cursor.execute(update_query, (profile_pic, username))

        # Commit the changes to the database
        connection.commit()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        print("Failed to insert user.")


def get_profile_pic_by_name(username):
    try:
        connection = connect_to_kevindb()
        cursor = connection.cursor()


        table_name = "Sign_Up_Table"

        update_query = f"SELECT profile_pic_bytes FROM {table_name} WHERE username = %s"

        # Execute the SELECT statement with the parameterized value
        cursor.execute(update_query, (username,))

        # Fetch the result
        result = cursor.fetchone()

        # Close the cursor and connection when done
        cursor.close()
        connection.close()

        if result:
            return result[0]
        else:
            # If username not found, return None or any other suitable value
            return None

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")


def change_password(username, new_password):
    try:
        connection = connect_to_kevindb()
        cursor = connection.cursor()

        # Generate a new salt for the user
        new_salt = generate_random_salt()

        # Hash the new password with the new salt
        hashed_new_password = hash_sha2(new_password + new_salt)

        # Update the user's password and salt in the database
        update_password_query = "UPDATE Sign_Up_Table SET password = %s, salt = %s WHERE username = %s"
        cursor.execute(update_password_query, (hashed_new_password + pepper, new_salt, username))

        # Commit the changes to the database
        connection.commit()


        # Close the cursor and connection when done
        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        print("Failed to change password.")


def is_table_exist(table_name):
    connection = connect_to_kevindb()


    cursor = connection.cursor()
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")

    # Fetch the result
    result = cursor.fetchone()

    # Return True if the table exists, False if it doesn't
    return result is not None


def add_message(sender_name, receiver_name, message_content, message_type, file_name):
    try:
        # Establish a connection to the MySQL server
        connection = connect_to_kevindb()
        if connection.is_connected():
            cursor = connection.cursor()

            # SQL query to insert a message into the 'messages' table
            if message_type in basic_files_types:
                encoded_base64_bytes = message_content
                message_content = base64.b64decode(encoded_base64_bytes)
                sql_query = "INSERT INTO messages (sender_id, receiver_id, message_content_bytes, type, file_name) VALUES (%s, %s, %s, %s, %s)"
                data = (sender_name, receiver_name, message_content, message_type, file_name)
            else:
                sql_query = "INSERT INTO messages (sender_id, receiver_id, message_content, type) VALUES (%s, %s, %s, %s)"
                data = (sender_name, receiver_name, message_content, message_type)

            # Execute the query
            cursor.execute(sql_query, data)

            # Commit changes to the database
            connection.commit()


    except Exception as e:
        print("Error in adding message:", e)

    finally:
        # Close the database connection
        if connection.is_connected():
            cursor.close()
            connection.close()


def mark_messages_as_read(receiver, sender):
    try:
        connection = connect_to_kevindb()

        cursor = connection.cursor()

        # Update has_read to 1 for messages with the specified receiver and sender
        update_query = "UPDATE messages SET has_read = 1 WHERE receiver_id = %s AND sender_id = %s"
        cursor.execute(update_query, (receiver, sender))

        connection.commit()


    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def gets_group_attributes_from_format(group_format):
    if "(" not in group_format:
        return group_format, None
    else:
        parts = group_format.split(")")
        id = parts[0][1]
        name = parts[1]
        return name, id


def get_messages(sender, receiver):
    try:
        # Connect to the MySQL database (replace with your own connection details)
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Check if the receiver is a group chat (starts with '(')
        is_group_chat = receiver.startswith('(')

        # Execute the query to retrieve messages
        if is_group_chat:
            _, group_id = gets_group_attributes_from_format(receiver)
            id_format = f"({str(group_id)})"
            query = "SELECT IFNULL(message_content, message_content_bytes), sender_id, timestamp, type, file_name FROM messages WHERE receiver_id LIKE '{0}%' ORDER BY timestamp".format(
                id_format.replace('\'', '\'\''))
        else:
            query = """
                SELECT IF(message_content IS NULL, message_content_bytes, message_content), sender_id, timestamp, type, file_name 
                FROM messages
                WHERE (sender_id = '{0}' AND receiver_id = '{1}') OR (sender_id = '{1}' AND receiver_id = '{0}') ORDER BY timestamp

            """.format(sender.replace('\'', '\'\''), receiver.replace('\'', '\'\''))
        cursor.execute(query)

        # Fetch all the results into a list of tuples
        messages = cursor.fetchall()
        messages.reverse()

        # Convert each tuple to a list and include timestamp
        formatted_messages = []
        for message in messages:
            if message[3] != "string":
                # If content is bytes, encode it as a Base64 string
                content = base64.b64encode(message[0]).decode('utf-8')
            else:
                content = message[0].decode('utf-8')
            message_dict = {
                "content": content,
                "sender_id": message[1],
                "timestamp": str(message[2]),
                "message_type": message[3],
                "file_name": message[4]
            }
            formatted_messages.append(message_dict)

        return formatted_messages

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_last_amount_of_messages(sender, receiver, first_message_index, last_message_index):
    try:
        # Connect to the MySQL database (replace with your own connection details)
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Check if the receiver is a group chat (starts with '(')
        is_group_chat = receiver.startswith('(')

        # Execute the query to retrieve messages
        if is_group_chat:
            _, group_id = gets_group_attributes_from_format(receiver)
            id_format = f"({str(group_id)})"
            query = "SELECT IFNULL(message_content, message_content_bytes), sender_id, timestamp, type, file_name FROM messages WHERE receiver_id LIKE '{0}%'".format(
                id_format.replace('\'', '\'\''))
        else:
            query = """
                SELECT IF(message_content IS NULL, message_content_bytes, message_content), sender_id, timestamp, type, file_name 
                FROM messages
                WHERE (sender_id = '{0}' AND receiver_id = '{1}') OR (sender_id = '{1}' AND receiver_id = '{0}')
            """.format(sender.replace('\'', '\'\''), receiver.replace('\'', '\'\''))

        # Add conditions for message indices
        query += f" ORDER BY timestamp DESC LIMIT {last_message_index - first_message_index + 1} OFFSET {first_message_index}"

        cursor.execute(query)

        # Fetch all the results into a list of tuples
        messages = cursor.fetchall()

        # Convert each tuple to a list and include timestamp
        formatted_messages = []
        for message in messages:
            if message[3] != "string":
                # If content is bytes, encode it as a Base64 string
                content = base64.b64encode(message[0]).decode('utf-8')
            else:
                content = message[0].decode('utf-8')
            message_dict = {
                "content": content,
                "sender_id": message[1],
                "timestamp": str(message[2]),
                "message_type": message[3],
                "file_name": message[4]
            }
            formatted_messages.append(message_dict)

        return formatted_messages

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def are_friends(username, friend_username):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if the users are already friends
    query = f"SELECT friendship_status FROM friends WHERE (username = '{username}' AND friend_user_name = '{friend_username}') OR (username = '{friend_username}' AND friend_user_name = '{username}')"
    cursor.execute(query)
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    # Return True if they are friends, False otherwise
    return result and result[0] == 'accepted'


def is_active_request(username, friend_username):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if the users are already friends
    query = f"SELECT friendship_status FROM friends WHERE (username = '{username}' AND friend_user_name = '{friend_username}') OR (username = '{friend_username}' AND friend_user_name = '{username}')"
    cursor.execute(query)
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    # Return True if they are pending, False otherwise
    return result and result[0] == 'pending'


def send_friend_request(username, friend_username):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if a friend request already exists
    query = f"SELECT id FROM friends WHERE username = '{username}' AND friend_user_name = '{friend_username}' AND friendship_status = 'pending'"
    cursor.execute(query)
    existing_request = cursor.fetchone()

    if existing_request:
        print("Friend request already sent.")
    else:
        # Send a new friend request
        insert_query = f"INSERT INTO friends (username, friend_user_name, friendship_status) VALUES ('{username}', '{friend_username}', 'pending')"
        cursor.execute(insert_query)
        connection.commit()
        print("Friend request sent successfully.")

    cursor.close()
    connection.close()


def handle_friend_request(username, friend_username, accept):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if the friend request exists
    query = f"SELECT id FROM friends WHERE username = '{friend_username}' AND friend_user_name = '{username}' AND friendship_status = 'pending'"
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
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Check if the friendship exists
    query = f"SELECT id FROM friends WHERE (username = '{username}' AND friend_user_name = '{friend_username}') OR (username = '{friend_username}' AND friend_user_name = '{username}') AND friendship_status = 'accepted'"
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
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Retrieve friend requests for the given username
    query = f"SELECT username FROM friends WHERE friend_user_name = '{username}' AND friendship_status = 'pending'"
    cursor.execute(query)
    friend_requests = cursor.fetchall()

    cursor.close()
    connection.close()

    # Extract the usernames from the result
    friend_requests_list = [request[0] for request in friend_requests]

    return friend_requests_list


def get_user_friends(username):
    # Assuming you have a MySQL database connection
    # Replace 'your_database', 'your_user', 'your_password' with your actual database credentials
    connection = connect_to_kevindb()

    cursor = connection.cursor()

    # Retrieve friends for the given username
    query = f"""
        SELECT CASE
            WHEN username = '{username}' THEN friend_user_name
            WHEN friend_user_name = '{username}' THEN username
        END AS friend_name
        FROM friends
        WHERE (username = '{username}' OR friend_user_name = '{username}') AND friendship_status = 'accepted';
    """
    cursor.execute(query)
    friends = cursor.fetchall()

    cursor.close()
    connection.close()

    # Extract the friend usernames from the result
    friends_list = [friend[0] for friend in friends]

    return friends_list


def add_chat_to_user(username, new_chat_name):
    try:
        # Connect to your MySQL database (replace with your own connection details)
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the current chats_list for the user
        cursor.execute("SELECT chats_list FROM sign_up_table WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            current_chats_list_json = result[0]

            # If the current_chats_list_json is None, set it to an empty list
            current_chats_list = json.loads(current_chats_list_json) if current_chats_list_json else []

            # Append the new_chat_name to the current_chats_list
            current_chats_list.append(new_chat_name)

            # Convert the updated_chats_list to JSON format
            updated_chats_list_json = json.dumps(current_chats_list)

            # Update the chats_list for the user
            cursor.execute("UPDATE sign_up_table SET chats_list = %s WHERE username = %s",
                           (updated_chats_list_json, username))

            # Commit the changes
            connection.commit()

            print(f"Added '{new_chat_name}' to the chats_list for user '{username}'.")
        else:
            print(f"No user found with username '{username}'.")

    except mysql.connector.Error as err:
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

        # Prepare the UPDATE query
        update_query = """
            UPDATE my_groups
            SET group_image = %s
            WHERE group_id = %s
        """

        # Execute the query
        cursor = connection.cursor()
        cursor.execute(update_query, (image_bytes, group_id))
        connection.commit()

        print(f"Group image updated successfully for group ID: {group_id}")

    except Exception as e:
        print(f"Error updating group image: {e}")

    finally:
        # Close the database connection
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def get_group_image_by_id(group_id):
    try:
        # Establish a connection to the MySQL database
        connection = connect_to_kevindb()

        select_query = """
            SELECT group_image
            FROM my_groups
            WHERE group_id = %s
        """

        # Execute the query
        cursor = connection.cursor()
        cursor.execute(select_query, (group_id,))
        result = cursor.fetchone()

        if result:
            return result

    except Exception as e:
        print(f"Error getting group image: {e}")

    finally:
        # Close the database connection
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def get_user_chats(username):
    try:
        # Connect to your MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the current chats_list for the user
        cursor.execute("SELECT chats_list FROM sign_up_table WHERE username = %s", (username,))
        result = cursor.fetchone()

        # If the result is None or empty, return an empty list
        if not result or not result[0]:
            return []

        # Convert the chats_list JSON to a Python list
        current_chats_list = json.loads(result[0])

        return current_chats_list

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def remove_chat_from_user(username, chat_to_remove):
    try:
        # Connect to your MySQL database (replace with your own connection details)
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Retrieve the current chats_list for the user
        cursor.execute("SELECT chats_list FROM sign_up_table WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            current_chats_list_json = result[0]

            # If the current_chats_list_json is None, set it to an empty list
            current_chats_list = json.loads(current_chats_list_json) if current_chats_list_json else []

            # Remove the specified chat from the current_chats_list
            if chat_to_remove in current_chats_list:
                current_chats_list.remove(chat_to_remove)

                # Convert the updated_chats_list to JSON format
                updated_chats_list_json = json.dumps(current_chats_list)

                # Update the chats_list for the user
                cursor.execute("UPDATE sign_up_table SET chats_list = %s WHERE username = %s",
                               (updated_chats_list_json, username))

                # Commit the changes
                connection.commit()

                print(f"Removed '{chat_to_remove}' from the chats_list for user '{username}'.")
            else:
                print(f"Chat '{chat_to_remove}' not found in the chats_list for user '{username}'.")
        else:
            print(f"No user found with username '{username}'.")

    except mysql.connector.Error as err:
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
        cursor.execute("SELECT blocked_list FROM sign_up_table WHERE username = %s", (username,))
        result = cursor.fetchone()

        # If no result or blocked_list is empty, return an empty list
        if not result or not result[0]:
            return []

        # Convert the blocked_list JSON to a Python list
        blocked_users = json.loads(result[0])

        return blocked_users

    except mysql.connector.Error as err:
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
        cursor.execute("SELECT blocked_list FROM sign_up_table WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            blocked_list_json = result[0]

            # If the blocked_list_json is None, set it to an empty list
            blocked_list = json.loads(blocked_list_json) if blocked_list_json else []

            # Add the user_to_block to the blocked_list
            blocked_list.append(user_to_block)

            # Convert the updated blocked_list to JSON format
            updated_blocked_list_json = json.dumps(blocked_list)

            # Update the blocked_list for the user
            cursor.execute("UPDATE sign_up_table SET blocked_list = %s WHERE username = %s",
                           (updated_blocked_list_json, username))

            # Commit the changes
            connection.commit()

            print(f"Blocked user '{user_to_block}' for user '{username}'.")
        else:
            print(f"No user found with username '{username}'.")

    except mysql.connector.Error as err:
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
        cursor.execute("SELECT blocked_list FROM sign_up_table WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            blocked_list_json = result[0]

            # If the blocked_list_json is None, set it to an empty list
            blocked_list = json.loads(blocked_list_json) if blocked_list_json else []

            # Remove the user_to_unblock from the blocked_list if it exists
            if user_to_unblock in blocked_list:
                blocked_list.remove(user_to_unblock)

                # Convert the updated blocked_list to JSON format
                updated_blocked_list_json = json.dumps(blocked_list)

                # Update the blocked_list for the user
                cursor.execute("UPDATE sign_up_table SET blocked_list = %s WHERE username = %s",
                               (updated_blocked_list_json, username))

                # Commit the changes
                connection.commit()

                print(f"Unblocked user '{user_to_unblock}' for user '{username}'.")
            else:
                print(f"User '{user_to_unblock}' not found in the blocked list for user '{username}'.")

        else:
            print(f"No user found with username '{username}'.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def create_group(group_name, group_manager, group_members_list=None):
    new_chat_name = ""
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Convert group_members_list to a JSON-formatted string
        group_members_json = json.dumps(group_members_list) if group_members_list else None

        # Insert the group into the 'my_groups' table
        cursor.execute("INSERT INTO my_groups (group_name, group_manager, group_members_list) VALUES (%s, %s, %s)",
                       (group_name, group_manager, group_members_json))

        # Get the last inserted group_id
        cursor.execute("SELECT LAST_INSERT_ID()")
        group_id = cursor.fetchone()[0]
        new_chat_name = f"({group_id}){group_name}"


        # Commit the changes
        connection.commit()

        print(f"Group '{group_name}' created successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        for member in group_members_list:
            add_chat_to_user(member, new_chat_name)
        return new_chat_name, group_id


def change_group_manager(group_id, new_manager):
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Update the manager for the specified group
        cursor.execute("UPDATE my_groups SET group_manager = %s WHERE group_id = %s", (new_manager, group_id))

        # Commit the changes
        connection.commit()

        print(f"Manager for group (ID: {group_id}) changed to '{new_manager}' successfully!")

    except mysql.connector.Error as err:
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
        cursor.execute("SELECT group_name FROM my_groups WHERE group_id = %s", (group_id,))
        group_name_result = cursor.fetchone()

        # Check if the group exists
        if group_name_result:
            group_name = group_name_result[0]
            return group_name
        else:
            print(f"Group with ID {group_id} not found.")
            return None

    except mysql.connector.Error as err:
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
        cursor.execute("SELECT group_members_list FROM my_groups WHERE group_id = %s", (group_id,))
        current_members_list = json.loads(cursor.fetchone()[0]) if cursor.fetchone() else []

        # Remove the group member from the list
        if group_member in current_members_list:
            current_members_list.remove(group_member)

            # Update the group_members_list for the specified group_id
            cursor.execute("UPDATE my_groups SET group_members_list = %s WHERE group_id = %s",
                           (json.dumps(current_members_list), group_id))

            # Commit the changes
            connection.commit()

            print(f"Group member '{group_member}' removed from group (ID: {group_id}) successfully!")
        else:
            print(f"Group member '{group_member}' not found in group (ID: {group_id}). No changes made.")

    except mysql.connector.Error as err:
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
        cursor.execute("SELECT group_members_list FROM my_groups WHERE group_id = %s", (group_id,))
        members_list_json = cursor.fetchone()

        # Check if the group exists and has members
        if members_list_json:
            members_list = json.loads(members_list_json[0])
            return members_list
        else:
            print(f"Group with ID {group_id} not found or has no members.")
            return []

    except mysql.connector.Error as err:
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
        cursor.execute("SELECT group_members_list FROM my_groups WHERE group_id = %s", (group_id,))
        row = cursor.fetchone()
        current_members_list = json.loads(row[0]) if row else []

        # Append the new group member to the list
        current_members_list.append(group_member)

        # Update the group_members_list for the specified group_id
        cursor.execute("UPDATE my_groups SET group_members_list = %s WHERE group_id = %s",
                       (json.dumps(current_members_list), group_id))

        # Commit the changes
        connection.commit()

        print(f"Group member '{group_member}' appended to group (ID: {group_id}) successfully!")

    except mysql.connector.Error as err:
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
        new_group_name_format = f"({str(group_id)}){new_group_name}"
        # Update the group_name for the specified group_id
        cursor.execute("UPDATE my_groups SET group_name = %s WHERE group_id = %s",
                       (new_group_name_format, group_id))

        # Commit the changes
        connection.commit()

        print(f"Group (ID: {group_id}) renamed to '{new_group_name}' successfully!")

    except mysql.connector.Error as err:
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
                       "group_image FROM my_groups")

        user_groups = []
        for row in cursor.fetchall():
            group_members_list = json.loads(row[2]) if row[2] else []

            # Check if the specified username is a group member or the manager
            if username in group_members_list or username == row[3]:
                user_groups.append({
                    "group_id": row[0],
                    "group_name": row[1],
                    "group_members": group_members_list,
                    "group_manager": row[3],
                    "creation_date": row[4].strftime("%Y-%m-%d") if row[4] else None,  # Format the date if not None
                    "group_b64_encoded_image": base64.b64encode(row[5]).decode("utf-8") if row[5] else None
                })

        return user_groups

    except mysql.connector.Error as err:
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
                       "group_image FROM my_groups WHERE group_id = %s", (group_id,))

        group_data = cursor.fetchone()

        if group_data:
            group_members_list = json.loads(group_data[2]) if group_data[2] else []

            group_info = {
                "group_id": group_data[0],
                "group_name": group_data[1],
                "group_members": group_members_list,
                "group_manager": group_data[3],
                "creation_date": group_data[4].strftime("%Y-%m-%d") if group_data[4] else None,
                "group_b64_encoded_image": base64.b64encode(group_data[5]).decode("utf-8") if group_data[5] else None
            }
            return group_info
        else:
            return None

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()



def get_latest_chats(username):
    try:
        chats_list = get_user_chats(username)
        user_groups = get_user_groups(username)

        # Initialize a list to store the latest chats
        latest_chats = []

        connection = connect_to_kevindb()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Iterate through the user's groups
        for group in user_groups:
            group_name = f"({group['group_id']}){group['group_name']}"

            # Query the latest timestamp for the group
            cursor.execute(
                f"SELECT MAX(timestamp) as latest_timestamp FROM messages WHERE sender_id = %s AND receiver_id = %s",
                (group_name, group_name))

            result = cursor.fetchone()
            latest_timestamp = result[0] if result and result[0] else datetime.min

            # Append the group to the list with its latest timestamp
            latest_chats.append({
                'chat_name': group_name,
                'latest_timestamp': latest_timestamp
            })

        # Iterate through the user's individual chats
        for chat_name in chats_list:
            # Query the latest timestamp for the individual chat
            cursor.execute(
                f"SELECT MAX(timestamp) as latest_timestamp FROM messages WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)",
                (username, chat_name, chat_name, username))

            result = cursor.fetchone()
            latest_timestamp = result[0] if result and result[0] else datetime.min


            # Append the individual chat to the list with its latest timestamp
            latest_chats.append({
                'chat_name': chat_name,
                'latest_timestamp': latest_timestamp
            })

        # Sort the latest_chats list by 'latest_timestamp' in descending order
        latest_chats = sorted(latest_chats, key=lambda x: x['latest_timestamp'], reverse=True)
        unique_chat_names = set()
        filtered_latest_chats = []

        for chat in latest_chats:
            chat_name = chat['chat_name']
            if chat_name not in unique_chat_names:
                filtered_latest_chats.append(chat)
                unique_chat_names.add(chat_name)

        return filtered_latest_chats

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def clear_tables():
    try:
        # Connect to the MySQL database
        connection = connect_to_kevindb()
        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # List of tables to clear
        tables_to_clear = ['sign_up_table', 'friends', 'messages', 'my_groups']

        # Clear (truncate) each table
        for table in tables_to_clear:
            cursor.execute(f"TRUNCATE TABLE {table}")

        # Commit the changes
        connection.commit()

        print("Tables cleared successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def create_messages_table():
    try:
        # Establish a connection
        connection = connect_to_kevindb()

        # Create a cursor
        cursor = connection.cursor()

        # Execute the SQL code to create the table
        create_table_query = """
            CREATE TABLE messages (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id VARCHAR(255),
                receiver_id VARCHAR(255),
                message_content TEXT,
                message_content_bytes LONGBLOB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                has_read TINYINT(1) DEFAULT 0,
                type VARCHAR(255),
            )
        """
        cursor.execute(create_table_query)
        print("Table 'messages' created successfully.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("Connection closed.")


def connect_to_kevindb():
    return mysql.connector.connect(host="localhost", user="root", password="LingshUpper1208", database="kevindb")


