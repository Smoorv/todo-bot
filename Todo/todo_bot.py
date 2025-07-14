import telebot
from telebot import types
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('TOKEN')
bot = telebot.TeleBot(token)

def init_db():
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     task TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Добавить задачу", "Список задач")
    markup.add("Удалить задачу")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "To-do Bot:\n"
        "1) Нажми 'Добавить задачу'\n"
        "2) Введи текст задачи \n"
        "3) Управляй списком через кнопки",
        reply_markup=get_keyboard()
    )

@bot.message_handler(func=lambda msg: msg.text == "Добавить задачу")
def add_task(message):
    msg = bot.send_message(message.chat.id, "Напиши задачу:")
    bot.register_next_step_handler(msg, save_task)

def save_task(message):
    try:
        conn = sqlite3.connect('todo.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)",
                      (message.chat.id, message.text))
        conn.commit()
        bot.send_message(message.chat.id, f"Добавлено: '{message.text}'", reply_markup=get_keyboard())
    except:
        bot.send_message(message.chat.id, "Ошибка при сохранении задачи", reply_markup=get_keyboard())
    finally:
        conn.close()

@bot.message_handler(func=lambda msg: msg.text == "Список задач")
def tasks_list(message): 
    try:
        conn = sqlite3.connect('todo.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, task FROM tasks WHERE user_id=?", (message.chat.id,))
        tasks = cursor.fetchall()
        
        if not tasks:
            bot.send_message(message.chat.id, "Список пуст", reply_markup=get_keyboard())
        else:
            tasks_text = "\n".join([f"{i+1}. {task[1]}" for i, task in enumerate(tasks)])
            bot.send_message(message.chat.id, f"📋 Ваши задачи:\n{tasks_text}", reply_markup=get_keyboard())
    except:
        bot.send_message(message.chat.id, "Ошибка при получении списка", reply_markup=get_keyboard())
    finally:
        conn.close()

@bot.message_handler(func=lambda msg: msg.text == "Удалить задачу")
def delete_task(message):
    try:
        conn = sqlite3.connect('todo.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, task FROM tasks WHERE user_id=?", (message.chat.id,))
        tasks = cursor.fetchall()
        
        if not tasks:
            bot.send_message(message.chat.id, "Нет задач для удаления", reply_markup=get_keyboard())
            return

        tasks_text = "\n".join([f"{i+1}. {task[1]}" for i, task in enumerate(tasks)])
        msg = bot.send_message(message.chat.id, f"Выберите номер задачи для удаления:\n{tasks_text}")
        bot.register_next_step_handler(msg, process_task_number, tasks)
    except:
        bot.send_message(message.chat.id, "Ошибка при удалении", reply_markup=get_keyboard())
    finally:
        conn.close()

def process_task_number(message, tasks):
    try:
        task_num = int(message.text)
        if 1 <= task_num <= len(tasks):
            conn = sqlite3.connect('todo.db')
            cursor = conn.cursor()
            task_id = tasks[task_num-1][0]
            cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            conn.commit()
            bot.send_message(message.chat.id, f"Задача '{tasks[task_num-1][1]}' удалена", reply_markup=get_keyboard())
        else:
            bot.send_message(message.chat.id, "Неверный номер задачи", reply_markup=get_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите номер задачи", reply_markup=get_keyboard())
    except:
        bot.send_message(message.chat.id, "Ошибка при удалении", reply_markup=get_keyboard())
    finally:
        conn.close()

if __name__ == "__main__":
    print("Бот запущен")
    try:
        bot.infinity_polling()
    except:
        print("Ошибка")