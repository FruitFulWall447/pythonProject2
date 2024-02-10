from datetime import datetime
import time
import uuid
import database_func
import copy

class Call:
    def __init__(self, parent, participants, nets, group_id=None):
        self.logger = logging.getLogger(__name__)
        self.nets_dict = nets
        self.parent = parent
        if group_id is not None:
            self.is_group_call = True
            self.group_id = group_id
        else:
            self.is_group_call = False
        self.participants = participants
        existed_ring_id_associated_with_call = self.parent.get_ring_id_by_possible_ringers(self.participants)
        if existed_ring_id_associated_with_call is not None:
            self.call_id = existed_ring_id_associated_with_call
        else:
            self.call_id = str(uuid.uuid4())  # Generates a random UUID
        self.logger.info(f"Call of id ({self.call_id}) was created. Users in call are {self.participants}")
        self.call_nets = {}
        self.initiated_time = datetime.now()
        self.gets_call_nets_from_dict()
        self.muted = []
        self.deafened = []
        self.video_streams_list = []
        self.send_call_object_to_clients()
        self.send_to_everyone_call_accepted()
        # if using thread here
        self.data_collection = []  # List of tuples containing user and vc_data
        self.stop_thread = threading.Event()  # Event for signaling the thread to stop
        self.thread = threading.Thread(target=self.process_vc_data)
        self.thread.start()

    def create_video_stream_of_user(self, user):
        if self.is_group_call:
            video_stream = VideoStream(self.parent, user, self, self.group_id)
        else:
            video_stream = VideoStream(self.parent, user, self, None)
        self.video_streams_list.append(video_stream)
        self.send_call_object_to_clients()

    def close_video_stream_by_user(self, user):
        for stream in self.video_streams_list:
            if stream.streamer == user:
                stream.end_stream()
                self.video_streams_list.remove(stream)
        self.send_call_object_to_clients()

    def get_call_group_members(self):
        temp_list = database_func.get_group_members(self.group_id)
        return temp_list

    def get_call_dict(self):
        call_data = {
            "is_group_call": self.is_group_call,
            "call_id": self.call_id,
            "participants": self.participants,
            "muted": self.muted,
            "deafened": self.deafened,
            "video_streamers": self.get_all_video_steamers(),
            "group_id": self.group_id if self.is_group_call else None,
            # Add more attributes as needed
        }
        return call_data

    def get_all_video_steamers(self):
        list_names = []
        for video_stream in self.video_streams_list:
            list_names.append(video_stream.streamer)
        return list_names

    def send_call_object_to_clients(self):
        # Extract relevant attributes to send
        call_data = {
            "is_group_call": self.is_group_call,
            "call_id": self.call_id,
            "participants": self.participants,
            "muted": self.muted,
            "deafened": self.deafened,
            "video_streamers": self.get_all_video_steamers(),
            "group_id": self.group_id if self.is_group_call else None,
            # Add more attributes as needed
        }

        for name, net in self.call_nets.items():
            if net is not None:
                net.send_call_dict(call_data)

    def call_ending_protocol(self):
        self.logger.debug(f"call participants: {self.participants}")
        for name, net in self.call_nets.items():
            if net is not None:
                net.send_str("call:ended")
                net.remove_call_to_user_of_id(self.call_id)
        self.logger.info(f"Call of id {self.call_id} ended")
        call_time = datetime.now() - self.initiated_time
        self.logger.info(f"Call was up for {call_time}")
        self.parent.cancel_ring_by_id(self.call_id)
        self.stop_processing()

    def send_to_everyone_call_accepted(self):
        for name, net in self.call_nets.items():
            if net is not None and name in self.participants:
                net.send_str("call:accepted")

    def is_user_in_a_call(self, user):
        if user in self.participants:
            return True
        else:
            return False

    def gets_call_nets_from_dict(self):
        if not self.is_group_call:
            temp_list = self.participants
        else:
            temp_list = database_func.get_group_members(self.group_id)
        # Create a dictionary with names and corresponding nets for names in temp_list
        self.call_nets = {name: self.parent.nets_dict.get(name) for name in temp_list}

    def update_call_nets(self):
        self.nets_dict = self.parent.nets_dict
        self.gets_call_nets_from_dict()

    def remove_user_from_call(self, user):
        self.participants.remove(user)
        self.gets_call_nets_from_dict()
        self.send_call_object_to_clients()
        self.logger.info(f"{user} left call by id {self.call_id}")

    def add_user_to_call(self, user):
        self.participants.append(user)
        self.gets_call_nets_from_dict()
        try:
            net = self.parent.get_net_by_name(user)
            net.send_str("call:accepted")
            self.logger.debug(f"Sent call:accepted to user {user}, with net {net}")
        except Exception as e:
            self.logger.error(f"Error sending string: {e}")
        self.send_call_object_to_clients()
        self.logger.info(f"{user} joined call by id {self.call_id}")


    def process_vc_data(self):
        while not self.stop_thread.is_set():
            if self.data_collection:
                user, vc_data = self.data_collection.pop(0)
                self.send_vc_data_to_everyone_but_user(vc_data, user)
            else:
                # Sleep or perform other tasks if the data collection is empty
                time.sleep(0.1)

    def stop_processing(self):
        self.stop_thread.set()
        self.thread.join()  # Wait for the thread to finish

    def adding_vc_data_to_user_call_thread_queue(self, user, vc_data):
        self.data_collection.append((user, vc_data))

    def send_vc_data_to_everyone_but_user(self, vc_data, user):
        for name, net in self.call_nets.items():
            if name != user and net is not None and name not in self.deafened and name in self.participants:
                net.send_vc_data(vc_data, user)
                # self.logger.debug(f"Sent voice chat data to {name}")

    def is_a_group_a_call(self):
        return self.is_group_call

    def toggle_mute_for_user(self, user):
        if user in self.muted:
            self.muted.remove(user)
            self.logger.info(f"{user} unmuted himself in call of id {self.call_id}")
        else:
            self.muted.append(user)
            self.logger.info(f"{user} muted himself in call of id {self.call_id}")
        self.send_call_object_to_clients()

    def toggle_deafen_for_user(self, user):
        if user in self.deafened:
            self.deafened.remove(user)
            self.logger.info(f"{user} undeafened himself in call of id {self.call_id}")
        else:
            self.deafened.append(user)
            self.logger.info(f"{user} deafened himself in call of id {self.call_id}")
        self.send_call_object_to_clients()

    def add_spectator_for_stream(self, spectator, streamer):
        for stream in self.video_streams_list:
            if stream.streamer == streamer:
                stream.add_spectator(spectator)

    def remove_spectator_for_stream(self, spectator):
        for stream in self.video_streams_list:
            if spectator in stream.spectators:
                stream.remove_spectator(spectator)

