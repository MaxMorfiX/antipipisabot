from pyrogram import Client, filters, idle
# Type checking imports - only used by IDE/linter, not at runtime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyrogram.types import Message

from config import API_ID, API_HASH, PHONE_NUMBER, PASSWORD, FORWARD_DELETED_MESSAGES, PIPISABOT_USER_ID, TELEGRAM_LOGS
app = Client("Antipipisabot", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER, password=PASSWORD)
# app = Client("Antipipisabot", api_id=API_ID, api_hash=API_HASH)

#^
#you can also login with only these two, and then pyrogram would prompt you
#to enter phone number & password on your first login

bot_phrases_to_pass = (

    "твой писюн вырос",
    "твой писюн сократился",
    "ты уже играл.",
    "Теперь он равен",
    "Следующая попытка завтра!",

    "Сейчас он равен",
    "Ты занимаешь",

    "Топ 10 игроков",
    "Данная команда доступна только в личке с ботом"
    
    "Привет! я линейка — бот для чатов",
    "Смысл бота: бот работает только в чатах",
    "/dick, где в ответ получит от бота рандомное",
    "Рандом работает от -5 см до +10 см",
    "Команды бота:",
    "/dick — Вырастить/уменьшить пипису",
    "/top_dick — Топ 10 пипис чата",
    "/stats — Статистика в виде картинки",
    "/global_top — Глобальный топ 10 игроков",
    "/buy — Покупка доп. попыток",
    "Контакты:",
    
)

@app.on_message(filters.incoming & filters.bot & filters.group & filters.user(PIPISABOT_USER_ID))
async def got_message_from_bot(client: 'Client', message: 'Message'):
    
    if not message.text:
        message.text = message.caption or "none"
    
    await log(f"\ngot message in group {message.chat.title} ({message.chat.id}) from {message.from_user.first_name} ({message.from_user.id}) with id {message.id}:")
    await log(message.text)
    
    if message.text == "none": return
    
    for phrase in bot_phrases_to_pass:
        if phrase not in message.text: continue
        
        await log(f"matched the string '{phrase}', exiting the function")
        return

    await log("didn't find any match, the message would be deleted")
    
    await delete_message(message)

async def delete_message(message: 'Message'):
    
    await log("Deleting...")
    
    try:
        if(FORWARD_DELETED_MESSAGES): await message.forward(chat_id=FORWARD_DELETED_MESSAGES)
    except Exception as e:
        await log(e)
    
    try:
        await message.delete()
        await log("#deleted successfully\nСообщение было удалено успешно!", True)
    except Exception as e:
        await log(f"#error occured during message deletion: {e}", True)
        # await app.send_message(message.chat.id, f"Ошибка при удалении рекламы: {e}")
    
async def log(text: str, in_forwarded_chat_too: bool = False):
    
    print(text)
    
    if in_forwarded_chat_too:
        if FORWARD_DELETED_MESSAGES: await app.send_message(FORWARD_DELETED_MESSAGES, text)
    
    if(not TELEGRAM_LOGS): return
    
    await app.send_message(TELEGRAM_LOGS, text)

async def after_startup():
     
    print("Connecting to server...")
    
    async with app:
        
        print("Initializing chats...")
        
        async for dialog in app.get_dialogs():
            pass
        #^this is fix for the https://docs.pyrogram.org/faq/peer-id-invalid-error error
        #where the chat id refers to a user or chat client current session hasn’t met yet,
        #so in the beginning of each session I get all chats the user has so that this error has no chance of occuring

        await log("Application is online!")
       
        await idle()

app.run(after_startup())