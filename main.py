import requests, json
import datetime
from exchange import Exchange


class BotHandler:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    # url = "https://api.telegram.org/bot<token>/"

    def get_updates(self, offset=0, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_first_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[0]
        else:
            last_update = None

        return last_update


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
            #print(json.dumps(current_update, indent=2))
            print('received... ',end='')
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
                exchanges[msg['chat']['id']] = Exchange(lambda x: magnito_bot.send_message(msg['chat']['id'], x))

            exchanges[msg['chat']['id']].handle_multiline(msg)
            print('processed.')