from discord_comms_protocol import server_net
import threading
from multiprocessing import Process

class Ring:
    def __init__(self, Parent, ringer, nets, ringing_to=None, group_id=None):
        self.logger = logging.getLogger(__name__)
        self.parent = Parent
        self.ring_time = 25
        self.nets_dict = nets
        self.ringer = ringer
        self.ring_id = str(uuid.uuid4())  # Generates a random UUID
        if group_id is not None:
            self.logger.info(f"Ring of id ({self.ring_id}) is a ring from type Group")
            self.is_group_ring = True
            group_members = database_func.get_group_members(group_id)
            self.ringing_to = group_members
            self.ringing_to.remove(ringer)
            self.group_id = group_id
        else:
            self.is_group_ring = False
            self.ringing_to = ringing_to
        self.initiated_time = datetime.now()
        self.ringers_nets = {}
        self.ringed_to = []
        self.gets_ringing_nets_from_dict()
        self.already_ringed_to = []
        self.ring_to_everyone_online()
        self.ring_thread_flag = True
        self.accepted_rings = []
        self.rejected_rings = []
        self.is_ringer_stopped_call = False
        threading.Thread(target=self.process_call_and_send_response, args=()).start()


    def rejected_ring(self, user):
        self.rejected_rings.append(user)
        self.logger.info(f"{user} declined call")

    def accepted_ring(self, user):
        self.accepted_rings.append(user)

    def process_call_and_send_response(self):
        time_counter = 0
        while self.ring_thread_flag:
            time.sleep(0.1)
            time_counter += 0.1
            if time_counter >= self.ring_time:
                self.ring_thread_flag = False
            if len(self.ringing_to) == (len(self.accepted_rings) + len(self.rejected_rings)):
                self.ring_thread_flag = False
                self.logger.info(f"Ring of id {self.ring_id} was stopped due to everyone answering or rejecting ring")
        if not self.is_ringer_stopped_call:
            self.stop_ring_for_unanswered_users()
            if len(self.accepted_rings) == 0:
                self.stop_ring_for_ringer()
                self.logger.info(f"Ring of id {self.ring_id} was stopped due to no answering the call")
            self.parent.remove_ring(self)

    def stop_ring_for_unanswered_users(self):
        for name, net in self.ringers_nets.items():
            if net is not None:
                if name not in self.accepted_rings and name not in self.rejected_rings:
                    net.send_str('call:timeout')

    def stop_ring_for_ringer(self):
        ringers_net = self.parent.get_net_by_name(self.ringer)
        ringers_net.send_str('call:timeout')

    def cancel_ring_for_all(self):
        for name, net in self.ringers_nets.items():
            if net is not None:
                net.send_str('call:timeout')
        self.stop_ring_for_ringer()
        self.is_ringer_stopped_call = True
        self.ring_thread_flag = False
        self.parent.remove_ring(self)
        self.logger.info(f"Ringer of ring id {self.ring_id} stopped ringing, {self.ringer} got frustrated...")

    def gets_ringing_nets_from_dict(self):
        temp_list = self.ringing_to
        # Create a dictionary with names and corresponding nets for names in temp_list
        self.ringers_nets = {name: self.nets_dict.get(name) for name in temp_list}

    def ring_to_everyone_online(self):
        if self.is_group_ring:
            group_name = database_func.get_group_name_by_id(self.group_id)
            format = f"({self.group_id}){group_name}({self.ringer})"
            for name, net in self.ringers_nets.items():
                if net is not None:
                    net.send_user_that_calling(format)
                    self.ringed_to.append(name)
                    self.logger.info(f"Sent ring of id {self.ring_id} to {name}")
                    self.already_ringed_to.append(name)
        else:
            self.logger.info(f"Created 1 on 1 ring (id={self.ring_id}) [{self.ringing_to[0]}, ringer is:{self.ringer}]")
            for name, net in self.ringers_nets.items():
                if net is not None:
                    net.send_user_that_calling(self.ringer)
                    self.ringed_to.append(name)
                    self.logger.info(f"Sent ring of id {self.ring_id} to {name}")
                    self.already_ringed_to.append(name)

    def update_ring_nets(self, nets):
        self.nets_dict = nets
        self.gets_ringing_nets_from_dict()
        self.ring_to_users_who_didnt_get_a_ring()

    def ring_to_users_who_didnt_get_a_ring(self):
        if self.is_group_ring:
            group_name = database_func.get_group_name_by_id(self.group_id)
            format = f"({self.group_id}){group_name}({self.ringer})"
            for name, net in self.ringers_nets.items():
                if name not in self.already_ringed_to and net is not None:
                    net.send_user_that_calling(format)
                    self.ringed_to.append(name)
                    self.logger.info(f"Sent ring of id {self.ring_id} to {name}")
                    self.already_ringed_to.append(name)
        else:
            for name, net in self.ringers_nets.items():
                if name not in self.already_ringed_to and net is not None:
                    net.send_user_that_calling(self.ringer)
                    self.ringed_to.append(name)
                    self.logger.info(f"Sent ring of id {self.ring_id} to {name}")
                    self.already_ringed_to.append(name)

    def is_ring_by_ringer(self, ringer):
        return self.ringer == ringer


