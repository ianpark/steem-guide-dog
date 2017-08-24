import os
import signal
import sys
from bot import Bot


try:
    bot = Bot()
    bot.run()
except KeyboardInterrupt as ki:
    bot.stop()