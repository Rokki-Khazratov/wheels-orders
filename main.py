import requests
import telebot
from keys import BOT_TOKEN, ADMINS_CHANNEL_ID

bot_token = BOT_TOKEN
bot = telebot.TeleBot(bot_token)

API_ENDPOINT = 'http://127.0.0.1:8000/api/'
CHANNEL = ADMINS_CHANNEL_ID

def get_orders():
    try:
        response = requests.get(API_ENDPOINT + 'orders/')
        if response.status_code == 200:
            orders = response.json()
            return orders
        else:
            print("Failed to fetch orders:", response.status_code)
            return []
    except Exception as e:
        print("Error fetching orders:", e)
        return []

@bot.message_handler(commands=['start'])
def send_orders_to_channel(message):
    try:
        orders = get_orders()
        for order in orders:
            order_message = f"ID: {order['id']}\nName: {order['full_name']}\nPhone: {order['phone_number']}\nAddress: {order['adress']}\nChecked: {'Yes' if order['is_checked'] else 'No'}"
            bot.send_message(CHANNEL, order_message)
    except Exception as e:
        print("Error:", e)

print("Bot is running...")
bot.polling()
