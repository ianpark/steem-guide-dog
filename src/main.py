import os
from bot import Bot
from config import Config
CONFIG_PATH = os.path.expanduser('~/.steem/config.json')

try:
    bot = Bot(Config(CONFIG_PATH))
    bot.run()
except Exception as e:
    print (e)