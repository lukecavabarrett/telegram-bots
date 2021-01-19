import traceback
from datetime import timedelta, datetime
import pytimeparse

BUY = 'BUY'
SELL = 'SELL'


class Order:
    next_id = 1

    def __init__(self, dir, qty, price, owner):
        self.dir = dir.upper()
        self.qty = self.original_qty = qty
        self.price = price
        self.owner = owner
        self.id = Order.next_id
        Order.next_id += 1

    def __str__(self):
        return '(#' + str(self.id) + ' ' + self.dir + ' ' + str(self.qty) + '[' + str(
            self.original_qty) + ']' + ' @' + str(
            self.price) + '  | ' + str(self.owner) + ')'

    def __repr__(self):
        return str(self)


def profit_string(balance, equity):
    if equity == 0:
        if balance < 0:
            return "<b>loss</b>"
        elif balance == 0:
            return "  "
        else:  # balance>0
            return "<b> gain </b>"
    elif equity < 0:
        return 'P &#8804; ' + "{:.2f}".format(-balance / equity)
    else:  # equity>0
        return 'P &#8805; ' + "{:.2f}".format(-balance / equity)


class OrderBook:  # Book for a single stock

    def __init__(self, output):
        # most competitive on the back
        self.output = output
        self.bids = []
        self.asks = []
        self.balance = dict()  # ids to balance
        self.equity = dict()  # ids to equity

    def to_string(self, id_to_users, balance=False, equity=False, profit=False):
        profit = True
        msg = '<b>BIDS:</b>\n' + '\n'.join(map(str, reversed(self.bids))) + '\n<b>ASKS:</b>\n' + '\n'.join(
            map(str, reversed(self.asks))) + '\n'
        if balance:
            msg += '<b>Balance:</b>\n' + '\n'.join(
                map(lambda x: str(id_to_users[x[0]]) + ': ' + str(x[1]) + '$', self.balance.items())) + '\n';
        if equity:
            msg += '<b>Stocks:</b>\n' + '\n'.join(
                map(lambda x: str(id_to_users[x[0]]) + ': ' + str(x[1]) + 'P', self.equity.items())) + '\n';
        if profit:
            msg += '<b>Profit:</b>\n' + '\n'.join(
                map(lambda id: str(id_to_users[id]) + ': ' + profit_string(self.balance[id], self.equity[id]),
                    self.equity.keys())) + '\n'

        return msg

    def trade_against(self, new: Order, old: Order):
        qty = min(new.qty, old.qty)
        if qty <= 0:
            return
        price = old.price

        self.output(str(new) + ' matched ' + str(old) + ' @' + str(price) + ' :' + str(qty))

        buy = new if new.dir == 'BUY' else old
        sell = new if new.dir == 'SELL' else old

        buyer_id: int = buy.owner.id
        seller_id: int = sell.owner.id

        if buyer_id not in self.balance:
            self.balance[buyer_id] = 0
        if buyer_id not in self.equity:
            self.equity[buyer_id] = 0
        if seller_id not in self.balance:
            self.balance[seller_id] = 0
        if seller_id not in self.equity:
            self.equity[seller_id] = 0

        self.balance[buyer_id] -= qty * price
        self.balance[seller_id] += qty * price

        self.equity[buyer_id] += qty
        self.equity[seller_id] -= qty

        buy.qty -= qty
        sell.qty -= qty

    def add_order(self, order: Order):
        if order.dir == 'BUY':
            while order.qty > 0 and self.asks and self.asks[-1].price <= order.price:
                self.trade_against(order, self.asks[-1])
                if self.asks[-1].qty == 0:
                    self.asks.pop()
            # if order has still some size, we insert it
            if order.qty > 0:
                idx = len(self.bids)
                while idx > 0 and self.bids[idx - 1].price >= order.price:
                    idx -= 1
                self.bids.insert(idx, order)
                self.output(str(order) + ' placed in the orderbook')
        else:
            while order.qty > 0 and self.bids and self.bids[-1].price >= order.price:
                self.trade_against(order, self.bids[-1])
                if self.bids[-1].qty == 0:
                    self.bids.pop()
            # if order has still some size, we insert it
            if order.qty > 0:
                idx = len(self.asks)
                while idx > 0 and self.asks[idx - 1].price <= order.price:
                    idx -= 1
                self.asks.insert(idx, order)
                self.output(str(order) + ' placed in the orderbook')



    def settle(self, price):
        for who, qty in self.equity.items():
            self.balance[who] += qty * price
        self.equity = dict()
        self.bids = []
        self.asks = []

    def remove_order(self, remove_id: int, sender):
        for i, order in enumerate(self.asks):
            if order.id == remove_id:
                if order.owner.id != sender.id:
                    self.output(str(sender) + ': you cannot remove order #' + str(
                        remove_id) + ' as the you\'re not the owner (' + str(order.owner) + ') is.')
                    return False
                self.output(str(sender) + ' removed order #' + str(remove_id))
                del self.asks[i]
                return True

        for i, order in enumerate(self.bids):
            if order.id == remove_id:
                if order.owner.id != sender.id:
                    self.output(str(sender) + ': you cannot remove order #' + str(
                        remove_id) + ' as the you\'re not the owner (' + str(order.owner) + ') is.')
                    return False
                self.output(str(sender) + ' removed order #' + str(remove_id))
                del self.bids[i]
                return True

        self.output(str(sender) + ': you cannot remove order #' + str(
            remove_id) + ' as it is not present in the book at the current time.')
        return False


