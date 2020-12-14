import requests
import logging
import time

from .UserStore import UserStore
from .MiscConstants import *
from .User import User
from . import creds
import source.TelegramCommandsHandler as TgCommandsHandler
import source.TextSnippets as TextSnippets


class TgWorker:
    USERS = UserStore()
    MESSAGE_UPDATE_TYPE = 'message'
    CBQ_UPDATE_TYPE = 'callback_query'
    # last update offset / incoming msg limit / long polling timeout / allowed messages types
    GET_UPDATES_PARAMS = {'offset': 0, 'limit': 100, 'timeout': 30, 'allowed_updates': [MESSAGE_UPDATE_TYPE,
                                                                                        CBQ_UPDATE_TYPE]}
    REQUESTS_TIMEOUT = 1.5 * GET_UPDATES_PARAMS['timeout']
    REQUESTS_MAX_ATTEMPTS = 5
    GLOBAL_LOOP_ERROR_TIMEOUT = 60  # seconds
    SESSION = requests.session()

    REQUEST_PHONE_PARAMS = {'text': TextSnippets.REQUEST_PHONE_NUMBER_MESSAGE,
                            'reply_markup': {
                                'keyboard': [[{'text': TextSnippets.REQUEST_PHONE_NUMBER_BUTTON,
                                               'request_contact': True}]],
                                'one_time_keyboard': True,
                                'resize_keyboard': True}}

    # no need to do multiple attempts for this kind of errors
    @staticmethod
    def is_error_permanent(error_text):
        for s in TG_PERMANENT_ERRORS_SNIPPETS:
            if s in error_text:
                return True

        return False

    @staticmethod
    def send_request(method, params, custom_error_text=''):
        for a in range(TgWorker.REQUESTS_MAX_ATTEMPTS):
            try:
                response = TgWorker.SESSION.post(url=creds.TG_API_URL + method,
                                                 json=params, timeout=TgWorker.REQUESTS_TIMEOUT)

                if response:
                    json = response.json()

                    if json['ok']:
                        return json
                    else:
                        logging.error('TG bad response %s : Attempt: %s, Called: %s : Request params: %s',
                                      a, json, custom_error_text, params)

                        if TgWorker.is_error_permanent(json['description']):
                            return {}
                else:
                    logging.error('TG response failed%s : Attempt: %s, Called: %s : Request params: %s',
                                  a, response.text, custom_error_text, params)

                    if TgWorker.is_error_permanent(response.json()['description']):
                        return {}

            except Exception as e:
                logging.error('Sending TG api request %s', e)

        return {}

    @staticmethod
    def send_message(chat_id, message_object, formatting='Markdown', disable_web_preview=True):
        message_object['chat_id'] = chat_id
        message_object['parse_mode'] = formatting
        message_object['disable_web_page_preview'] = disable_web_preview
        return TgWorker.send_request('sendMessage', message_object, 'Message sending')

    @staticmethod
    def edit_message(chat_id, message_id, message_object, formatting='Markdown', disable_web_preview=True):
        message_object['chat_id'] = chat_id
        message_object['message_id'] = message_id
        message_object['parse_mode'] = formatting
        message_object['disable_web_page_preview'] = disable_web_preview
        return TgWorker.send_request('editMessageText', message_object, 'Message editing')

    # edit current "working" message of user
    @staticmethod
    def edit_user_wm(user, message_object, formatting='Markdown', from_callback=False):
        res = TgWorker.edit_message(user.get_chat_id(), user.get_wm_id(), message_object, formatting)

        if res or from_callback:
            return res

        res = TgWorker.send_message(user.get_chat_id(), message_object, formatting)
        user.set_wm_id(res['result']['message_id'])

    @staticmethod
    def delete_message(chat_id, message_id):
        params = {'chat_id': chat_id, 'message_id': message_id}
        return TgWorker.send_request('deleteMessage', params, 'Message deleting')

    @staticmethod
    def answer_cbq(cbq_id, cbq_text=None, cbq_alert=False):
        cbq_object = {'callback_query_id': cbq_id, 'show_alert': cbq_alert}
        if cbq_text is not None:
            cbq_object['text'] = cbq_text

        return TgWorker.send_request('answerCallbackQuery', cbq_object, 'Answering cbq')

    @staticmethod
    def handle_user_command(message):
        try:
            TgCommandsHandler.TelegramCommandsHandler.handle_command(message)
        except Exception as e:
            logging.error('Handling command: %s', e)

    @staticmethod
    def handle_prauth_messages(user):
        for m_id in user.get_prauth_messages():
            TgWorker.delete_message(user.get_chat_id(), m_id)

        user.clear_prauth_messages()

    @staticmethod
    def handle_message(message):
        user_id = message['from']['id']
        chat_id = message['chat']['id']
        user = None
        sent_prauth_msg_id = None

        # has user been already cached?-
        if TgWorker.USERS.has_user(user_id):
            user = TgWorker.USERS.get_user(user_id)

            if chat_id != user.get_chat_id():
                user._chat_id = chat_id

            if user.is_number_requested():
                try:
                    contact = message['contact']
                    phone_number = contact['phone_number']
                    contact_user_id = contact['user_id']

                    if contact_user_id == user_id:
                        TgWorker.USERS.authorize(user_id, phone_number)
                    else:
                        logging.error('Fake contact authorization attempt')
                        raise Exception()
                except Exception:
                    secondary_phone_params = TgWorker.REQUEST_PHONE_PARAMS.copy()
                    secondary_phone_params['text'] = TextSnippets.AUTHORIZATION_UNSUCCESSFUL
                    res = TgWorker.send_message(chat_id, secondary_phone_params)['result']
                    sent_prauth_msg_id = res['message_id']
                else:
                    # remove phone requesting keyboard now
                    res = TgWorker.send_message(chat_id, {'text': TextSnippets.AUTHORIZATION_SUCCESSFUL,
                                                      'reply_markup': {'remove_keyboard': True}})['result']

                    sent_prauth_msg_id = res['message_id']

                    # res = self.send_message(chat_id, {'text': TextSnippets.BOT_HELP_TEXT})

                    user.add_prauth_message(message['message_id'])
                    user.add_prauth_message(sent_prauth_msg_id)

                    TgWorker.handle_prauth_messages(user)
                    res = TgCommandsHandler.TelegramCommandsHandler.get_deals_list(user)
                    user.set_wm_id(res['result']['message_id'])
                    return

            elif user.is_authorized():
                TgWorker.handle_user_command(message)
                return  # no pre-authorize messages
        else:
            res = TgWorker.send_message(chat_id, TgWorker.REQUEST_PHONE_PARAMS)['result']
            sent_prauth_msg_id = res['message_id']
            user = TgWorker.USERS.add_user(user_id, User())

        user.add_prauth_message(message['message_id'])
        user.add_prauth_message(sent_prauth_msg_id)

    @staticmethod
    def handle_cb_query(cb):
        try:
            TgCommandsHandler.TelegramCommandsHandler.handle_cb_query(cb)
        except Exception as e:
            logging.error('Handling cb query: %s', e)

    @staticmethod
    def handle_update(update):
        try:
            if TgWorker.MESSAGE_UPDATE_TYPE in update:
                TgWorker.handle_message(update[TgWorker.MESSAGE_UPDATE_TYPE])
            elif TgWorker.CBQ_UPDATE_TYPE in update:
                TgWorker.handle_cb_query(update[TgWorker.CBQ_UPDATE_TYPE])
            else:
                raise Exception('Unknown update type: %s' % update)
        except Exception as e:
            logging.error('Handling TG response update: %s', e)

    @staticmethod
    def base_response_handler(json_response):
        # TODO: remove in production
        # print(json_response)

        try:
            max_update_id = TgWorker.GET_UPDATES_PARAMS['offset']
            updates = json_response['result']
            for update in updates:
                cur_update_id = update['update_id']
                if cur_update_id > max_update_id:
                    max_update_id = cur_update_id

                # TODO: thread for each user?
                TgWorker.handle_update(update)

            if updates:
                TgWorker.GET_UPDATES_PARAMS['offset'] = max_update_id + 1

        except Exception as e:
            logging.error('Base TG response exception handler: %s', e)

    # entry point
    @staticmethod
    def run():
        TgWorker.USERS.load_user_store()

        while True:
            response = TgWorker.send_request('getUpdates', TgWorker.GET_UPDATES_PARAMS, 'Main getting updates')

            # prevent logs spamming in case of network problems
            if not response:
                time.sleep(TgWorker.GLOBAL_LOOP_ERROR_TIMEOUT)

            TgWorker.base_response_handler(response)
            # TODO: multithreading timer for updates?
            TgWorker.USERS.update_user_store()
