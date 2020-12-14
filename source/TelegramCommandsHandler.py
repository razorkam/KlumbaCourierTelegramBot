from .BitrixFieldsAliases import *
from .CbqData import *
from . import Utils, Commands
from .Deal import Deal
from .MiscConstants import *
import source.TelegramWorker
import source.BitrixWorker as BW
from .User import *
import copy


class TelegramCommandsHandler:

    @staticmethod
    def handle_deal_view_action(user, deal_id):
        deals = user.get_cur_deals()
        deal = next((d for d in deals if d._id == deal_id), None)

        if deal is None:
            source.TelegramWorker.TgWorker.edit_user_wm(user,
                                  {'text': TextSnippets.CBQ_DEALS_WRONG_MESSAGE,
                                   'reply_markup': TO_DEALS_BUTTON_OBJ})
            return

        address_res_link = TextSnippets.ADDRESS_RESOLUTION_LINK + deal._address

        if user.get_deals_category() == DealsCategory.DEALS_WAITING:
            view_text = TextSnippets.DEAL_TEMPLATE_WAITING.format(deal._id, deal._order, deal._date, deal._time,
                                                                      deal._comment,
                                                                      deal._order_comment, deal._delivery_comment,
                                                                      deal._customer_phone, deal._customer_phone,
                                                                      deal._recipient_name, deal._recipient_surname,
                                                                      deal._recipient_phone, deal._recipient_phone,
                                                                      deal._address, address_res_link, deal._deal_sum,
                                                                      deal._responsible_name)
        else:
            view_text = TextSnippets.DEAL_TEMPLATE_DELIVERY.format(deal._id, deal._order, deal._date, deal._time,
                                                                      deal._comment,
                                                                      deal._order_comment, deal._delivery_comment,
                                                                      deal._customer_phone, deal._customer_phone,
                                                                      deal._recipient_name, deal._recipient_surname,
                                                                      deal._recipient_phone, deal._recipient_phone,
                                                                      deal._address, address_res_link, deal._deal_sum,
                                                                      deal._responsible_name,
                                                                      deal._close_command)

        view_obj = {'reply_markup': TO_DEALS_BUTTON_OBJ,
                    'text': view_text}

        source.TelegramWorker.TgWorker.edit_user_wm(user, view_obj)

    @staticmethod
    def handle_deal_closing_dialog(user, deal_id):
        dialog_keyboard = copy.deepcopy(CLOSE_DEAL_DIALOG_BUTTON_OBJ)
        dialog_keyboard['inline_keyboard'][0][0]['callback_data'] += CBQ_DELIM + deal_id

        source.TelegramWorker.TgWorker.edit_user_wm(user,
                              {'text': TextSnippets.DEAL_CLOSING_DIALOG_TEXT.format(deal_id),
                               'reply_markup': dialog_keyboard})

    @staticmethod
    def handle_deal_closing(user, deal_id):
        if user.get_deals_category() == DealsCategory.DEALS_WAITING:
            source.TelegramWorker.TgWorker.edit_user_wm(user,
                                                        {'text': TextSnippets.CBQ_CLOSING_WAITING_DEAL_ERROR,
                                                         'reply_markup': TO_DEALS_BUTTON_OBJ})
            return

        deals = user.get_cur_deals()

        if not deals:
            source.TelegramWorker.TgWorker.edit_user_wm(user,
                                  {'text': TextSnippets.CBQ_DEALS_WRONG_MESSAGE,
                                   'reply_markup': TO_DEALS_BUTTON_OBJ})
            return

        deal = next((d for d in deals if d._id == deal_id), None)

        if deal is None:
            source.TelegramWorker.TgWorker.edit_user_wm(user,
                                  {'text': TextSnippets.CBQ_DEALS_WRONG_MESSAGE,
                                   'reply_markup': TO_DEALS_BUTTON_OBJ})
            return

        new_stage = DEAL_CLOSED_STATUS_ID

        result = BW.BitrixWorker.change_deal_stage(user, deal_id, new_stage)

        if result is not None:
            TelegramCommandsHandler.get_deals_list(user)
        else:
            source.TelegramWorker.TgWorker.edit_user_wm(user, {'text': TextSnippets.ERROR_HANDLING_DEAL_ACTION,
                                                        'reply_markup': TO_DEALS_BUTTON_OBJ})

    @staticmethod
    def get_deals_list(user, is_callback=False, new_deals_category=None):
        if new_deals_category:
            user.set_deals_category(new_deals_category)

        deals = BW.BitrixWorker.get_deals_list(user)

        if deals is None:
            source.TelegramWorker.TgWorker.edit_user_wm(user, {'text': TextSnippets.ERROR_GETTING_DEALS,
                                                        'reply_markup': REFRESH_DEALS_BUTTON_OBJ})

            return None

        if not deals or ('result' not in deals):
            if user.get_deal_category() == DealsCategory.DEALS_IN_DELIVERY:
                error_text = TextSnippets.YOU_HAVE_NO_DEALS_IN_DELIVERY
            else:
                error_text = TextSnippets.YOU_HAVE_NO_DEALS_WAITING

            msg_obj = {'text': error_text,
                       'reply_markup': REFRESH_DEALS_BUTTON_OBJ}

            if user.get_wm_id() is None:
                return source.TelegramWorker.TgWorker.send_message(user.get_chat_id(), msg_obj)
            else:
                return source.TelegramWorker.TgWorker.edit_user_wm(user, msg_obj, from_callback=is_callback)

        deals_msg = TelegramCommandsHandler._generate_deals_preview_data(deals, user)

        user.cur_page_index = 0

        # in case of no main menu, send deals list first time
        if user.get_wm_id() is None:
            return source.TelegramWorker.TgWorker.send_message(user.get_chat_id(), deals_msg)
        else:
            return source.TelegramWorker.TgWorker.edit_user_wm(user, deals_msg, from_callback=is_callback)

    @staticmethod
    def handle_command(message):
        user_id = message['from']['id']
        chat_id = message['chat']['id']
        user = source.TelegramWorker.TgWorker.USERS.get_user(user_id)

        if 'text' not in message:
            source.TelegramWorker.TgWorker.delete_message(chat_id, message['message_id'])
            return

        command = message['text']

        if command == Commands.START:
            TelegramCommandsHandler.get_deals_list(user)
        elif Utils.is_deal_close_action(command):
            deal_id = command.split(TextSnippets.DEAL_ACTION_DELIM)[1]
            TelegramCommandsHandler.handle_deal_closing_dialog(user, deal_id)
        elif Utils.is_deal_view_action(command):
            deal_id = command.split(TextSnippets.DEAL_ACTION_DELIM)[1]
            TelegramCommandsHandler.handle_deal_view_action(user, deal_id)
        else:
            pass

        source.TelegramWorker.TgWorker.delete_message(chat_id, message['message_id'])

    @staticmethod
    def _get_deal_representation(user, deal):
        if user.get_deals_category() == DealsCategory.DEALS_IN_DELIVERY:
            deal_representation = (TextSnippets.DEAL_DELIVERY_PREVIEW_TEMPLATE.format(deal._view_command,
                                                                                      deal._time, deal._comment,
                                                                                      deal._order_comment,
                                                                                      deal._delivery_comment,
                                                                                      deal._incognito, deal._address,
                                                                                      deal._address_res_link,
                                                                                      deal._flat, deal._recipient_phone,
                                                                                      deal._recipient_phone,
                                                                                      deal._deal_sum,
                                                                                      deal._responsible_name,
                                                                                      deal._close_command)
                                   + '\n\n' + TextSnippets.DEAL_DELIMETER + '\n\n')
        else:
            deal_representation = (TextSnippets.DEAL_WAITING_PREVIEW_TEMPLATE.format(deal._view_command,
                                                                                     deal._date, deal._time,
                                                                                     deal._responsible_name)
                                   + '\n\n' + TextSnippets.DEAL_DELIMETER + '\n\n')

        return deal_representation

    @staticmethod
    def _generate_deals_preview_data(deals, user):
        if user.get_deals_category() == DealsCategory.DEALS_IN_DELIVERY:
            header_text = TextSnippets.DEALS_DELIVERY_HEADER
        else:
            header_text = TextSnippets.DEALS_WAITING_HEADER

        deals_msg = {'text': header_text % (len(deals['result'])),
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
            order_comment = Utils.prepare_external_field(d, DEAL_ORDER_COMMENT_ALIAS)
            delivery_comment = Utils.prepare_external_field(d, DEAL_DELIVERY_COMMENT_ALIAS)
            incognito = Utils.prepare_deal_incognito(d, DEAL_INCOGNITO_ALIAS)
            flat = Utils.prepare_external_field(d, DEAL_FLAT_ALIAS)
            recipient_phone = Utils.prepare_phone_number(Utils.prepare_external_field(d, DEAL_RECIPIENT_PHONE_ALIAS))
            deal_sum = Utils.prepare_external_field(d, DEAL_SUM_ALIAS)
            date = Utils.prepare_deal_date(d, DEAL_DATE_ALIAS)
            order = Utils.prepare_external_field(d, DEAL_ORDER_ALIAS)
            recipient_name = Utils.prepare_external_field(d, DEAL_RECIPIENT_NAME_ALIAS)
            recipient_surname = Utils.prepare_external_field(d, DEAL_RECIPIENT_SURNAME_ALIAS)

            contact_id = Utils.get_field(d, DEAL_CONTACT_ID_ALIAS)
            customer_phone = Utils.prepare_phone_number(BW.BitrixWorker.get_contact_phone(user, contact_id))

            address, location = Utils.prepare_deal_address(d, DEAL_ADDRESS_ALIAS)

            deal_close_command = Commands.DEAL_CLOSE_PREFIX + '\\' + TextSnippets.DEAL_ACTION_DELIM + deal_id
            deal_view_command = Commands.DEAL_VIEW_PREFIX + '\\' + TextSnippets.DEAL_ACTION_DELIM + deal_id

            address_res_link = TextSnippets.ADDRESS_RESOLUTION_LINK + address

            responsible_id = Utils.get_field(d, DEAL_RESPONSIBLE_ID_ALIAS)
            responsible_name = BW.BitrixWorker.get_user_name(user, responsible_id)

            deal_obj = Deal(deal_id, order, date, time, comment, order_comment, delivery_comment, incognito,
                            customer_phone, address, address_res_link, location, deal_sum, deal_close_command,
                            deal_view_command, flat, recipient_phone, recipient_name, recipient_surname,
                            responsible_name)

            deals_lst.append(deal_obj)

            deal_representation = TelegramCommandsHandler._get_deal_representation(user, deal_obj)

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

        pages_num = user.get_deal_pages_num()

        if pages_num > 1:
            deals_msg['text'] += TextSnippets.DEAL_PAGE_FOOTER.format(user.cur_page_index + 1, pages_num)

        if pages_num < 2:
            deals_msg['reply_markup'] = REFRESH_DEALS_BUTTON_OBJ
        else:
            deals_msg['reply_markup'] = TO_NEXT_DEALS_BUTTON_OBJ

        user.set_deals(deals_lst)
        return deals_msg

    @staticmethod
    def render_cur_deals_page(user):
        page_deals = user.get_cur_deals_page()

        if user.get_deals_category() == DealsCategory.DEALS_IN_DELIVERY:
            header_text = TextSnippets.DEALS_DELIVERY_HEADER
        else:
            header_text = TextSnippets.DEALS_WAITING_HEADER

        deals_msg = {'text': header_text % (user.get_deals_num()),
                     'reply_markup': {}}

        for d in page_deals:
            deal_representation = TelegramCommandsHandler._get_deal_representation(user, d)

            deals_msg['text'] += deal_representation

        pages_num = user.get_deal_pages_num()

        if pages_num > 1:
            deals_msg['text'] += TextSnippets.DEAL_PAGE_FOOTER.format(user.cur_page_index + 1, pages_num)

        if user.cur_page_index is 0:
            deals_msg['reply_markup'] = TO_NEXT_DEALS_BUTTON_OBJ
        elif user.cur_page_index is pages_num - 1:
            deals_msg['reply_markup'] = TO_PREV_DEALS_BUTTON_OBJ
        else:
            deals_msg['reply_markup'] = TO_BOTH_DEALS_BUTTON_OBJ

        # in case of no main menu, send deals list first time
        if user.get_wm_id() is None:
            return source.TelegramWorker.TgWorker.send_message(user.get_chat_id(), deals_msg)
        else:
            return source.TelegramWorker.TgWorker.edit_user_wm(user, deals_msg)

    @staticmethod
    def handle_deals_pages_cb(cbq, user, cb_data):
        cbq_id = cbq['id']

        if cb_data == DEALS_BUTTON_NEXT_DATA and user.cur_page_index + 1 < user.get_deal_pages_num():
            user.cur_page_index += 1
        elif cb_data == DEALS_BUTTON_PREV_DATA and user.cur_page_index > 0:
            user.cur_page_index -= 1
        else:
            source.TelegramWorker.TgWorker.answer_cbq(cbq_id, TextSnippets.CBQ_UNKNOW_COMMAND, True)
            raise Exception('Handling cb query: unknown cb data %s' % cb_data)

        TelegramCommandsHandler.render_cur_deals_page(user)
        source.TelegramWorker.TgWorker.answer_cbq(cbq_id)

    @staticmethod
    def handle_to_deals_cb(cbq, user):
        TelegramCommandsHandler.get_deals_list(user, True)
        source.TelegramWorker.TgWorker.answer_cbq(cbq['id'])

    @staticmethod
    def handle_close_deal_cb(cbq, user, deal_id):
        TelegramCommandsHandler.handle_deal_closing(user, deal_id)
        source.TelegramWorker.TgWorker.answer_cbq(cbq['id'])

    @staticmethod
    def handle_refresh_deals_cb(cbq, user, cb_data):
        if cb_data == REFRESH_DEALS_DELIVERY_DATA:
            new_deals_category = DealsCategory.DEALS_IN_DELIVERY
        else:
            new_deals_category = DealsCategory.DEALS_WAITING

        TelegramCommandsHandler.get_deals_list(user, True, new_deals_category)
        source.TelegramWorker.TgWorker.answer_cbq(cbq['id'])

    @staticmethod
    def handle_cb_query(cbq):
        # all cbq's are expected in format 'command' / 'command_data'
        cb_command = cbq['data']
        cb_data = None
        user_id = cbq['from']['id']
        user = source.TelegramWorker.TgWorker.USERS.get_user(user_id)

        if CBQ_DELIM in cb_command:
            splitted = cbq['data'].split(CBQ_DELIM)
            cb_command = splitted[0]
            cb_data = splitted[1]

        if cb_command == REFRESH_DEALS_CALLBACK_PREFIX:
            TelegramCommandsHandler.handle_refresh_deals_cb(cbq, user, cb_data)
        elif cb_command == TO_DEALS_CALLBACK_DATA:
            TelegramCommandsHandler.handle_to_deals_cb(cbq, user)
        elif cb_command == CLOSE_DEAL_CALLBACK_PREFIX:
            TelegramCommandsHandler.handle_close_deal_cb(cbq, user, cb_data)
        elif cb_command == DEALS_CALLBACK_PREFIX:
            TelegramCommandsHandler.handle_deals_pages_cb(cbq, user, cb_data)
        else:
            source.TelegramWorker.TgWorker.answer_cbq(cbq['id'], TextSnippets.CBQ_UNKNOW_COMMAND, True)
            raise Exception('Handling cb query: unknown cb command %s' % cb_command)
