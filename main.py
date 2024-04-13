import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import Message
from keys import BOT_TOKEN, ADMINS_CHANNEL_ID

bot_token = BOT_TOKEN
bot = telebot.TeleBot(bot_token)

API_ENDPOINT = 'http://127.0.0.1:8000/api/'
CHANNEL = ADMINS_CHANNEL_ID

@bot.message_handler(commands=['start'])
def send_hello(message):
    bot.send_message(message.chat.id, "Hello! Send /orders to fetch and send orders to the channel.")

def get_orders():
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

@bot.message_handler(commands=['orders'])
def send_orders_to_channel(message):
    orders = get_orders()
    if not orders:
        bot.send_message(message.chat.id, "We have no orders yet.")
    else:
        try:
            for order in orders:
                image_url = order.get('passport_image', '')
                image_data = requests.get(image_url).content if image_url else None

                order_message = f"ID: {order['id']}\nName: {order['full_name']}\nPhone: {order['phone_number']}\nAddress: {order['adress']}"


                # Send the location
                latitude = float(order.get('latitude', 0))
                longitude = float(order.get('longitude', 0))
                bot.send_location(CHANNEL, latitude, longitude)

                # Create inline keyboard buttons
                keyboard = InlineKeyboardMarkup(row_width=2)
                accept_button = InlineKeyboardButton("Accept", callback_data=f"accept_{order['id']}")
                reject_button = InlineKeyboardButton("Reject", callback_data=f"reject_{order['id']}")
                keyboard.add(accept_button, reject_button)

                # Send photo and message with inline keyboard
                bot.send_photo(CHANNEL, image_data, caption=order_message, parse_mode='Markdown', reply_markup=keyboard)
        except Exception as e:
            print("Error:", e)


@bot.message_handler(commands=['my_location'])
def prompt_for_location(message: Message):
    bot.send_message(message.chat.id, "Please send me your coordinates (latitude, longitude)")

@bot.message_handler(func=lambda message: True, content_types=['location'])
def handle_location(message: Message):
    latitude = message.location.latitude
    longitude = message.location.longitude
    bot.send_message(message.chat.id, "Sending your location...")
    bot.send_location(message.chat.id, latitude, longitude)

print("Bot is running...")
bot.polling()
