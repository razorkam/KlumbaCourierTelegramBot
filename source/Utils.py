import re
import requests
import logging
from . import Commands, BitrixFieldMappings, TextSnippets, BitrixFieldsAliases, creds

MD_ESCAPE_PATTERN = re.compile('([*_`])')
DEAL_CLOSE_COMMAND_PATTERN = re.compile(Commands.DEAL_CLOSE_PREFIX + TextSnippets.DEAL_ACTION_DELIM + '\\d+')
DEAL_VIEW_COMMAND_PATTERN = re.compile(Commands.DEAL_VIEW_PREFIX + TextSnippets.DEAL_ACTION_DELIM + '\\d+')
BITRIX_ADDRESS_PATTERN = re.compile('(.+)\\|(\\d+\\.\\d+;\\d+\\.\\d+)')
BITRIX_DATE_PATTERN = re.compile('(\\d{4})-(\\d{2})-(\\d{2}).*')
ADDRESS_LINK_RESOLVING_SPECIAL_CHARS_PATTERN = re.compile('["]')
PHONE_VALID_SYMBOLS_LIST_PATTERN = re.compile('[^\\d,+]')

# utils network requests
SESSION = requests.session()
REQUESTS_TIMEOUT = 10
REQUESTS_MAX_ATTEMPTS = 3


def get_field(obj, key):
    if key in obj:
        return obj[key]
    else:
        return None


# remove all except digits to properly display in Tg clients
def prepare_phone_number(phone):
    return re.sub(PHONE_VALID_SYMBOLS_LIST_PATTERN, '', phone)


def escape_markdown_special_chars(str):
    return re.sub(MD_ESCAPE_PATTERN, r'\\\g<1>', str)


def _stringify_field(field):
    if field in (False, None, {}, []):
        return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER
    else:
        return field


def prepare_external_field(obj, key):
    val = get_field(obj, key)

    if type(val) is list:
        val = ', '.join(val)

    return escape_markdown_special_chars(_stringify_field(val))


def prepare_deal_time(obj, timekey):
    val = prepare_external_field(obj, timekey)

    if val in BitrixFieldMappings.DEAL_TIME_MAPPING:
        return BitrixFieldMappings.DEAL_TIME_MAPPING[val]
    else:
        return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER


def prepare_deal_incognito(obj, inckey):
    val = prepare_external_field(obj, inckey)

    if val in BitrixFieldMappings.DEAL_INCOGNITO_MAPPING:
        return BitrixFieldMappings.DEAL_INCOGNITO_MAPPING[val]
    else:
        return TextSnippets.FIELD_IS_EMPTY_PLACEHOLDER


def prepare_deal_address(obj, addrkey):
    val = prepare_external_field(obj, addrkey)

    val = re.sub(ADDRESS_LINK_RESOLVING_SPECIAL_CHARS_PATTERN, '', val)

    location_check = BITRIX_ADDRESS_PATTERN.search(val)

    if location_check:
        return location_check[1], location_check[2]

    # address, location
    return val, None


def prepare_deal_date(obj, datekey):
    val = prepare_external_field(obj, datekey)

    date_check = BITRIX_DATE_PATTERN.search(val)

    if date_check:
        return date_check[3] + '.' + date_check[2] + '.' + date_check[1]

    return val


def send_get_request_JSON(u):
    for a in range(REQUESTS_MAX_ATTEMPTS):
        try:
            response = SESSION.get(url=u).json()
            return response

        except Exception as e:
            logging.error('Sending Utils get JSON request: %s', e)
            return {}


def prepare_photos_urls(obj, client_hash):
    val = get_field(obj, client_hash)
    if not val:
        return []

    try:
        photos_urls = send_get_request_JSON(creds.CLIENT_ORDERS_STORAGE_URL + '/' + val)['photos']
        return [creds.CLIENT_ORDERS_STORAGE_URL + '/' + url for url in photos_urls]
    except Exception as e:
        logging.error('Error getting photos URLs from client storage: %s', e)
        return []

def is_deal_close_action(command):
    return DEAL_CLOSE_COMMAND_PATTERN.match(command)


def is_deal_view_action(command):
    return DEAL_VIEW_COMMAND_PATTERN.match(command)
