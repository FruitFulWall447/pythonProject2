from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap
from messages_page_widgets import ScrollAreaWidget


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

            self.setup_friends_box(friends_box_list, self.online_button, selecting_button_pressed_stylesheet,
                                   f"ONLINE — {len(friends_box_list)}", search_x, search_y, search_width, search_height,
                                   friend_x, border2_width)
        if self.parent.friends_box_page == "all":
            friends_box_list = []
            try:
                if self.parent.current_friends_box_search:
                    friends_box_list = self.parent.temp_search_list
                else:
                    friends_box_list = self.parent.friends_list
            except Exception as e:
                print(f"error in friends_box{e}")
            self.setup_friends_box(friends_box_list, self.all_button, selecting_button_pressed_stylesheet,
                                   f"ALL FRIENDS — {len(friends_box_list)}", search_x, search_y, search_width,
                                   search_height, friend_x, border2_width)
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
                temp_list = []
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

                    container = QWidget(self)
                    container_layout = QHBoxLayout(container)
                    container_layout.addWidget(request_label)
                    container_layout.addWidget(accept_button)
                    container_layout.addWidget(reject_button)
                    temp_list.append(container)

                for i in range(0, len(self.requests_items), 3):
                    accept_button = self.requests_items[i + 1]
                    reject_button = self.requests_items[i + 2]

                    accept_button.clicked.connect(
                        lambda checked, index=i: self.handle_friend_request(index, accept=True))
                    reject_button.clicked.connect(
                        lambda checked, index=i: self.handle_friend_request(index, accept=False))

                x = request_x - 27
                request_list_widget = ScrollAreaWidget(self, x, 200, 710, 760, temp_list, True)
                # self.raise_all_element()
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
            temp_list = []
            for friend in friends_box_list:
                friend_label = QLabel(friend, self)
                friend_label.setStyleSheet(style_sheet)
                friend_label.move(friends_label_x + 25, friend_starter_y)
                friend_label.setFixedHeight(self.font_size)  # Increase height
                friend_label.adjustSize()  # Ensure the label size is adjusted to its content

                unblock_friend_button_x = 1235
                unblock_friend_button = QPushButton(self)

                self.set_up_button_with_icon(
                    unblock_friend_button,
                    "Unblock",
                    "discord_app_assets/block_icon.png",
                    self.unblock_friend,
                    unblock_friend_button_x - 60,
                    friend_starter_y + 10,
                    friend  # Pass the friend parameter here
                )

                friend_starter_y += 70
                self.friend_labels.append(friend_label)

                container = QWidget(self)
                container_layout = QHBoxLayout(container)
                container_layout.setSpacing(0)

                # Set contents margins to 0
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setAlignment(Qt.AlignLeft)

                container_layout.addWidget(friend_label)
                container_layout.addWidget(unblock_friend_button)
                temp_list.append(container)
            x = search_x - 27
            blocked_list_widget = ScrollAreaWidget(self, x, 200, 710, 760, temp_list, True)

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

    def setup_social_label(self, text, y_offset, search_x, search_y):
        self.social_label = QLabel(text, self)
        self.social_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        self.social_label.move(search_x, search_y + y_offset)
        self.social_label.adjustSize()

    def setup_search_input(self, search_x, search_y, search_width, search_height):
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search")
        self.search.setStyleSheet(
            f"background-color: {self.parent.standard_hover_color}; color: {self.search_box_color}; padding: 10px; border: 1px solid {self.parent.standard_hover_color}; border-radius: 5px; font-size: 14px;")
        self.search.setGeometry(search_x, search_y, search_width, search_height)
        self.search.textChanged.connect(self.on_text_changed_in_contact_search)

    def setup_friend_ui(self, friend, y_position, label_x, chat_button_x, friends_label_x, friend_x, border2_width):
        style_sheet = '''
            color: white;
            font-size: 40px;
            margin-bottom: 10px;
        '''
        friend_label = QLabel(friend, self)
        friend_label.setStyleSheet(style_sheet)
        friend_label.move(label_x + 25, y_position)
        friend_label.setFixedHeight(self.font_size)
        friend_label.adjustSize()

        chat_button = QPushButton(self)
        self.set_up_button_with_icon(
            chat_button,
            "Message",
            "discord_app_assets/press_chat_icon.png",
            self.open_chat,
            chat_button_x,
            y_position + 10,
            friend
        )

        remove_friend_button = QPushButton(self)
        remove_friend_button_x = chat_button_x - 60
        self.set_up_button_with_icon(
            remove_friend_button,
            "Remove",
            "discord_app_assets/remove_friend_icon.png",
            self.remove_friend,
            remove_friend_button_x,
            y_position + 10,
            friend
        )

        block_friend_button = QPushButton(self)
        self.set_up_button_with_icon(
            block_friend_button,
            "Block",
            "discord_app_assets/block_icon.png",
            self.block_friend,
            remove_friend_button_x - 60,
            y_position + 10,
            friend
        )

        circle_label = QLabel(self)
        circle_label.setGeometry(friends_label_x, y_position + 20, 20, 20)
        if friend in self.parent.online_users_list:
            self.draw_circle(circle_label, "green")
        else:
            self.draw_circle(circle_label, "gray")

        container = QWidget(self)
        container_layout = QHBoxLayout(container)
        container_layout.addWidget(circle_label)
        friend_label.setAlignment(Qt.AlignLeft)
        container_layout.addWidget(friend_label, alignment=Qt.AlignLeft)  # Ensure label aligns to the left
        container_layout.addStretch()  # Add a stretchable space to push other widgets to the right
        container_layout.addWidget(block_friend_button)
        container_layout.addWidget(remove_friend_button)
        container_layout.addWidget(chat_button)
        container.setLayout(container_layout)

        # Position the container widget
        container.move(label_x, y_position)
        container.show()

        # Return the container if needed
        return container

    def setup_friends_box(self, friends_box_list, button, button_stylesheet, label_text, search_x, search_y,
                          search_width, search_height, friend_x, border2_width):

        friends_label_x = search_x
        friend_starter_y = 200 + (self.parent.friends_box_index * -50)
        self.parent.friends_box_index_y_start = friend_starter_y

        button.setStyleSheet(button_stylesheet)
        self.setup_social_label(label_text, 60, search_x, search_y)
        self.setup_search_input(search_x, search_y, search_width, search_height)

        self.friend_labels = []

        temp_list = []
        for friend in friends_box_list:
            friend_label = self.setup_friend_ui(friend, friend_starter_y, friends_label_x, 1235, friends_label_x,
                                                friend_x, border2_width)
            temp_list.append(friend_label)
            self.friend_labels.append(friend_label)
            friend_starter_y += 70

        friends_label_x = friends_label_x - 27
        chats_list_scroll_area = ScrollAreaWidget(self, friends_label_x, 200, 710, 760, temp_list, True)

    def set_up_button_with_icon(self, button, label_text, icon_path, click_callback, x, y, friend):
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
                    self.parent.updated_social_page()
                else:
                    try:
                        self.parent.current_friends_box_search = False
                        self.parent.temp_search_list = []
                        self.parent.updated_social_page()
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
            # self.chat_label.raise_()
        except Exception as e:
            print(e)
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
            self.parent.updated_social_page()

    def all_button_pressed(self):
        if self.parent.friends_box_page != "all":
            if self.parent.friends_box_page != "add friend":
                self.search.clear()
            self.parent.current_friends_box_search = False
            self.parent.temp_search_list = []
            self.parent.friends_box_index = 0
            self.parent.friends_box_page = "all"
            self.parent.updated_social_page()

    def pending_button_pressed(self):
        try:
            if self.parent.friends_box_page != "pending":
                if self.parent.friends_box_page != "add friend":
                    self.search.clear()
                self.parent.current_friends_box_search = False
                self.parent.temp_search_list = []
                self.parent.friends_box_index = 0
                self.parent.friends_box_page = "pending"
                self.parent.updated_social_page()
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
            self.parent.updated_social_page()

    def add_friend_button_pressed(self):
        try:
            if self.parent.friends_box_page != "add friend":
                if self.parent.friends_box_page != "add friend":
                    self.search.clear()
                self.parent.current_friends_box_search = False
                self.parent.temp_search_list = []
                self.parent.friends_box_index = 0
                self.parent.friends_box_page = "add friend"
                self.parent.updated_social_page()
        except Exception as e:
            print(f"error add_friend_button_pressed {e}")

    def open_chat(self, friend):
        # Implement the logic to start a chat with the selected friend
        print(f"Starting chat with {friend}")
        self.parent.chat_box.selected_chat_changed(friend)
        self.parent.chat_clicked()

    def remove_friend(self, friend):
        # Implement the logic to start a chat with the selected friend
        print(f"Removing {friend} as friend")
        self.Network.send_remove_friend(friend)
        self.parent.friends_list.remove(friend)
        self.parent.updated_social_page()

    def block_friend(self, friend):
        # Implement the logic to start a chat with the selected friend
        self.Network.block_user(friend)
        self.parent.blocked_list.append(friend)
        self.parent.friends_list.remove(friend)
        print(f"blocking {friend}")
        self.parent.updated_social_page()

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
            self.Network.send_friend_request(friend_username)
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
        self.parent.updated_social_page()