import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = os.getenv('TG_TOKEN')


# Initialize bot, dispatcher, and storage
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(Command('start'))
async def on_start(message: types.Message):
    await message.reply("Приветствуем вас! Для подачи заявки на ипотеку, пожалуйста, введите запрашиваемую сумму кредита.")
    await dp.current_state(user=message.from_user.id).set_state('loan_amount')


@dp.message_handler(state='*', commands=['start'])
async def restart_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data.clear()
    await on_start(message)


@dp.message_handler(state='loan_amount', content_types=types.ContentType.TEXT)
async def on_loan_amount_entered(message: types.Message, state: FSMContext):
    try:
        loan_amount = int(message.text)
    except ValueError:
        await message.reply("Пожалуйста, введите сумму кредита числом.")
        return

    async with state.proxy() as data:
        data['loan_amount'] = loan_amount

    await message.reply("Теперь введите сумму первоначального взноса (не менее 15% от запрашиваемой суммы кредита).")
    await dp.current_state(user=message.from_user.id).set_state('down_payment')


@dp.message_handler(state='down_payment', content_types=types.ContentType.TEXT)
async def on_down_payment_entered(message: types.Message, state: FSMContext):
    try:
        down_payment = int(message.text)
    except ValueError:
        await message.reply("Пожалуйста, введите сумму первоначального взноса числом.")
        return


    async with state.proxy() as data:
        loan_amount = data['loan_amount']
        minimum_down_payment = loan_amount * 0.15

        if down_payment >= minimum_down_payment:
            await message.reply("Спасибо за вашу заявку! Вы можете подать онлайн-заявку на ипотеку на сайте "
                                "https://domclick.ru/ipoteka/programs/onlajn-zayavka")
        else:
            await message.reply(f"Сумма первоначального взноса должна быть не меньше {minimum_down_payment} рублей. "
                                f"Пожалуйста, укажите бОльшую сумму первоначального взноса.")
            return

    await state.finish()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
