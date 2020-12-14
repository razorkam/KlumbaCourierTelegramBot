from source import TextSnippets

CBQ_DELIM = '_'

# to current deals
TO_DEALS_CALLBACK_DATA = 'todeals'

# deals pagination
DEALS_CALLBACK_PREFIX = 'deals'
DEALS_BUTTON_PREV_DATA = 'prev'
DEALS_BUTTON_NEXT_DATA = 'next'
DEALS_NEXT_CBQ_DATA = DEALS_CALLBACK_PREFIX + CBQ_DELIM + DEALS_BUTTON_NEXT_DATA
DEALS_PREV_CBQ_DATA = DEALS_CALLBACK_PREFIX + CBQ_DELIM + DEALS_BUTTON_PREV_DATA

# refresh deals
REFRESH_DEALS_CALLBACK_PREFIX = 'refreshdeals'
REFRESH_DEALS_DELIVERY_DATA = 'delivery'
REFRESH_DEALS_WAITING_DATA = 'waiting'
REFRESH_DELIVERY_DEALS_CALLBACK_DATA = REFRESH_DEALS_CALLBACK_PREFIX + CBQ_DELIM + REFRESH_DEALS_DELIVERY_DATA
REFRESH_WAITING_DEALS_CALLBACK_DATA = REFRESH_DEALS_CALLBACK_PREFIX + CBQ_DELIM + REFRESH_DEALS_WAITING_DATA

# buttons / objects
DEALS_PREV_BUTTON_OBJ = {'text': TextSnippets.DEALS_PAGE_PREV_BUTTON_TEXT, 'callback_data': DEALS_PREV_CBQ_DATA}
DEALS_NEXT_BUTTON_OBJ = {'text': TextSnippets.DEALS_PAGE_NEXT_BUTTON_TEXT, 'callback_data': DEALS_NEXT_CBQ_DATA}

REFRESH_DELIVERY_DEALS_BUTTON = {'text': TextSnippets.REFRESH_DELIVERY_DEALS_BUTTON_TEXT,
                                 'callback_data': REFRESH_DELIVERY_DEALS_CALLBACK_DATA}
REFRESH_WAITING_DEALS_BUTTON = {'text': TextSnippets.REFRESH_WAITING_DEALS_BUTTON_TEXT,
                                'callback_data': REFRESH_WAITING_DEALS_CALLBACK_DATA}

REFRESH_DEALS_BUTTON_OBJ = {'inline_keyboard': [[REFRESH_DELIVERY_DEALS_BUTTON],
                                                [REFRESH_WAITING_DEALS_BUTTON]
                                                ]}

TO_PREV_DEALS_BUTTON_OBJ = {'inline_keyboard': [[DEALS_PREV_BUTTON_OBJ],
                                                [REFRESH_DELIVERY_DEALS_BUTTON],
                                                [REFRESH_WAITING_DEALS_BUTTON]]}

TO_NEXT_DEALS_BUTTON_OBJ = {'inline_keyboard': [[DEALS_NEXT_BUTTON_OBJ],
                                                [REFRESH_DELIVERY_DEALS_BUTTON],
                                                [REFRESH_WAITING_DEALS_BUTTON]]}

TO_BOTH_DEALS_BUTTON_OBJ = {'inline_keyboard': [[DEALS_PREV_BUTTON_OBJ, DEALS_NEXT_BUTTON_OBJ],
                                                [REFRESH_DELIVERY_DEALS_BUTTON],
                                                [REFRESH_WAITING_DEALS_BUTTON]]}

CLOSE_DEAL_CALLBACK_PREFIX = 'closedeal'
CLOSE_DEAL_DIALOG_BUTTON_OBJ = {'inline_keyboard': [[{'text': TextSnippets.DEAL_CLOSING_DIALOG_YES,
                                                      'callback_data': CLOSE_DEAL_CALLBACK_PREFIX}],
                                                    [{'text': TextSnippets.TO_DEALS_BUTTON_TEXT,
                                                      'callback_data': TO_DEALS_CALLBACK_DATA}]
                                                    ]}

TO_DEALS_BUTTON_OBJ = {'inline_keyboard':
                           [[{'text': TextSnippets.TO_DEALS_BUTTON_TEXT,
                              'callback_data': TO_DEALS_CALLBACK_DATA}]]}
