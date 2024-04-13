import os
import time
import telebot
from telebot import types
from keys import BOT_TOKEN, ADMINS_CHANNEL_ID

bot_token = BOT_TOKEN
bot = telebot.TeleBot(bot_token)

CHANNEL = ADMINS_CHANNEL_ID
ADMIN = 6325708298

@bot.message_handler(commands=['start'])
def send_hello_world(message):
    
    bot.send_message(CHANNEL, "hello world")

# Start the bot
bot.polling()

# test rv branch 