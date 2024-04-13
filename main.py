import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

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


def get_order_detail(order_id):
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

    


@bot.message_handler(commands=['orders'])
def send_orders_to_channel(message):
    orders = get_orders()
    if not orders:
        bot.send_message(message.chat.id, "We have no orders yet.")
    else:
        try:
            for order in orders:
                image_url = order.get('passport_image')
                image_data = None
                if image_url:
                    image_data = requests.get(image_url).content

                order_message = f"ID: {order['id']}\nName: {order['full_name']}\nPhone: {order['phone_number']}\nAddress: {order['adress']}"

                latitude = float(order.get('latitude', 0))
                longitude = float(order.get('longitude', 0))
                bot.send_location(CHANNEL, latitude, longitude)

                # Create inline keyboard buttons
                keyboard = InlineKeyboardMarkup(row_width=2)
                accept_button = InlineKeyboardButton("Accept", callback_data=f"accept_{order['id']}")
                reject_button = InlineKeyboardButton("Reject", callback_data=f"reject_{order['id']}")
                keyboard.add(accept_button, reject_button)

                # Send photo if available, otherwise send message without photo
                if image_data:
                    bot.send_photo(CHANNEL, image_data, caption=order_message, parse_mode='Markdown', reply_markup=keyboard)
                else:
                    bot.send_message(CHANNEL, order_message, reply_markup=keyboard)
        except Exception as e:
            print("Error:", e)




def update_order_checked(order_id):
    try:
        payload = {"is_checked": True}
        response = requests.patch(f"{API_ENDPOINT}orders/{order_id}/", json=payload)
        if response.status_code == 200:
            print(f"Order {order_id} checked successfully.")
        else:
            print(f"Failed to check order {order_id}: {response.status_code}")
    except Exception as e:
        print(f"Error updating order {order_id}: {e}")

def delete_order(order_id):
    try:
        response = requests.delete(f"{API_ENDPOINT}orders/{order_id}/")
        if response.status_code == 204:
            print(f"Order {order_id} deleted successfully.")
        else:
            print(f"Failed to delete order {order_id}: {response.status_code}")
    except Exception as e:
        print(f"Error deleting order {order_id}: {e}")



@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_order_callback(query: CallbackQuery):
    order_id = query.data.split("_")[1]  # Extract order ID from callback data
    order_detail = get_order_detail(order_id)
    if order_detail:
        # Send PATCH request to update order status to checked
        update_order_checked(order_id)
        # Hide inline keyboard buttons
        bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id)
        


@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_order_callback(query: CallbackQuery):
    order_id = query.data.split("_")[1]  # Extract order ID from callback data
    # Send DELETE request to delete the order
    delete_order(order_id)
    # Hide inline keyboard buttons
    bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id)
    # Delete the main message along with the location and previous messages
    message_id = query.message.message_id
    for _ in range(3):  
        try:
            bot.delete_message(chat_id=query.message.chat.id, message_id=message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")
        message_id -= 1



print("Bot is running...")
bot.polling()