from enum import Enum


class UserState(Enum):
    PHONE_NUMBER_REQUESTED = 1
    AUTHORIZED = 2


class User:

    def __init__(self):
        self._phone_number = None
        self._state = UserState.PHONE_NUMBER_REQUESTED
        self._chat_id = None
        self.deal_page_borders = []
        self.cur_page_index = 0
        self.preauthorize_msg_list = []
        self._working_message_id = None
        self._deals = None

    # pickle serializing fields
    def __getstate__(self):
        return self._chat_id, self._state, self._phone_number, self._working_message_id

    def __setstate__(self, dump):
        self._chat_id, self._state, self._phone_number, self._working_message_id = dump
        self.deal_page_borders = []
        self.preauthorize_msg_list = []
        self._deals = None
        self.cur_page_index = 0

    def get_deal_pages_num(self):
        return len(self.deal_page_borders) - 1

    def get_deals_num(self):
        return len(self._deals)

    # add pre-auth message to delete later
    def add_prauth_message(self, message_id):
        self.preauthorize_msg_list.append(message_id)

    # delete all preauth messages from chat, if so
    def get_prauth_messages(self):
        return self.preauthorize_msg_list

    def clear_prauth_messages(self):
        self.preauthorize_msg_list.clear()

    def is_number_requested(self):
        return self._state == UserState.PHONE_NUMBER_REQUESTED

    def is_authorized(self):
        return self._state == UserState.AUTHORIZED

    def authorize(self, phone_number):
        self._state = UserState.AUTHORIZED
        phone_number.replace('+', '')
        self._phone_number = phone_number

    def unauthorize(self):
        self._state = UserState.PHONE_NUMBER_REQUESTED
        self._phone_number = None
        self._chat_id = None

    def get_phone_numer(self):
        return self._phone_number

    def get_chat_id(self):
        return self._chat_id

    def get_deals(self):
        return self._deals

    def set_deals(self, deals):
        self._deals = deals

    def get_cur_deals(self):
        if self._deals is None:
            return {}

        return self.get_deals()

    def get_cur_deals_page(self):
        if self._deals is None:
            return {}

        left_border_index = self.deal_page_borders[self.cur_page_index]
        right_border_index = self.deal_page_borders[self.cur_page_index + 1]

        return self._deals[left_border_index:right_border_index]

    def get_wm_id(self):
        return self._working_message_id

    def set_wm_id(self, wm_id):
        self._working_message_id = wm_id
