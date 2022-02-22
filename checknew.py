import telebot
from diary import *
from profile import *

token = ''
login = ''
password = ''
bot = telebot.TeleBot(token)
profile = Profile({'main_login': login, 'main_password': password})
week = profile.check_grades()
if week:
    res = "Новые оценки:\n"
    for sub, grades in week.items():
        res += "    " + sub + ": " + " ".join(list(map(str, grades))) + "\n"
    bot.send_message(470082397, res)