import logging


class Communication:
    def __init__(self):
        self.calls = []
        self.rings = []
        self.nets_dict = {}
        self.online_users = []
        self.logger = logging.getLogger(__name__)

    def send_to_user_needed_info(self, User):
        net = self.get_net_by_name(User)
        friends_list = database_func.get_user_friends(User)
        net.send_friends_list(friends_list)
        self.logger.info(f"Sent friend list ({friends_list}) to user {User}")
        friend_request_list = database_func.get_friend_requests(User)
        net.send_requests_list(friend_request_list)
        self.logger.info(f"Sent requests list ({friend_request_list}) to user {User}")
        user_groups_list = database_func.get_user_groups(User)
        net.send_user_groups_list(user_groups_list)
        self.logger.info(f"Sent groups list to user {User}")
        user_chats_list = database_func.get_user_chats(User)
        net.send_user_chats_list(user_chats_list)
        self.logger.info(f"Sent Chats list to user {User}")
        online_friends = self.find_common_elements(self.online_users, friends_list)
        net.send_online_users_list(online_friends)
        self.logger.info(f"Sent Online friends list to user {User}")
        list_call_dicts = self.get_list_of_calls_for_user(User)
        net.send_call_list_of_dicts(list_call_dicts)
        self.logger.info(f"Sent list of call dicts list to user {User}")

    def get_list_of_calls_for_user(self, user):
        list_of_calls_dicts = []
        for call in self.calls:
            if call.is_group_call:
                if user in call.get_call_group_members():
                    current_call_dict = call.get_call_dict()
                    list_of_calls_dicts.append(current_call_dict)
        return list_of_calls_dicts

    def update_online_list_for_users_friends(self, user):
        user_friends_list = database_func.get_user_friends(user)
        for friend in user_friends_list:
            if friend in self.online_users:
                friend_friends_list = database_func.get_user_friends(friend)
                friends_net = self.get_net_by_name(friend)
                online_friends = self.find_common_elements(self.online_users, friend_friends_list)
                friends_net.send_online_users_list(online_friends)

    def find_common_elements(self, list1, list2):
        # Use set intersection to find common elements
        common_elements = list(set(list1) & set(list2))
        return common_elements

    def user_online(self, user, net):
        self.online_users.append(user)
        self.add_net(user, net)
        self.send_to_user_needed_info(user)
        self.update_online_list_for_users_friends(user)

    def user_offline(self, user):
        self.online_users.remove(user)
        self.remove_net_by_name(user)
        self.update_nets_for_child_class()
        self.update_online_list_for_users_friends(user)

    def add_net(self, name, obj):
        self.nets_dict[name] = obj
        self.update_nets_for_child_class()

    def update_nets_for_child_class(self):
        for ring in self.rings:
            ring.update_ring_nets(self.nets_dict)
        for call in self.calls:
            call.update_call_nets()

    def get_net_by_name(self, name):
        return self.nets_dict.get(name, None)

    def remove_net_by_name(self, name):
        if name in self.nets_dict:
            del self.nets_dict[name]
            self.logger.info(f"Net '{name}' removed successfully.")
        else:
            self.logger.warning(f"Net '{name}' not found.")

    def add_call(self, call):
        if len(call.participants) < 2:
            self.logger.error("A call must have at least 2 participants. Call was not added.")
        else:
            self.calls.append(call)

    def is_user_in_a_call(self, user):
        for call in self.calls:
            if call.is_user_in_a_call(user):
                return True
        return False

    def remove_user_from_call(self, user):
        if not self.calls:
            self.logger.warning("Tried to remove user from call. But there is No active calls.")
            return

        for call in self.calls:
            if user in call.participants:
                if len(call.participants) == 2:
                    if call.is_group_call:
                        self.logger.info(
                            f"{user} ended call in group call of id:{database_func.get_group_name_by_id(call.group_id)}")
                    else:
                        temp_list = copy.deepcopy(call.participants)
                        temp_list.remove(user)
                        self.logger.info(f"{user} ended call with {temp_list[0]}")
                    call.call_ending_protocol()
                    self.calls.remove(call)  # Remove the call from the calls list
                else:
                    call.remove_user_from_call(user)
                    users_net = self.get_net_by_name(user)
                    users_net.send_str("call:ended")
                    self.logger.info("Removed user from group call")

    def are_users_in_a_call(self, list_users):
        for call in self.calls:
            if call.participants == list_users:
                return True
        return False

    def get_call_members_with_user(self, user):
        for call in self.calls:
            if user in call.participants:
                return [participant for participant in call.participants if participant != user]
        return None

    def create_call_and_add(self, group_id, participants):
        call = Call(parent=self, participants=participants, nets=self.nets_dict, group_id=group_id)
        self.add_call(call)

    def get_id_from_format(self, format):
        temp = format.split("(")[1]
        temp = temp.split(")")[0]
        return int(temp)

    def add_ring(self, ring):
        self.rings.append(ring)

    def remove_ring(self, ring):
        try:
            self.rings.remove(ring)
        except Exception as e:
            self.logger.error(e)

    def create_ring(self, ringer, ringing_to):
        if ringing_to.startswith("("):
            group_id = self.get_id_from_format(ringing_to)
            ring = Ring(Parent=self, ringer=ringer, nets=self.nets_dict, group_id=group_id)
            self.add_ring(ring)
        else:
            temp_list = [ringing_to]
            ring = Ring(Parent=self, ringer=ringer, nets=self.nets_dict, ringing_to=temp_list)
            self.add_ring(ring)

    def is_group_call_exist_by_id(self, group_id):
        for call in self.calls:
            if call.is_group_call:
                if call.group_id == group_id:
                    return True
        return False

    def send_vc_data_to_call(self, vc_data, User):
        for call in self.calls:
            if call.is_user_in_a_call(User):
                call.adding_vc_data_to_user_call_thread_queue(User, vc_data)
                # call.send_vc_data_to_everyone_but_user(vc_data, User)

    def send_share_screen_data_to_call(self, share_screen_data, User):
        for call in self.calls:
            if call.is_user_in_a_call(User):
                for video_stream in call.video_streams_list:
                    if video_stream.streamer == User:
                        video_stream.adding_vc_data_to_user_call_thread_queue(User, share_screen_data)

    def add_user_to_group_call_by_id(self, User, id):
        for call in self.calls:
            if call.is_a_group_a_call:
                if call.group_id == id:
                    call.add_user_to_call(User)

    def reject_ring_by_ringer(self, ringer, User):
        for ring in self.rings:
            if ring.is_ring_by_ringer(ringer):
                ring.rejected_ring(User)
                break

    def accept_ring_by_ringer(self, ringer, User):
        for ring in self.rings:
            if ring.is_ring_by_ringer(ringer):
                ring.accepted_ring(User)
                break

    def cancel_ring_by_the_ringer(self, ringer):
        for ring in self.rings:
            if ring.is_ring_by_ringer(ringer):
                ring.cancel_ring_for_all()

    def mute_or_unmute_self_user(self, user):
        for call in self.calls:
            if call.is_user_in_a_call(user):
                call.toggle_mute_for_user(user)

    def deafen_or_undeafen_self_user(self, user):
        for call in self.calls:
            if call.is_user_in_a_call(user):
                call.toggle_deafen_for_user(user)

    def get_ring_id_by_possible_ringers(self, possible_ringers):
        for ring in self.rings:
            if ring.ringer in possible_ringers:
                return ring.ring_id
        return None

    def cancel_ring_by_id(self, ring_id):
        for ring in self.rings:
            if ring.ring_id == ring_id:
                ring.stop_ring_for_unanswered_users()
                self.rings.remove(ring)

    def create_video_stream_for_user_call(self, user):
        for call in self.calls:
            if user in call.participants:
                call.create_video_stream_of_user(user)

    def close_video_stream_for_user_call(self, user):
        for call in self.calls:
            if user in call.participants:
                call.close_video_stream_by_user(user)

    def add_spectator_to_call_stream(self, spectator, streamer):
        for call in self.calls:
            if (spectator and streamer) in call.participants:
                call.add_spectator_for_stream(spectator, streamer)

    def remove_spectator_from_call_stream(self, spectator):
        for call in self.calls:
            if spectator in call.participants:
                call.remove_spectator_for_stream(spectator)

