from .BitrixWorker import BitrixWorker
from .BitrixFieldsAliases import *
from .CbqData import *
from . import Utils, Commands
from .Deal import Deal
from .MiscConstants import *
import copy


class TelegramCommandsHandler:
    TgWorker = None
    BitrixWorker = None

    def __init__(self, TelegramWorker):
        self.TgWorker = TelegramWorker
        self.BitrixWorker = BitrixWorker(TelegramWorker)

    def handle_deal_view_action(self, user, deal_id):
        deals = user.get_cur_deals()
        deal = next((d for d in deals if d.id == deal_id), None)

        if deal is None:
            self.TgWorker.edit_user_wm(user,
                                       {'text': TextSnippets.CBQ_DEALS_WRONG_MESSAGE,
                                        'reply_markup': TO_DEALS_BUTTON_OBJ})
            return

        address_res_link = TextSnippets.ADDRESS_RESOLUTION_LINK + deal.address

        view_obj = {'reply_markup': TO_DEALS_BUTTON_OBJ,
                    'text': TextSnippets.DEAL_TEMPLATE.format(deal.id, deal.order, deal.date, deal.time, deal.comment,
                                                              deal.customer_phone, deal.customer_phone,
                                                              deal.recipient_name, deal.recipient_surname,
                                                              deal.recipient_phone, deal.recipient_phone,
                                                              deal.address, address_res_link, deal.sum,
                                                              deal.responsible_name, deal.close_command)}

        self.TgWorker.edit_user_wm(user, view_obj)

    def handle_deal_closing_dialog(self, user, deal_id):
        dialog_keyboard = copy.deepcopy(CLOSE_DEAL_DIALOG_BUTTON_OBJ)
        dialog_keyboard['inline_keyboard'][0][0]['callback_data'] += CBQ_DELIM + deal_id

        self.TgWorker.edit_user_wm(user,
                                   {'text': TextSnippets.DEAL_CLOSING_DIALOG_TEXT.format(deal_id),
                                    'reply_markup': dialog_keyboard})

    def handle_deal_closing(self, user, deal_id):
        deals = user.get_cur_deals()

        if not deals:
            self.TgWorker.edit_user_wm(user,
                                       {'text': TextSnippets.CBQ_DEALS_WRONG_MESSAGE,
                                        'reply_markup': TO_DEALS_BUTTON_OBJ})
            return

        deal = next((d for d in deals if d.id == deal_id), None)

        if deal is None:
            self.TgWorker.edit_user_wm(user,
                                       {'text': TextSnippets.CBQ_DEALS_WRONG_MESSAGE,
                                        'reply_markup': TO_DEALS_BUTTON_OBJ})
            return

        new_stage = DEAL_CLOSED_STATUS_ID

        result = self.BitrixWorker.change_deal_stage(user, deal_id, new_stage)

        if result is not None:
            self.get_deals_list(user)

    def get_deals_list(self, user, is_callback=False):
        deals = self.BitrixWorker.get_deals_list(user)

        if deals is None:
            return None

        if not deals or ('result' not in deals):
            msg_obj = {'text': TextSnippets.YOU_HAVE_NO_DEALS,
                       'reply_markup': REFRESH_DEALS_BUTTON_OBJ}

            if user.get_wm_id() is None:
                return self.TgWorker.send_message(user.get_chat_id(), msg_obj)
            else:
                return self.TgWorker.edit_user_wm(user, msg_obj, from_callback=is_callback)

        deals_msg = self._generate_deals_preview_data(deals, user)

        user.cur_page_index = 0

        # in case of no main menu, send deals list first time
        if user.get_wm_id() is None:
            return self.TgWorker.send_message(user.get_chat_id(), deals_msg)
        else:
            return self.TgWorker.edit_user_wm(user, deals_msg, from_callback=is_callback)

    def handle_command(self, message):
        user_id = message['from']['id']
        chat_id = message['chat']['id']
        user = self.TgWorker.USERS.get_user(user_id)

        if 'text' not in message:
            # self.TgWorker.edit_user_wm(user, {'text': TextSnippets.UNKNOWN_NONTEXT_COMMAND + '\n' +
            #                                           TextSnippets.BOT_HELP_TEXT,
            #                                   'reply_markup': TO_DEALS_BUTTON_OBJ})

            # self.get_deals_list(user)
            self.TgWorker.delete_message(chat_id, message['message_id'])
            return

        command = message['text']

        # if command == Commands.GET_DEALS_LIST:
        #     self.get_deals_list(user)
        # elif command == Commands.HELP:
        #     self.TgWorker.edit_user_wm(user, {'text': TextSnippets.BOT_HELP_EXTENDED_TEXT,
        #                                       'reply_markup': TO_MAIN_MENU_BUTTON_OBJ})
        if command == Commands.START:
            # self.TgWorker.edit_user_wm(user, {'text': TextSnippets.BOT_HELP_TEXT})
            self.get_deals_list(user)

        # elif command == Commands.REAUTHORIZE:
        #     res = self.TgWorker.send_message(chat_id, self.TgWorker.REQUEST_PHONE_PARAMS)['result']
        #     user.add_prauth_message(res['message_id'])
        #     user.add_prauth_message(user.get_wm_id())
        #     user.unauthorize()
        elif Utils.is_deal_close_action(command):
            deal_id = command.split(TextSnippets.DEAL_ACTION_DELIM)[1]
            self.handle_deal_closing_dialog(user, deal_id)
        elif Utils.is_deal_view_action(command):
            deal_id = command.split(TextSnippets.DEAL_ACTION_DELIM)[1]
            self.handle_deal_view_action(user, deal_id)
        else:
            pass
            # prepared_msg = Utils.escape_markdown_special_chars(command)
            # self.TgWorker.edit_user_wm(user, {'text': TextSnippets.UNKNOWN_COMMAND % prepared_msg + '\n' +
            #                                           TextSnippets.BOT_HELP_TEXT})

            # self.get_deals_list(user)

        self.TgWorker.delete_message(chat_id, message['message_id'])

    def _generate_deals_preview_data(self, deals, user):
        deals_msg = {'text': TextSnippets.DEAL_HEADER % (len(deals['result'])),
                     'reply_markup': {}}

        deals_lst = []

        msg_size = len(deals_msg['text'])
        header_size = msg_size

        # begin, past-to-end
        user.deal_page_borders = [0, 0]
        user.cur_page_index = 0
        first_page_formed = False

        for d in deals['result']:
            deal_id = Utils.prepare_external_field(d, DEAL_ID_ALIAS)
            time = Utils.prepare_deal_time(d, DEAL_TIME_ALIAS)
            comment = Utils.prepare_external_field(d, DEAL_COMMENT_ALIAS)
            incognito = Utils.prepare_deal_incognito(d, DEAL_INCOGNITO_ALIAS)
            flat = Utils.prepare_external_field(d, DEAL_FLAT_ALIAS)
            recipient_phone = Utils.prepare_external_field(d, DEAL_RECIPIENT_PHONE_ALIAS)
            sum = Utils.prepare_external_field(d, DEAL_SUM_ALIAS)
            date = Utils.prepare_deal_date(d, DEAL_DATE_ALIAS)
            order = Utils.prepare_external_field(d, DEAL_ORDER_ALIAS)
            recipient_name = Utils.prepare_external_field(d, DEAL_RECIPIENT_NAME_ALIAS)
            recipient_surname = Utils.prepare_external_field(d, DEAL_RECIPIENT_SURNAME_ALIAS)

            contact_id = Utils.get_field(d, DEAL_CONTACT_ID_ALIAS)
            customer_phone = self.BitrixWorker.get_contact_phone(user, contact_id)

            address, location = Utils.prepare_deal_address(d, DEAL_ADDRESS_ALIAS)

            deal_close_command = Commands.DEAL_CLOSE_PREFIX + '\\' + TextSnippets.DEAL_ACTION_DELIM + deal_id
            deal_view_command = Commands.DEAL_VIEW_PREFIX + '\\' + TextSnippets.DEAL_ACTION_DELIM + deal_id

            address_res_link = TextSnippets.ADDRESS_RESOLUTION_LINK + address

            responsible_id = Utils.get_field(d, DEAL_RESPONSIBLE_ID_ALIAS)
            responsible_name = self.BitrixWorker.get_user_name(user, responsible_id)

            deal_representation = (TextSnippets.DEAL_PREVIEW_TEMPLATE.format(deal_view_command,
                                                                             time, comment,
                                                                             incognito, address, address_res_link,
                                                                             flat, recipient_phone, recipient_phone,
                                                                             sum,
                                                                             responsible_name, deal_close_command)
                                   + '\n\n' + TextSnippets.DEAL_DELIMETER + '\n\n')

            cur_deal_len = len(deal_representation)
            msg_size += cur_deal_len

            if msg_size >= TG_MESSAGE_SIZE_LIMIT:
                first_page_formed = True
                last_elt = user.deal_page_borders[-1]
                user.deal_page_borders.append(last_elt + 1)
                msg_size = header_size + cur_deal_len
            else:
                user.deal_page_borders[-1] += 1

            if not first_page_formed:
                deals_msg['text'] += deal_representation

            deal_obj = Deal()
            deal_obj.id = deal_id
            deal_obj.time = time
            deal_obj.comment = comment
            deal_obj.incognito = incognito
            deal_obj.address = address
            deal_obj.address_res_link = address_res_link
            deal_obj.flat = flat
            deal_obj.recipient_phone = recipient_phone
            deal_obj.sum = sum
            deal_obj.date = date
            deal_obj.order = order
            deal_obj.recipient_name = recipient_name
            deal_obj.recipient_surname = recipient_surname
            deal_obj.customer_phone = customer_phone
            deal_obj.close_command = deal_close_command
            deal_obj.view_command = deal_view_command
            deal_obj.address = address
            deal_obj.location = location
            deal_obj.responsible_name = responsible_name

            deals_lst.append(deal_obj)

        pages_num = user.get_deal_pages_num()

        if pages_num > 1:
            deals_msg['text'] += TextSnippets.DEAL_PAGE_FOOTER.format(user.cur_page_index+1, pages_num)

        if pages_num < 2:
            deals_msg['reply_markup'] = REFRESH_DEALS_BUTTON_OBJ
        else:
            deals_msg['reply_markup'] = TO_NEXT_DEALS_BUTTON_OBJ

        user.set_deals(deals_lst)
        return deals_msg

    def render_cur_deals_page(self, user):
        page_deals = user.get_cur_deals_page()
        deals_msg = {'text': TextSnippets.DEAL_HEADER % (user.get_deals_num()),
                     'reply_markup': {}}

        for d in page_deals:
            deal_representation = (TextSnippets.DEAL_PREVIEW_TEMPLATE.format(d.view_command,
                                                                             d.time, d.comment,
                                                                             d.incognito, d.address, d.address_res_link,
                                                                             d.flat, d.recipient_phone,
                                                                             d.recipient_phone,
                                                                             d.sum,
                                                                             d.responsible_name, d.close_command)
                                   + '\n\n' + TextSnippets.DEAL_DELIMETER + '\n\n')

            deals_msg['text'] += deal_representation

        pages_num = user.get_deal_pages_num()

        if pages_num > 1:
            deals_msg['text'] += TextSnippets.DEAL_PAGE_FOOTER.format(user.cur_page_index+1, pages_num)

        if user.cur_page_index is 0:
            deals_msg['reply_markup'] = TO_NEXT_DEALS_BUTTON_OBJ
        elif user.cur_page_index is pages_num - 1:
            deals_msg['reply_markup'] = TO_PREV_DEALS_BUTTON_OBJ
        else:
            deals_msg['reply_markup'] = TO_BOTH_DEALS_BUTTON_OBJ

        # in case of no main menu, send deals list first time
        if user.get_wm_id() is None:
            return self.TgWorker.send_message(user.get_chat_id(), deals_msg)
        else:
            return self.TgWorker.edit_user_wm(user, deals_msg)

    def handle_deals_pages_cb(self, cbq, user, cb_data):
        cbq_id = cbq['id']

        if cb_data == DEALS_BUTTON_NEXT_DATA and user.cur_page_index + 1 < user.get_deal_pages_num():
            user.cur_page_index += 1
        elif cb_data == DEALS_BUTTON_PREV_DATA and user.cur_page_index > 0:
            user.cur_page_index -= 1
        else:
            self.TgWorker.answer_cbq(cbq_id, TextSnippets.CBQ_UNKNOW_COMMAND, True)
            raise Exception('Handling cb query: unknown cb data %s' % cb_data)

        self.render_cur_deals_page(user)
        self.TgWorker.answer_cbq(cbq_id)

    def handle_main_menu_cb(self, cbq, user):
        self.TgWorker.edit_user_wm(user, {'text': TextSnippets.BOT_HELP_TEXT})
        self.TgWorker.answer_cbq(cbq['id'])

    def handle_to_deals_cb(self, cbq, user):
        self.get_deals_list(user, True)
        self.TgWorker.answer_cbq(cbq['id'])

    def handle_close_deal_cb(self, cbq, user, deal_id):
        self.handle_deal_closing(user, deal_id)
        self.TgWorker.answer_cbq(cbq['id'])

    def handle_cb_query(self, cbq):
        # all cbq's are expected in format 'command_data'
        cb_command = cbq['data']
        cb_data = None
        user_id = cbq['from']['id']
        user = self.TgWorker.USERS.get_user(user_id)

        if CBQ_DELIM in cb_command:
            splitted = cbq['data'].split(CBQ_DELIM)
            cb_command = splitted[0]
            cb_data = splitted[1]

        if cb_command == TO_MAIN_MENU_CALLBACK_DATA:
            self.handle_main_menu_cb(cbq, user)
        elif cb_command == TO_DEALS_CALLBACK_DATA:
            self.handle_to_deals_cb(cbq, user)
        elif cb_command == CLOSE_DEAL_CALLBACK_PREFIX:
            self.handle_close_deal_cb(cbq, user, cb_data)
        elif cb_command == DEALS_CALLBACK_PREFIX:
            self.handle_deals_pages_cb(cbq, user, cb_data)
        else:
            self.TgWorker.answer_cbq(cbq['id'], TextSnippets.CBQ_UNKNOW_COMMAND, True)
            raise Exception('Handling cb query: unknown cb command %s' % cb_command)
