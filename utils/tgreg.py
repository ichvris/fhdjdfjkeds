from redis import Redis
import time
from aiogram import Bot, Dispatcher, executor, types
import string
import random

from utils import bot_common



TOKEN = "6296239815:AAHWZ_iYhTCVw8OwsASmwPI_R0mnIo5SHDE" # token of bot from @BotFather


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
r = Redis(decode_responses=True)


@dp.message_handler(commands=["start"])
async def newacc(message: types.Message):
    print(1)
    passwd = r.get(f"tg:{message.from_user.id}")
    if passwd:
        await message.reply(f"PASS-WORD: {passwd}")
        return
    else:
        print(2)
        passwd = await bot_common.new_account(r)
        r.set(f"tg:{message.from_user.id}", passwd)
    await message.reply(f"PASS-WORD: {passwd}")



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