class VideoStream:
    def __init__(self, Comms_object, streamer, call_object, group_id=None):
        self.call_parent = call_object
        self.comms_parent = Comms_object
        self.logger = logging.getLogger(__name__)
        self.stream_id = str(uuid.uuid4())
        self.streamer = streamer
        if group_id:
            self.is_group_stream = True
        else:
            self.is_group_stream = False
        self.spectators = []
        self.data_collection = []  # List of tuples containing user and vc_data
        self.stop_thread = threading.Event()  # Event for signaling the thread to stop
        self.thread = threading.Thread(target=self.process_share_screen_data)
        self.logger.info(f"Video Stream of id {self.stream_id} was created")

    def remove_spectator(self, user):
        self.spectators.remove(user)
        self.logger.info(f"{user} stopped watching stream of {self.streamer} with id {self.stream_id}")
        if len(self.spectators) == 0:
            self.stop_processing()
            self.data_collection.clear()

    def add_spectator(self, user):
        self.spectators.append(user)
        self.logger.info(f"{user} started watching stream of {self.streamer} with id {self.stream_id}")
        if len(self.spectators) == 1:
            self.stop_thread = threading.Event()  # Event for signaling the thread to stop
            self.thread = threading.Thread(target=self.process_share_screen_data)
            self.thread.start()
            self.logger.info(f"Started stream thread of id {self.stream_id}")

    def process_share_screen_data(self):
        while not self.stop_thread.is_set():
            if self.data_collection:
                user, share_screen = self.data_collection.pop(0)
                self.send_share_screen_data_to_everyone_but_user(share_screen, user)
            else:
                # Sleep or perform other tasks if the data collection is empty
                time.sleep(0.1)

    def stop_processing(self):
        self.stop_thread.set()
        self.thread.join()  # Wait for the thread to finish

    def send_share_screen_data_to_everyone_but_user(self, share_screen_data, user):
        for name, net in self.call_parent.call_nets.items():
            if name != user and net is not None and name in self.spectators:
                net.send_share_screen_data(share_screen_data, user)
                #self.logger.info(f"Sent share screen data to {name}")

    def end_stream(self):
        if len(self.spectators) > 0:
            self.stop_processing()
        self.logger.info(f"Video Stream of id {self.stream_id} ended")

    def adding_vc_data_to_user_call_thread_queue(self, user, share_screen_data):
        if len(self.spectators) > 0:
            self.data_collection.append((user, share_screen_data))
