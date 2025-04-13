from gigachat.models import Image, Chat, Messages, MessagesRole
from whatsapp_chatbot_python import GreenAPIBot, Notification
from http.server import BaseHTTPRequestHandler, HTTPServer
import os, time, requests, json
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from gigachat import GigaChat
from g4f.client import Client
from threading import Thread
from dateutil import tz
import datetime
import random
import base64
import ssl
system_prompt = """
Ты — типичный школьный одноклассник 12-13 лет. Общайся неформально, как в реальной жизни:
   - Отвечай коротко (1-2 предложения)
   - Раз в 10 сообщений тупи: "Хз...", "Я не знаю"
   - Ты учишься в 6Г классе, тебя зовут Инокентий Иванович сокращенно ИИ, любишь CS2 и ненавидишь географию.
"""
load_dotenv()
kesha = True
ID = os.getenv('ID')
TOKEN = os.getenv('TOKEN')
CRD = os.getenv('CRD')
BASE_URL = 'https://api.green-api.com'
bot = GreenAPIBot(ID, TOKEN)
def generate_image(prompt):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    giga = GigaChat(
        credentials=CRD,
        verify_ssl_certs=False
    )

    payload = Chat(
        messages=[
            Messages(
                role=MessagesRole.SYSTEM,
                content="Ты — Василий Кандинский"
            ),
            Messages(
                role=MessagesRole.USER,
                content=prompt
                )
            ],
        function_call="auto",
    )

    response = giga.chat(payload).choices[0].message.content
    file_id = BeautifulSoup(response, "html.parser").find('img').get("src")
    image = giga.get_image(file_id)
    with open('image.jpg', mode="wb") as fd:
        fd.write(base64.b64decode(image.content))

def send_file_by_upload(chat_id: str, file_path: str, caption: str = "") -> dict:
    url = f"https://api.green-api.com/waInstance{ID}/SendFileByUpload/{TOKEN}"
    with open(file_path, "rb") as file:
        files = {"file": (os.path.basename(file_path), file)}
        data = {"chatId": chat_id, "caption": caption}
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Ошибка {response.status_code}: {response.text}"}
#ДОБАВЛЕНО_____________________________________________________________________________________________________________
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/ping':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

def run_ping_server():
    server = HTTPServer(('0.0.0.0', 8080), PingHandler)
    print("Ping server started on port 8080")
    server.serve_forever()

def keep_alive():
    while True:
        try:
            requests.get("https://whatsappbot-qv2p.onrender.com/ping", timeout=5)
            print("Keep-alive ping sent")
        except Exception as e:
            print(f"Keep-alive error: {str(e)}")
        time.sleep(300)

def main():

    ping_thread = Thread(target=run_ping_server)
    ping_thread.daemon = True
    ping_thread.start()
    
    keepalive_thread = Thread(target=keep_alive)
    keepalive_thread.daemon = True
    keepalive_thread.start()
#ДОБАВЛЕНО_____________________________________________________________________________________________________________
    @bot.router.message(command="help")
    def handle_help(notification: Notification):
        global kesha
        if kesha == True:
            kesha_status = "✅"
        elif kesha == False:
            kesha_status = "❌"
        notification.answer(f"""🤖 Информация о боте:
Это ИИ-бот Инокентий (Кеша) — твой виртуальный ассистент-одноклассник

⚡ Доступные команды:
/help — показать это сообщение
/kesha — переключить случайные ответы Инокентия (сейчас: {kesha_status})
/gpt [текст] — задать вопрос обычному ИИ
/img [описание] — сгенерировать изображение

🔎 Как общаться:
Просто напиши «ИИ», «Инокентий» или «Кеша» в начале сообщения!(или если /kesha включен бот возможно ответит сам)""")
    @bot.router.message(command="kesha")
    def handle_keshasettings(notification: Notification):
        global kesha
        if kesha == True:
            kesha = False
            notification.answer("😵 Выключаю внезапные ответы Инокентия!")
        elif kesha == False:
            kesha = True
            notification.answer("🫡 Включаю внезапные ответы Инокентия!")

    @bot.router.message(command="time")
    def handle_time(notification: Notification):
        novosibirsk_tz = tz.gettz('Asia/Novosibirsk')
        current_time = datetime.datetime.now(novosibirsk_tz)
        summer_start = datetime.datetime(2025, 6, 1, tzinfo=novosibirsk_tz)
        holidays_start = datetime.datetime(2025, 5, 24, tzinfo=novosibirsk_tz)
        time_to_summer = summer_start - current_time
        time_to_holidays = holidays_start - current_time
        response = (
            f"⏰ *Текущее время (Новосибирск):*\n"
            f"{current_time.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            f"☀️ *До лета (01.06.2025):*\n"
            f"{time_to_summer.days} дней {time_to_summer.seconds//3600} часов\n\n"
            f"🎒 *До каникул (24.05.2025):*\n"
            f"{time_to_holidays.days} дней {time_to_holidays.seconds//3600} часов\n\n"
            f"Точное время: {current_time.strftime('%H:%M:%S')}"
        )
        notification.answer(response)

    @bot.router.message(command="gpt")
    def handle_gpt(notification: Notification):
        try:
            client = Client()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": notification.message_text.split(maxsplit=1)[1]}],
                web_search=False
            )
            notification.answer(response.choices[0].message.content)
        except Exception as e:
            print(f"Ошибка: {str(e)}")
            notification.answer("❌ Произошла ошибка. Пожалуйста, попробуйте другой запрос или повторите позже.")
    
    @bot.router.message(command="img")
    def handle_img(notification: Notification):
        try:
            prompt = notification.message_text.split(maxsplit=1)[1]
            generate_image(prompt=prompt)  
            image_path = "image.jpg"
            chat_id = notification.chat
            send_file_by_upload(
                chat_id=chat_id,
                file_path=image_path,
                caption=f"Сгенерировано по запросу: {prompt}"
            )
            os.remove(image_path)
        except Exception as e:
            print(f"Ошибка: {str(e)}")
            notification.answer("❌ Произошла ошибка. Пожалуйста, попробуйте другой запрос или повторите позже.")
            
    @bot.router.message(type_message=["textMessage", "extendedTextMessage"])
    def message_handler(notification: Notification) -> None:
        global kesha
        user_text = notification.message_text.lower()
        bot_name_triggers = ["ии", "инокентий", "кеша"]
        if any(name in user_text for name in bot_name_triggers):
            client = Client()
            response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Только что тебя назвали: '{user_text}'. Ответь как Инокентий"}], temperature=0.5,
                web_search=False)
            notification.answer(response.choices[0].message.content)
        else:
            if kesha == True:
                RNDMZR = random.randint(0, 100)
                if RNDMZR > 60:
                    try:
                        client = Client()
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": notification.message_text}], temperature=0.7,
                            web_search=False
                        )
                        notification.answer(response.choices[0].message.content)
                    except Exception as e:
                        print(f"Ошибка: {str(e)}")
                        notification.answer("❌ Произошла ошибка. Пожалуйста, попробуйте другой запрос или повторите позже.")
                else:
                    pass
            else:
                pass

    bot.run_forever()
if __name__ == "__main__":
    main()
