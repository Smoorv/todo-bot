import telebot
from telebot import types
import sqlite3
import logging
from dotenv import load_dotenv
import os

print("Текущая папка:", os.getcwd())  
print("Файлы в папке:", os.listdir())  
#Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Токен бота
loaded = load_dotenv()
token = os.getenv('TOKEN')
if not token:
    logger.error("Токен не найден в .env!")
    exit(1)
bot = telebot.TeleBot(token)


#База данных заявок
conn = sqlite3.connect('visits.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS requests 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   name TEXT, 
                   phone TEXT)''')
conn.commit()


def get_keyboard():
    """Основные кнопки"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    buttons = [
        types.KeyboardButton("Прайс лист"),
        types.KeyboardButton("Контакты"),
        types.KeyboardButton("Оставить заявку"),
        types.KeyboardButton("/cancel")
    ]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите интересуюищй вас раздел:", reply_markup = get_keyboard())

#Обработка кнопок
@bot.message_handler(func=lambda msg: msg.text == "/cancel")
def cancel_operation(message):
    bot.send_message(message.chat.id, "Текущая операция отменена. Чтобы вы хотели сделать?", reply_markup=get_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "Прайс лист")
def price(message):
    markup = types.InlineKeyboardMarkup()
    btn_hair = types.InlineKeyboardButton("Волосы", callback_data="hair")
    btn_nails = types.InlineKeyboardButton("Ногти", callback_data="nails")
    markup.add(btn_hair,btn_nails)
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "Контакты")
def contacts(message):
    contact_text = """
    Адрес: Волгоград, ул. Колотушкина 20
    Телефон: +7 (999) 123-45-67
    """
    markup = types.InlineKeyboardMarkup()
    btn_insta = types.InlineKeyboardButton("Instagram", url = "https://instagram.com/example..")
    btn_website = types.InlineKeyboardButton("Наш сайт", url = "https://example.com")
    markup.add(btn_insta,btn_website)
    bot.send_message(message.chat.id, contact_text, reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "Оставить заявку")
def request(message):
    msg = bot.send_message(message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    name = message.text
    if not name.isalpha() or len(name) < 2:
        bot.send_message(message.chat.id, "Имя должно содержать только буквы и быть не короче 2 символов")
        return
    msg = bot.send_message(message.chat.id, "Введите ваш номер телефона:")
    bot.register_next_step_handler(msg, get_phone,name)

def get_phone(message, name):
    phone = message.text
    if not validate_phone(phone):
        bot.send_message(message.chat.id, "Номер должен быть в формате +7XXXXXXXXXX")
        return
    try:
        cursor.execute("INSERT INTO requests (...) VALUES (?, ?)", (name, phone))
        conn.commit()
        bot.send_message(message.chat.id, "Заявка принята!")
    except sqlite3.Error as e:
        logger.error(f"Ошибка БД: {e}")
        bot.send_message(message.chat.id, "Ошибка сохранения заявки.")
    conn.commit()
    bot.send_message(message.chat.id, "Спасибо! Мы скоро вам перезвоним.")

def validate_phone(phone: str) -> bool:
    return phone.startswith("+7") and len(phone) == 12

#Обработка inline кнопок
@bot.callback_query_handler(func=lambda call: True)
def casllback_handler(call):
    if call.data == "hair":
        bot.send_message(call.message.chat.id, "Услуги для волос:\n- Модельная стрижка: 1800р\n- Окрашивание: 3000р")
    elif call.data == "nails":
        bot.send_message(call.message.chat.id, "Маникюр:\n- Классический: 1000р\n- Дизайн: +500р")

if __name__ == "__main__":
    logger.info("Бот запущен")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")
    finally:
        conn.close()
        logger.info("Бот остановлен")