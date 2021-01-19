import yfinance as yf
import math, sys
import argparse

parser = argparse.ArgumentParser(description='Market Ticker')
parser.add_argument('name', type=str, help='the stock to be followed')
parser.add_argument('--delay', type=float, help='print delay in seconds', default=0.1)
parser.add_argument('--period', type=str, help='period of stock', default='1d')
parser.add_argument('--interval', type=str, help='interval of stock', default='1m')
args = parser.parse_args()

ticker_data = yf.Ticker(args.name)
ticker_df = ticker_data.history(period=args.period, interval=args.interval)

import sched, time

s = sched.scheduler(time.time, time.sleep)


class TimeValue:
    def __init__(self, value):
        self.value = value
        self.delta = value - value

    def __add__(self, other):
        next = TimeValue(self.value + other)
        next.delta = other
        return next

    def __sub__(self, other):
        return self.__add__(-other)

    def assign(self, value):
        self.delta = value - self.value
        self.value = value

    def __str__(self):
        delta = '{:8.04f}'.format(abs(float(self.delta)))
        return '{:8.04f}'.format(float(self.value)) + (
            '\033[0;31m ▼' if self.delta < 0 else ('\033[0;32m ▲' if self.delta > 0 else ' ■')) + delta + '\033[0m'

    def __repr__(self):
        return (self.value.__repr__()) + ' d ' + str(self.delta.__repr__())


high, low = None, None


def do_something(i):
    if i >= len(ticker_df):
        sys.stdout.write('\n')
        sys.stdout.flush()
        return
    s.enter(args.delay, 1, do_something, (i + 1,))
    row = ticker_df.iloc[i]
    global high, low
    if high is None:
        high = TimeValue(row['High'])
    else:
        high.assign(row['High'])
    if low is None:
        low = TimeValue(row['Low'])
    else:
        low.assign(row['Low'])
    sys.stdout.write(
        '\r  ' + str(ticker_df.index[i]) + '  | ' + '  S ' + str(low) + '  | ' + ' B ' + str(high)+'    ')
    sys.stdout.flush()


print('\033[1;33m '+ticker_data.ticker + '\033[0m')
s.enter(args.delay, 1, do_something, (0,))
try:
    s.run()
except KeyboardInterrupt:
    sys.stdout.write('\n')
    sys.stdout.flush()