class User:
    def __init__(self, obj):
        self.id = obj['id']
        self.first_name = obj['first_name'] if 'first_name' in obj else None
        self.last_name = obj['last_name'] if 'last_name' in obj else None
        self.username = obj['username'] if 'username' in obj else None

    def human_name(self):
        if self.username:
            return self.username
        if self.first_name:
            return self.first_name + (' ' + self.last_name if self.last_name else '')
        if self.last_name:
            return self.last_name
        return 'user ' + str(self.id)

    def __str__(self):
        return self.human_name()

    def __repr__(self):
        return str(self)


def ensure_no_arguments(args):
    if len(args) > 1:
        raise IOError(args[0] + ' doesn\'t expect any argument')


class Exchange:
    def __init__(self, output):
        self.output = output
        self.open = False
        self.close_at = None
        self.id_to_user = dict()
        self.orderbook = OrderBook(output)

    def reset(self):
        self.orderbook = OrderBook(self.output)

    def print_state(self, orderbook=False, balances=False, profit=False):
        msg = 'The exchange is currently <b>' + ('open' if self.open else 'close') + '</b>.'
        if self.open and self.close_at:
            msg += ' It will close at <b>' + str(self.close_at) + '</b>.'
        if self.open and orderbook:
            msg += '\n' + self.orderbook.to_string(self.id_to_user, balance=balances, equity=balances, profit=profit)
        self.output(msg)

    def handle_multiline(self, msg):
        orig_msg = msg['text']
        for single in orig_msg.split('\n'):
            if single:
                msg['text'] = single
                self.handle(msg)

    def handle(self, msg):
        sender = User(msg['from'])
        self.id_to_user[sender.id] = sender
        argc = msg['text'].split()
        try:
            if (argc[0].endswith('@TradingEstimathonBot')):
                argc[0] = argc[0][:-21]
            if argc[0] == '/state':
                self.print_state(orderbook=True, balances=True, profit=True)
            elif argc[0] == '/reset':
                self.reset()
                self.print_state(orderbook=True, balances=True)
            elif argc[0] == '/settle':
                price = None
                for arg in argc[1:]:
                    if arg[0] == '@':
                        price = int(arg[1:])
                    else:
                        raise IOError(arg + ' is not a valid argument for ' + argc[0])
                if price is None:
                    raise IOError(argc[0] + ' is missing argument @price')
                self.orderbook.settle(price)
                self.print_state(orderbook=True, balances=True)
            elif argc[0] == '/close':
                self.open = False
                self.print_state()
            elif argc[0] == '/open':
                self.open = True
                if len(argc) == 1:
                    self.close_at = None
                else:
                    timedelta = pytimeparse.timeparse.timeparse(argc[1])
                    if timedelta is None:
                        raise IOError(argc[1] + ' is not a valid time interval')
                    self.close_at = datetime.fromtimestamp(int(msg['date']) + timedelta)
                self.print_state(orderbook=True, balances=True)
            elif argc[0] == '/remove':
                if not self.open:
                    self.print_state()
                    return
                if len(argc) != 2:
                    raise IOError(argc[0] + ' requires a single argument #id')
                id = int(argc[1])
                if self.orderbook.remove_order(id, sender):
                    self.print_state(orderbook=True, balances=True)
            elif argc[0] == '/buy':
                if not self.open:
                    self.print_state()
                    return
                qty = None
                price = None
                for arg in argc[1:]:
                    if arg[0] == '@':
                        price = int(arg[1:])
                    elif arg[0] == ':':
                        qty = int(arg[1:])
                    else:
                        raise IOError(arg + ' is not a valid argument for ' + argc[0])
                if qty is None:
                    raise IOError(argc[0] + ' is missing argument :qty')
                if price is None:
                    raise IOError(argc[0] + ' is missing argument @price')
                order = Order(dir='BUY', qty=qty, price=price, owner=sender)
                self.output(sender.human_name() + ' added order ' + str(order))
                self.orderbook.add_order(order)
                print(sender.human_name() + ' added order ' + str(order))
                self.print_state(orderbook=True, balances=True)
            elif argc[0] == '/sell':
                if not self.open:
                    self.print_state()
                    return
                qty = None
                price = None
                for arg in argc[1:]:
                    if arg[0] == '@':
                        price = int(arg[1:])
                    elif arg[0] == ':':
                        qty = int(arg[1:])
                    else:
                        raise IOError(arg + ' is not a valid argument for ' + argc[0])
                if qty is None:
                    raise IOError(argc[0] + ' is missing argument :qty')
                if price is None:
                    raise IOError(argc[0] + ' is missing argument @price')
                order = Order(dir='SELL', qty=qty, price=price, owner=sender)
                self.output(sender.human_name() + ' added order ' + str(order))
                self.orderbook.add_order(order)
                print(sender.human_name() + ' added order ' + str(order))
                self.print_state(orderbook=True, balances=True)
            else:
                self.output('command: \'' + msg['text'] + '\' is not recognized')
        except Exception as exception:
            self.output(sender.human_name() + ' your message \"' + msg['text'] + '\" was malformed (It raised "' + str(
                exception) + '" )')
