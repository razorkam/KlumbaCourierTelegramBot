# representation with parsed deal fields
class Deal:
    _id = None
    _order = None
    _date = None
    _time = None
    _comment = None
    _order_comment = None
    _delivery_comment = None
    _incognito = None
    _customer_phone = None
    _address = None
    _address_res_link = None
    _location = None
    _deal_sum = None
    _close_command = None
    _view_command = None
    _flat = None
    _recipient_phone = None
    _recipient_name = None
    _recipient_surname = None

    # name + last_name combined
    _responsible_name = None

    def __init__(self, deal_id, order, date, time, comment, order_comment, delivery_comment, incognito,
                 customer_phone, address, address_res_link, location, deal_sum, close_command, view_command,
                 flat, recipient_phone, recipient_name, recipient_surname, responsible_name):
        self._id = deal_id
        self._order = order
        self._date = date
        self._time = time
        self._comment = comment
        self._order_comment = order_comment
        self._delivery_comment = delivery_comment
        self._incognito = incognito
        self._customer_phone = customer_phone
        self._address = address
        self._address_res_link = address_res_link
        self._location = location
        self._deal_sum = deal_sum
        self._close_command = close_command
        self._view_command = view_command
        self._flat = flat
        self._recipient_phone = recipient_phone
        self._recipient_name = recipient_name
        self._recipient_surname = recipient_surname
        self._responsible_name = responsible_name

