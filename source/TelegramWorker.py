from .UserStore import UserStore
from .User import User
from . import creds
from .TelegramCommandsHandler import *
import requests
import logging
import time


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
    PROXIES = [creds.HTTPS_PROXY_GERMANY, creds.HTTPS_PROXY_FINLAND]
    CommandsHandler = None

    REQUEST_PHONE_PARAMS = {'text': TextSnippets.REQUEST_PHONE_NUMBER_MESSAGE,
                            'reply_markup': {
                                'keyboard': [[{'text': TextSnippets.REQUEST_PHONE_NUMBER_BUTTON,
                                               'request_contact': True}]],
                                'one_time_keyboard': True,
                                'resize_keyboard': True}}

    def __init__(self):
        self.CommandsHandler = TelegramCommandsHandler(self)

    # no need to do multiple attempts for this kind of errors
    def is_error_permanent(self, error_text):
        for s in TG_PERMANENT_ERRORS_SNIPPETS:
            if s in error_text:
                return True

        return False

    def send_request(self, method, params, custom_error_text=''):
        proxy_index = 0

        for a in range(self.REQUESTS_MAX_ATTEMPTS):
            try:
                response = self.SESSION.post(url=creds.TG_API_URL + method, proxies=self.PROXIES[proxy_index],
                                             json=params, timeout=self.REQUESTS_TIMEOUT)

                if response:
                    json = response.json()

                    if json['ok']:
                        return json
                    else:
                        logging.error('TG bad response %s : Attempt: %s, Called: %s : Request params: %s',
                                      a, json, custom_error_text, params)

                        if self.is_error_permanent(json['description']):
                            return {}
                else:
                    logging.error('TG response failed%s : Attempt: %s, Called: %s : Request params: %s',
                                  a, response.text, custom_error_text, params)

                    if self.is_error_permanent(response.json()['description']):
                        return {}

            except requests.exceptions.ProxyError:
                logging.error('Proxy #{} got connection error.'.format(proxy_index))

                if proxy_index < (len(self.PROXIES) - 1):
                    proxy_index += 1
                    logging.info('Trying proxy #{}'.format(proxy_index))
                else:
                    logging.error('All proxies got connection problems. Request failed')

            except Exception as e:
                logging.error('Sending TG api request %s', e)

        return {}

    def send_message(self, chat_id, message_object, formatting='Markdown', disable_web_preview=True):
        message_object['chat_id'] = chat_id
        message_object['parse_mode'] = formatting
        message_object['disable_web_page_preview'] = disable_web_preview
        return self.send_request('sendMessage', message_object, 'Message sending')

    def edit_message(self, chat_id, message_id, message_object, formatting='Markdown', disable_web_preview=True):
        message_object['chat_id'] = chat_id
        message_object['message_id'] = message_id
        message_object['parse_mode'] = formatting
        message_object['disable_web_page_preview'] = disable_web_preview
        return self.send_request('editMessageText', message_object, 'Message editing')

    # edit current "working" message of user
    def edit_user_wm(self, user, message_object, formatting='Markdown', from_callback=False):
        res = self.edit_message(user.get_chat_id(), user.get_wm_id(), message_object, formatting)

        if res or from_callback:
            return res

        res = self.send_message(user.get_chat_id(), message_object, formatting)
        user.set_wm_id(res['result']['message_id'])

    def delete_message(self, chat_id, message_id):
        params = {'chat_id': chat_id, 'message_id': message_id}
        return self.send_request('deleteMessage', params, 'Message deleting')

    def answer_cbq(self, cbq_id, cbq_text=None, cbq_alert=False):
        cbq_object = {'callback_query_id': cbq_id, 'show_alert': cbq_alert}
        if cbq_text is not None:
            cbq_object['text'] = cbq_text

        return self.send_request('answerCallbackQuery', cbq_object, 'Answering cbq')

    def handle_user_command(self, message):
        try:
            self.CommandsHandler.handle_command(message)
        except Exception as e:
            logging.error('Handling command: %s', e)

    def handle_prauth_messages(self, user):
        for m_id in user.get_prauth_messages():
            self.delete_message(user.get_chat_id(), m_id)

        user.clear_prauth_messages()

    def handle_message(self, message):
        user_id = message['from']['id']
        chat_id = message['chat']['id']
        user = None
        sent_prauth_msg_id = None

        # has user been already cached?-
        if self.USERS.has_user(user_id):
            user = self.USERS.get_user(user_id)

            if chat_id != user.get_chat_id():
                user._chat_id = chat_id

            if user.is_number_requested():
                try:
                    contact = message['contact']
                    phone_number = contact['phone_number']
                    contact_user_id = contact['user_id']

                    if contact_user_id == user_id:
                        self.USERS.authorize(user_id, phone_number)
                    else:
                        logging.error('Fake contact authorization attempt')
                        raise Exception()
                except Exception:
                    secondary_phone_params = self.REQUEST_PHONE_PARAMS.copy()
                    secondary_phone_params['text'] = TextSnippets.AUTHORIZATION_UNSUCCESSFUL
                    res = self.send_message(chat_id, secondary_phone_params)['result']
                    sent_prauth_msg_id = res['message_id']
                else:
                    # remove phone requesting keyboard now
                    res = self.send_message(chat_id, {'text': TextSnippets.AUTHORIZATION_SUCCESSFUL,
                                                'reply_markup': {'remove_keyboard': True}})['result']

                    sent_prauth_msg_id = res['message_id']

                    # res = self.send_message(chat_id, {'text': TextSnippets.BOT_HELP_TEXT})

                    user.add_prauth_message(message['message_id'])
                    user.add_prauth_message(sent_prauth_msg_id)

                    self.handle_prauth_messages(user)
                    res = self.CommandsHandler.get_deals_list(user)
                    user.set_wm_id(res['result']['message_id'])
                    return

            elif user.is_authorized():
                self.handle_user_command(message)
                return # no pre-authorize messages
        else:
            res = self.send_message(chat_id, self.REQUEST_PHONE_PARAMS)['result']
            sent_prauth_msg_id = res['message_id']
            user = self.USERS.add_user(user_id, User())

        user.add_prauth_message(message['message_id'])
        user.add_prauth_message(sent_prauth_msg_id)

    def handle_cb_query(self, cb):
        try:
            self.CommandsHandler.handle_cb_query(cb)
        except Exception as e:
            logging.error('Handling cb query: %s', e)

    def handle_update(self, update):
        try:
            if self.MESSAGE_UPDATE_TYPE in update:
                self.handle_message(update[self.MESSAGE_UPDATE_TYPE])
            elif self.CBQ_UPDATE_TYPE in update:
                self.handle_cb_query(update[self.CBQ_UPDATE_TYPE])
            else:
                raise Exception('Unknown update type: %s' % update)
        except Exception as e:
            logging.error('Handling TG response update: %s', e)

    def base_response_handler(self, json_response):
        # TODO: remove in production
        # print(json_response)

        try:
            max_update_id = self.GET_UPDATES_PARAMS['offset']
            updates = json_response['result']
            for update in updates:
                cur_update_id = update['update_id']
                if cur_update_id > max_update_id:
                    max_update_id = cur_update_id

                # TODO: thread for each user?
                self.handle_update(update)

            if updates:
                self.GET_UPDATES_PARAMS['offset'] = max_update_id + 1

        except Exception as e:
            logging.error('Base TG response exception handler: %s', e)

    # entry point
    def run(self):
        self.USERS.load_user_store()

        while True:
            response = self.send_request('getUpdates', self.GET_UPDATES_PARAMS, 'Main getting updates')

            # prevent logs spamming in case of network problems
            if not response:
                time.sleep(self.GLOBAL_LOOP_ERROR_TIMEOUT)

            self.base_response_handler(response)
            # TODO: multithreading timer for updates?
            self.USERS.update_user_store()
