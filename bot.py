import telebot
import time
import datetime
import re
import json
import threading
import random
import pytz

TOKEN = 'TOKEN'
bot = telebot.TeleBot(TOKEN)

#Файл для хранения текущей недели (числитель или знаменатель)
WEEK_FILE = 'week_status.txt'

#Файл для хранения списка чатов
CHATS_FILE = 'chats.json'

#Файл с заготовками приветсвия
MESSAGES_FILE = 'messages.txt'

#установка времени по МСК (т.к. на vds он может быть другим)
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

#чтение текущего состояния недели из файла
def read_week_status():
    try:
        with open(WEEK_FILE, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except UnicodeDecodeError:
        try:
            with open(WEEK_FILE, 'r', encoding='latin-1') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Ошибка при чтении файла {WEEK_FILE}: {e}")
            return 'Числитель'
    except FileNotFoundError:
        return 'Числитель'

#запись состояния недели в тхт файл
def write_week_status(status):
    with open(WEEK_FILE, 'w', encoding='utf-8') as file:
        file.write(status)

#чтение списка чатов из файла
def read_chats():
    try:
        with open(CHATS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

#запись списка чатов в файл
def write_chats(chats):
    with open(CHATS_FILE, 'w', encoding='utf-8') as file:
        json.dump(chats, file, ensure_ascii=False)

#чтение списка сообщений из файла
def read_messages():
    try:
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        return ["Привет-привет! Следующая неделя - {status}"]

#добавления нового чата в список
def add_chat(chat_id):
    chats = read_chats()
    if chat_id not in chats:
        chats.append(chat_id)
        write_chats(chats)
        print(f"Чат {chat_id} добавлен в список")

#переключение недели
def toggle_week_status():
    current_status = read_week_status()
    new_status = 'Знаменатель' if current_status == 'Числитель' else 'Числитель'
    write_week_status(new_status)
    return new_status

#выбор случайного сообщения
def get_random_message(status):
    messages = read_messages()
    message_template = random.choice(messages)
    return message_template.format(status=status.lower())

#переименование чатов
def rename_chats():
    new_status = read_week_status()
    chats = read_chats()
    for chat_id in chats:
        try:

            chat = bot.get_chat(chat_id)
            current_title = chat.title

            new_base_title = re.sub(r'\s*(Числитель|Знаменатель)\s*$', '', current_title, flags=re.IGNORECASE).strip()

            new_title = f"{new_base_title} {new_status}"

            if current_title != new_title:
                bot.set_chat_title(chat_id, new_title)
                print(f"Переименован чат {chat_id} в '{new_title}'")

                random_message = get_random_message(new_status)
                bot.send_message(chat_id, random_message)
            else:
                print(f"Чат {chat_id} уже имеет корректное название '{current_title}'")
        except Exception as e:
            print(f"Ошибка при переименовании чата {chat_id}: {e}")


def check_and_rename_chats():
    while True:
        now = datetime.datetime.now(MOSCOW_TZ)
        if now.weekday() == 6 and now.hour == 18 and now.minute == 0:
            rename_chats()
            toggle_week_status()
            time.sleep(60)

# Детект добавления бота в чат
@bot.message_handler(content_types=['new_chat_members'])
def on_chat_add(message):
    chat_id = message.chat.id
    add_chat(chat_id)

# Запуск бота и проверка расписания
if __name__ == '__main__':
    print("Бот работает...")
    # Запускаем проверку времени в фоновом потоке
    thread = threading.Thread(target=check_and_rename_chats)
    thread.start()
    # Запускаем бота
    bot.infinity_polling()
