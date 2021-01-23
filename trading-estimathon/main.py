import datetime
from exchange import Exchange
from bot import BotHandler

with open("token.txt", "r") as myfile:
    token = myfile.readlines()[0]

magnito_bot = BotHandler(token)  # Your bot's name

new_offset = 0
print('hi, now launching...')

exchanges = dict()

while True:
    all_updates = magnito_bot.get_updates(new_offset)
    if len(all_updates) > 0:
        for current_update in all_updates:
            # print(json.dumps(current_update, indent=2))
            print('received... ', end='')
            first_update_id = current_update['update_id']
            new_offset = first_update_id + 1
            if 'message' not in current_update:
                continue
            msg = current_update['message']
            if 'text' not in msg:
                continue
            if 'from' not in msg:
                continue
            if 'chat' not in msg:
                continue

            if msg['chat']['id'] not in exchanges:
                exchanges[msg['chat']['id']] = Exchange(
                    lambda x: (print('sending: '+str(x)), magnito_bot.send_message(msg['chat']['id'], x)))

            exchanges[msg['chat']['id']].handle_multiline(msg)
            print('processed.')
