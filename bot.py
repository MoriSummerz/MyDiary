import telebot
from diary import *
from profile import *
import datetime
token = ''
bot = telebot.TeleBot(token)
login  = ''
password = ''
profile = Profile({'main_login': login, 'main_password': password})

markup = telebot.types.ReplyKeyboardMarkup()
markup.add(telebot.types.KeyboardButton('Расписание на сегодня'), telebot.types.KeyboardButton('Расписание на завтра'))
markup.add(telebot.types.KeyboardButton('Табель'))


@bot.message_handler(commands=['start'])
def start(message):
    usid = message.from_user.id
    if usid not in admins:
        return

    bot.send_message(message.chat.id, '*Выбери действие с помощью кнопок снизу =)*', parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(content_types=['text'])
def deauth_user(message):
    if "Расписание" in message.text:
        bot.send_chat_action(message.chat.id, 'typing')
        if "завтра" in message.text:
            diary = profile.diary_day((datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%d.%m.%Y'))
        else:
            diary = profile.diary_day(datetime.datetime.now().strftime('%d.%m.%Y'))

        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        subs = ""
        for sub in diary.subjects:
            subs += sub.get_str() + '\n'

        if diary.weekday != 6:
            bot.send_message(message.chat.id, '*🔸  ' + weekdays[diary.weekday] + ':*\n' + subs, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, '*🔸 Воскресенье*:\n\nСвободный день!', parse_mode="Markdown")
    elif message.text == "Табель":
        bot.send_chat_action(message.chat.id, 'upload_photo')
        profile.diary_term(draw=True)
        bot.send_photo(message.chat.id, photo=open('grades.png', 'rb').read())


bot.polling(none_stop=True, timeout=123)
