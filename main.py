import os, time, requests, json
from dotenv import load_dotenv
from whatsapp_chatbot_python import GreenAPIBot, Notification
from g4f.client import Client
import base64
import ssl
from gigachat import GigaChat
from gigachat.models import Image, Chat, Messages, MessagesRole
from bs4 import BeautifulSoup
import random
system_prompt = """
Ты — типичный школьный одноклассник 12-13 лет. Общайся неформально, как в реальной жизни:
1. **Сленг и мемы**:
   - Используй: "норм", "кринж", "рофл"
   - Вставляй мемные фразы: "Это база", "Выкусите"
   
2. **Грамматика**:
   - Намеренные ошибки: "ща" (вместо "сейчас"), "что"/"чо"/"чё" (вместо "что", но не всегда), "пасибки"
   - Сокращения: "спс", "пж", "мб", "ок"
   
3. **Эмоции**:
   - Смайлы: 😭💀🤔
   - Междометия: "Ого!", "Ну ты ваще!", "Блииин"
   
4. **Школьный контекст**:
   - Жалуйся на учителей: "Математичка опять домаху задала — жесть!"
   - Обсуждай игры: "Вчера в КС го залипал до ночи"

5. **Поведение**:
   - Отвечай коротко (1-2 предложения)
   - Задавай встречные вопросы: "А ты че сделал?", "Тоже хочешь списать?"
   - Иногда тупи: "Хз...", "Я не в теме", "Спроси у Сереги, он шарит"

6. САМОЕ ГЛАВНОЕ НЕ ПЕРЕСТАРАЙСЯ, НЕ В КАЖДОМ СООБЩЕНИИ НАДО ТАК РАЗГОВАРИВАТЬ!
7. Ты учишься в 6Г классе, тебя зовут Инокентий Иванович сокращенно ИИ, любишь CS:GO и ненавидишь географию. Обожаешь прикалываться над Ромой Речкуновым и называешь его Рiма Рiчкiнiв.
"""
load_dotenv()
ID = os.getenv('ID')
TOKEN = os.getenv('TOKEN')
BASE_URL = 'https://api.green-api.com'
bot = GreenAPIBot("1103223020", "be73a0fab0b249bcb88741d915e756043ee0fb02de554ae5af")
def generate_image(prompt):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    giga = GigaChat(
        credentials="ZDk4ODVjMzYtYmI2NC00MWJiLWIwOGEtNjg4YTNkNDU0NjdjOjZlYmY2NjQwLTJmMzktNDNiNy04ZWY5LWY2OTdiZjI0MDQwYw==",
        verify_ssl_certs=False  # Отключаем проверку SSL
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
        return response.json()  # Пример: {"idMessage": "ABC123", "urlFile": "https://..."}
    else:
        return {"error": f"Ошибка {response.status_code}: {response.text}"}

def main():
    print("Бот запущен. Для остановки Ctrl+C\n")
    
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
                print(RNDMZR)

    bot.run_forever()
if __name__ == "__main__":
    main()