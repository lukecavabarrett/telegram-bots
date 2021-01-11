from datetime import timedelta, datetime
import pytimeparse


class OrderBook:  # Book for a single stock

    class Order:
        next_id = 1

        def __init__(self, dir, qty, price, owner):
            self.dir = dir.upper()
            self.qty = self.original_qty = qty
            self.price = price
            self.owner = owner
            self.id = OrderBook.Order.next_id
            OrderBook.Order.next_id += 1

        def __str__(self):
            return '#'+str(self.id)+' '+self.dir+' '+str(self.original_qty)+' @'+str(self.price)+'  | '+str(self.owner)
    def __init__(self):
        pass


class Exchange:
    def __init__(self, output):
        self.output = output
        self.open = False
        self.close_at = None

    def print_state(self):
        msg = 'The exchange is currently <b>' + ('open' if self.open else 'close') + '</b>.'
        if self.open and self.close_at:
            msg += ' It will close at <b>' + str(self.close_at) + '</b>'
        self.output(msg)

    def handle(self, msg):
        argc = msg['text'].split()
        if (argc[0].endswith('@TradingEstimathonBot')):
            argc[0] = argc[0][:-21]
        if argc[0] == '/state':
            self.print_state()
        elif argc[0] == '/close':
            self.open = False
            self.print_state()
        elif argc[0] == '/open':
            self.open = True
            if len(argc) == 1:
                self.close_at = None
            else:
                self.close_at = datetime.fromtimestamp(int(msg['date']) + pytimeparse.timeparse.timeparse(argc[1]))
            self.print_state()
        elif argc[0] == '/buy':
            qty = None
            price = None
            for arg in argc[1:]:
                if arg[0]=='@':
                    price = int(arg[1:])
                elif arg[0]==':':
                    qty = int(arg[1:])
                else:
                    pass
            order = OrderBook.Order(dir='buy',qty=qty,price=price,owner=msg['from']['id'])
            self.output(msg['from']['first_name']+' added order '+str(order))
        else:
            self.output('command: \'' + msg['text'] + '\' is not recognized')
