from exchange import Exchange, Order, OrderBook, User
luke = User(dict(id=25,username='luke'))
order = Order(dir='sell',qty=50,price=25,owner=luke)
print(order)
l = []
print(l)
l.insert(0,order)
print(l)
list