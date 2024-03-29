import requests
from . import creds
import logging
from datetime import date

from .BitrixFieldsAliases import *
from .CbqData import *
from . import Utils
from .User import *


class BitrixWorker:
    SESSION = requests.session()
    REQUESTS_TIMEOUT = 10
    REQUESTS_MAX_ATTEMPTS = 3

    get_deals_params = {'filter': {DEAL_COURIER_FIELD_ALIAS: None,
                                   DEAL_STAGE_ALIAS: None,
                                   DEAL_DATE_ALIAS: None},
                        'select': [DEAL_ID_ALIAS, DEAL_ORDER_ALIAS, DEAL_DATE_ALIAS, DEAL_TIME_ALIAS,
                                   DEAL_COMMENT_ALIAS, DEAL_RECIPIENT_NAME_ALIAS,
                                   DEAL_RECIPIENT_SURNAME_ALIAS, DEAL_RECIPIENT_PHONE_ALIAS,
                                   DEAL_ADDRESS_ALIAS, DEAL_SUM_ALIAS, DEAL_INCOGNITO_ALIAS, DEAL_FLAT_ALIAS,
                                   DEAL_CONTACT_ID_ALIAS, DEAL_RESPONSIBLE_ID_ALIAS, DEAL_ORDER_COMMENT_ALIAS,
                                   DEAL_DELIVERY_COMMENT_ALIAS, DEAL_CLIENT_HASH_ALIAS, DEAL_TYPE_ID_ALIAS],
                        'order': {DEAL_TIME_ALIAS: 'ASC'}}

    @staticmethod
    def _send_request(user, method, params=None, custom_error_text='', notify_user=True):
        if params is None:
            params = {}

        for a in range(BitrixWorker.REQUESTS_MAX_ATTEMPTS):
            try:
                response = BitrixWorker.SESSION.post(url=creds.BITRIX_API_URL + method,
                                                     json=params, timeout=BitrixWorker.REQUESTS_TIMEOUT)

                if response and response.ok:
                    json = response.json()

                    if 'result' in json:
                        return json
                    else:
                        error = 'Bitrix bad response %s : Attempt: %s, Called: %s : Request params: %s' \
                                % (a, json, custom_error_text, params)
                        logging.error(error)
                else:
                    error = 'Bitrix response failed - %s : Attempt: %s,  Called: %s : Request params: %s' \
                            % (a, response.text, custom_error_text, params)
                    logging.error(error)

            except Exception as e:
                error = 'Sending Bitrix api request %s' % e
                logging.error(error)

        raise Exception('Bitrix request error')

    @staticmethod
    def get_deals_list(user):
        try:
            courier_field = BitrixWorker._send_request(user, 'crm.deal.userfield.get', {'id': COURIER_FIELD_ID})
            couriers = courier_field['result']['LIST']
            target_courier_id = None
            ethalon_pn = user.get_phone_numer().replace('+', '')[1:]

            for c in couriers:
                courier_phone = c['VALUE'].split('/')[-1]
                courier_phone = courier_phone.replace('-', '')
                # simple checking for number format - +7, 7, 8 etc.
                if ethalon_pn in courier_phone:
                    target_courier_id = c['ID']
                    break

            # TODO: Testing only. don't check courier every query
            # optimal caching / mapping of couriers

            if target_courier_id is None:
                return {}

            BitrixWorker.get_deals_params['filter'][DEAL_COURIER_FIELD_ALIAS] = target_courier_id

            today = date.today().isoformat()
            BitrixWorker.get_deals_params['filter'][DEAL_DATE_ALIAS] = today

            if user.get_deals_category() == DealsCategory.DEALS_IN_DELIVERY:
                BitrixWorker.get_deals_params['filter'][DEAL_STAGE_ALIAS] = [DEAL_OPEN_STATUS_ID]
            else:
                BitrixWorker.get_deals_params['filter'][DEAL_STAGE_ALIAS] = DEAL_WAITING_STATUS_LIST

            deals = BitrixWorker._send_request(user, 'crm.deal.list', BitrixWorker.get_deals_params)

            more_deals = 'next' in deals

            # getting next deal pages, if any
            while more_deals:
                get_next_deals_params = BitrixWorker.get_deals_params.copy()
                get_next_deals_params['start'] = deals['next']
                next_deals = BitrixWorker._send_request(user, 'crm.deal.list', get_next_deals_params)
                deals['result'].extend(next_deals['result'])
                more_deals = 'next' in next_deals

            return deals

        except Exception as e:
            logging.error('Getting deals %s', e)
            return None

    @staticmethod
    def change_deal_stage(user, deal_id, deal_new_stage, deal_is_late, deal_is_late_reason=''):
        try:
            return BitrixWorker._send_request(user, 'crm.deal.update',
                                              {'id': deal_id, 'fields': {DEAL_STAGE_ALIAS: deal_new_stage,
                                                                         DEAL_IS_LATE_ALIAS: deal_is_late,
                                                                         DEAL_IS_LATE_REASON_ALIAS: deal_is_late_reason}})
        except Exception as e:
            logging.error('Changing deal stage %s', e)
            return None

    @staticmethod
    def get_contact_phone(user, contact_id):
        if not contact_id:
            return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER

        try:
            res = BitrixWorker._send_request(user, 'crm.contact.get',
                                             {'id': contact_id}, notify_user=False)

            if 'result' in res:
                data = res['result']
                if data[CONTACT_HAS_PHONE_ALIAS] == CONTACT_HAS_PHONE_TRUE:
                    return data[CONTACT_PHONELIST_ALIAS][0]['VALUE']

            return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER

        except Exception as e:
            return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER

    # name + last_name
    @staticmethod
    def get_user_name(user, bitrix_user_id):
        if not bitrix_user_id:
            return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER

        try:
            res = BitrixWorker._send_request(user, 'user.get',
                                             {'id': bitrix_user_id}, notify_user=False)

            if 'result' in res:
                data = res['result'][0]
                return Utils.prepare_external_field(data, USER_NAME_ALIAS) + ' ' + \
                       Utils.prepare_external_field(data, USER_LAST_NAME_ALIAS)

            return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER

        except Exception as e:
            return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER

    @staticmethod
    def get_deal_type(user, deal_type_id):
        if not deal_type_id:
            return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER

        try:
            type_field = BitrixWorker._send_request(user, 'crm.deal.userfield.get', {'id': DEAL_TYPE_FIELD_ID})
            types = type_field['result']['LIST']

            for t in types:
                if t['ID'] == deal_type_id:
                    return Utils.prepare_external_field(t, 'VALUE')

            return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER

        except Exception as e:
            return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER
