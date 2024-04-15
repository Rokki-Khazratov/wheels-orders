import asyncio
import requests
from aiogram import Bot, types
from aiogram import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import executor
from keys import BOT_TOKEN, ADMINS_CHANNEL_ID

bot_token = BOT_TOKEN
bot = Bot(token=bot_token)
dp = Dispatcher(bot)

API_ENDPOINT = 'http://127.0.0.1:8000/api/'
CHANNEL = ADMINS_CHANNEL_ID

already_orders = set()

@dp.message_handler(commands=['start'])
async def send_hello(message: types.Message):
    await message.answer("Hello! I am Wheels.uz personal assistent.")

async def get_orders():
    try:
        response = requests.get(API_ENDPOINT + 'orders/?is_checked=False')
        if response.status_code == 200:
            orders = response.json()
            return orders
        else:
            print("Failed to fetch orders:", response.status_code)
            return []
    except Exception as e:
        print("Error fetching orders:", e)
        return []

async def get_order_detail(order_id):
    try:
        response = requests.get(f"{API_ENDPOINT}orders/{order_id}/")
        if response.status_code == 200:
            order_detail = response.json()
            return order_detail
        else:
            print(f"Failed to fetch details for order {order_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching details for order {order_id}: {e}")
        return None

async def send_orders_to_channel():
    orders = await get_orders()
    if not orders:
        print("We have no orders yet.")
    else:
        try:
            for order in orders:
                print(already_orders)
                order_id = order.get('id')

                if order_id in already_orders:
                    continue

                already_orders.add(order_id)
                order_message = f"ID: {order['id']}\nName: {order['full_name']}\nPhone: {order['phone_number']}\nAddress: {order['adress']}\n\n"

                order_detail = await get_order_detail(order_id)
                if order_detail:
                    details = order_detail.get('details', [])
                    if details:
                        order_message += "Details:\n"
                        for detail in details:
                            order_message += f"  - {detail['wheel']}, Size: {detail['size']}, Width: {detail['width']}, Length: {detail['length']}, Price: {detail['price']}\n"

                latitude = float(order.get('latitude', '0') if order.get('latitude') != 'undefined' else '0')
                longitude = float(order.get('longitude', '0') if order.get('longitude') != 'undefined' else '0')
                await bot.send_location(CHANNEL, latitude, longitude)

                keyboard = InlineKeyboardMarkup(row_width=2)
                accept_button = InlineKeyboardButton("Accept", callback_data=f"accept_{order['id']}")
                reject_button = InlineKeyboardButton("Reject", callback_data=f"reject_{order['id']}")
                keyboard.add(accept_button, reject_button)

                await bot.send_message(CHANNEL, order_message, reply_markup=keyboard)
        except Exception as e:
            print("Error:", e)

async def main():
    while True:
        await send_orders_to_channel()
        await asyncio.sleep(15)

@dp.callback_query_handler(lambda c: c.data.startswith('accept_'))
async def accept_order_callback(query: CallbackQuery):
    order_id = int(query.data.split("_")[1])
    # Implement logic to accept order
    await update_order_checked(order_id)
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id)

async def update_order_checked(order_id):
    try:
        payload = {"is_checked": True}
        response = requests.patch(f"{API_ENDPOINT}orders/{order_id}/", json=payload)
        if response.status_code == 200:
            print(f"Order {order_id} checked successfully.")
        else:
            print(f"Failed to check order {order_id}: {response.status_code}")
    except Exception as e:
        print(f"Error updating order {order_id}: {e}")

async def delete_order(order_id):
    try:
        response = requests.delete(f"{API_ENDPOINT}orders/{order_id}/")
        if response.status_code == 204:
            print(f"Order {order_id} deleted successfully.")
        else:
            print(f"Failed to delete order {order_id}: {response.status_code}")
    except Exception as e:
        print(f"Error deleting order {order_id}: {e}")

@dp.callback_query_handler(lambda c: c.data.startswith('reject_'))
async def reject_order_callback(query: CallbackQuery):
    order_id = int(query.data.split("_")[1])

    await delete_order(order_id)
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id)
    message_id = query.message.message_id
    for _ in range(2):
        try:
            await bot.delete_message(chat_id=query.message.chat.id, message_id=message_id)
        except Exception as e:
            print(f"Error deleting message: {e}")
        message_id -= 1

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(main())
        executor.start_polling(dp, skip_updates=True)
    finally:
        loop.close()
