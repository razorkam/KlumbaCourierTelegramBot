from . import Commands

REQUEST_PHONE_NUMBER_BUTTON = 'Отправить номер телефона'
REQUEST_PHONE_NUMBER_MESSAGE = 'Добро пожаловать в *интерфейс курьера Клумба*!\n' \
                               'Для дальнейшей работы необходимо авторизоваться по вашему номеру телефона.\n' \
                               'Подтвердите его отправку нажатием кнопки *%s* ниже. \n' % REQUEST_PHONE_NUMBER_BUTTON \
                               + '\n' \
                               'КНОПКА НАХОДИТСЯ *СНИЗУ* ПОД ИЛИ НАД КЛАВИАТУРОЙ \n' \
                               'ЕСЛИ ОНА СКРЫТА НУЖНО НАЖАТЬ НА СТРЕЛКУ ВВЕРХ РЯДОМ с КЛАВИАТУРОЙ.'
AUTHORIZATION_SUCCESSFUL = 'Авторизация по номеру телефона пройдена!\n' \
                           'Теперь вы можете использовать команды бота.'
AUTHORIZATION_UNSUCCESSFUL = 'Авторизация не пройдена. Попробуйте снова.'
UNKNOWN_COMMAND = 'Неизвестная команда: %s. Попробуйте снова.'
UNKNOWN_NONTEXT_COMMAND = 'Команды должны быть переданы в текстовом виде. Попробуйте снова.'

BOT_HELP_TEXT = 'Интерфейс курьера поддерживает следующие возможности: \n' \
                '*%s* - получение вашего списка заказов' % Commands.GET_DEALS_LIST + '\n'\
                '*%s* - справка об интерфейсе курьера' % Commands.HELP + '\n'\
                '*%s* - обновление своего номера телефона для входа' % Commands.REAUTHORIZE

ERROR_BITRIX_REQUEST = 'Произошла ошибка при обращении к серверу. \n' \
                       'Попробуйте снова или подождите некоторое время.'

YOU_HAVE_NO_DEALS_IN_DELIVERY = 'Cейчас у вас нет заказов в доставке.'
YOU_HAVE_NO_DEALS_WAITING = 'Cейчас у вас нет заказов в ожидании.'

ERROR_GETTING_DEALS = 'Произошла ошибка при получении заказов.\n' \
                      ' Попробуйте снова или подождите некоторое время.'

ERROR_HANDLING_DEAL_ACTION = 'Произошла ошибка при смене статуса заказа.\n' \
                             'Попробуйте снова или подождите некоторое время.'

ERROR_SYSTEM_EXCEPTION = 'Произошла внутренняя ошибка. Попробуйте снова или подождите некоторое время.'

DEALS_DELIVERY_HEADER = '_Заказов в доставке: %s._\n\n'
DEALS_WAITING_HEADER = '_Заказов в ожидании: %s._\n\n'
DEAL_PAGE_FOOTER = '_Страница_ {} из {}\n\n'

ADDRESS_RESOLUTION_LINK = 'https://maps.yandex.ru/?text='

# deals in delivery
DEAL_DELIVERY_PREVIEW_TEMPLATE = \
                '*№ заказа: ПОДРОБНЕЕ ЖМИ --->* {}\n' \
                '*Время:* {} \n' \
                '*Комментарий:* {} \n' \
                '*Комментарий к товару:* {} \n' \
                '*Комментарий по доставке:* {} \n' \
                '*Инкогнито:* {} \n' \
                '*Адрес:* [{}]({}) \n' \
                '*Квартира:* {} \n' \
                '*Телефон получателя:* [{}](tel:{}) \n' \
                '*К оплате:* {} \n' \
                '*Ответственный:* {} \n' \
                '*Тип заказа:* *{}* \n' \
                '*ЗАКАЗ ДОСТАВЛЕН:* {}'

# all deals
DEAL_WAITING_PREVIEW_TEMPLATE = \
                '*№ заказа: ПОДРОБНЕЕ ЖМИ --->* {}\n' \
                '*Дата:* {} \n' \
                '*Время:* {} \n' \
                '*Ответственный:* {} \n' \
                '*Тип заказа:* *{}*'


DEAL_TEMPLATE_WAITING = \
                '*№ заказа:* {} \n' \
                '*Что заказано:* {} \n' \
                '*Дата:* {} \n' \
                '*Время:* {} \n' \
                '*Комментарий:* {} \n' \
                '*Комментарий к товару:* {} \n' \
                '*Комментарий по доставке:* {} \n' \
                '*Телефон заказчика:* [{}](tel:{}) \n' \
                '*Имя получателя:* {} \n' \
                '*Фамилия получателя:* {} \n' \
                '*Телефон получателя:* [{}](tel:{}) \n' \
                '*Адрес получателя:* [{}]({}) \n' \
                '*К оплате:* {} \n' \
                '*Ответственный:* {} \n' \
                '*Тип заказа:* *{}*'

DEAL_TEMPLATE_DELIVERY = DEAL_TEMPLATE_WAITING + '\n *ЗАКАЗ ДОСТАВЛЕН:* {}'

DEAL_ACTION_NAME_OPEN = 'Переоткрыть'
DEAL_ACTION_NAME_CLOSE = 'Заказ доставлен'


DEAL_DELIMETER = '`------------------`'
DEAL_OPEN_STAGE_NAME = 'Открыт'
DEAL_CLOSED_STAGE_NAME = 'Закрыт'
DEAL_ERROR_STAGE_NAME = 'Ошибка'
DEAL_ACTION_DELIM = '_'


CBQ_DEALS_WRONG_MESSAGE = 'Такого заказа нет.'
CBQ_CLOSING_WAITING_DEAL_ERROR = 'Заказ не в доставке не может быть завершен.'

CBQ_UNKNOW_COMMAND = 'Возникла внутренняя ошибка обработки запроса.\n' \
                     'Возможно, причина в вашем клиенте Telegram.\n' \
                     'Попробуйте обновить или перeустановить его.'

DEAL_VIEW_GENERATION_ERROR = 'Произошла ошибка при просмотре заказа.'


FIELD_IS_EMPTY_PLACEHOLDER = 'нет'

TO_DEALS_BUTTON_TEXT = 'Назад к заказам'
REFRESH_DELIVERY_DEALS_BUTTON_TEXT = 'Обновить заказы в доставке'
REFRESH_WAITING_DEALS_BUTTON_TEXT = 'Обновить заказы в ожидании'

DEAL_CLOSING_DIALOG_TEXT = 'Подтвердить доставку заказа {}?'
DEAL_CLOSING_DIALOG_YES = 'Да'
DEAL_CLOSING_DIALOG_NO = 'Отмена'

DEALS_PAGE_NEXT_BUTTON_TEXT = 'Вперед'
DEALS_PAGE_PREV_BUTTON_TEXT = 'Назад'

DEAL_TOO_LATE = 'Заказ опоздал. Напишите причину опоздания:'




