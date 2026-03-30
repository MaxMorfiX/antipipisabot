from pyrogram import Client, filters, idle
# Type checking imports - only used by IDE/linter, not at runtime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyrogram.types import Message

from config import API_ID, API_HASH, PHONE_NUMBER, PASSWORD, FORWARD_DELETED_MESSAGES, PIPISABOT_USER_ID, TELEGRAM_LOGS, TEST_MODE
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

# Build the base filter
base_filter = filters.incoming & filters.bot & filters.group & filters.user(PIPISABOT_USER_ID)

# If in test mode, also include outgoing messages
if TEST_MODE:
    base_filter = base_filter | filters.outgoing


@app.on_message(base_filter)
async def got_message_from_bot(client: 'Client', message: 'Message'):
    
    text = extract_visible_text(message)
    
    await log(f"\ngot message in group {message.chat.title} ({message.chat.id}) from {message.from_user.first_name} ({message.from_user.id}) with id {message.id} with the following extracted text:\n\n{text}")
    
    for phrase in bot_phrases_to_pass:
        if phrase not in text: continue
        
        await log(f"matched the string '{phrase}', exiting the function and keeping the message")
        
        return
    
    await log("dinn't find a match in the extracted text, trying to match the raw message just in case...")
    
    raw_message = str(message)
    
    for phase in bot_phrases_to_pass:
        if phase not in raw_message: continue
        
        await log(f"#strange matched the string '{phase}' in the raw message string, exiting the function and keeping the message")
        
        return

    await log("didn't find any match, the message would be deleted")
    
    await delete_message(message)

#DeepSeek said this might be better or so lol
def extract_visible_text(message):
    
    parts = []

    # Basic text fields
    if message.text:
        parts.append(message.text)
    if message.caption:
        parts.append(message.caption)

    # Poll
    if message.poll:
        parts.append(message.poll.question)
        for opt in message.poll.options:
            parts.append(opt.text)

    # Game
    if message.game:
        parts.append(message.game.title)
        if message.game.description:
            parts.append(message.game.description)

    # Sticker emoji
    if message.sticker and message.sticker.emoji:
        parts.append(message.sticker.emoji)

    # Contact
    if message.contact:
        if message.contact.first_name:
            parts.append(message.contact.first_name)
        if message.contact.last_name:
            parts.append(message.contact.last_name)
        if message.contact.phone_number:
            parts.append(message.contact.phone_number)

    # Venue
    if message.venue:
        parts.append(message.venue.title)
        parts.append(message.venue.address)

    # Audio
    if message.audio:
        if message.audio.title:
            parts.append(message.audio.title)
        if message.audio.performer:
            parts.append(message.audio.performer)

    # Service: new chat title
    if message.new_chat_title:
        parts.append(message.new_chat_title)

    # Pinned message – contains its own text, so we call this same function recursively
    if message.pinned_message:
        pinned_text = extract_visible_text(message.pinned_message)
        if pinned_text:
            parts.append(pinned_text)

    # Inline keyboard buttons
    if message.reply_markup and message.reply_markup.inline_keyboard:
        for row in message.reply_markup.inline_keyboard:
            for button in row:
                if button.text:
                    parts.append(button.text)

    # Join everything, filtering out empty strings
    return "\n".join(filter(None, parts))

async def delete_message(message: 'Message'):
    
    await log("Deleting...")
    
    try:
        if(FORWARD_DELETED_MESSAGES & TEST_MODE): await message.forward(chat_id=TELEGRAM_LOGS)
        if(FORWARD_DELETED_MESSAGES): await message.forward(chat_id=FORWARD_DELETED_MESSAGES)
    except Exception as e:
        await log(e)
        
        if "[400 PEER_ID_INVALID]" not in str(e) and "Peer id invalid" not in str(e): return
        
        await log("trying to refresh all chat id's...")
        
        await initialize_chats()
        
        await log("succes!? (idk)")
        
        await retry_message_forwarding(message)
    
    try:
        await message.delete()
        await log("#deleted successfully\nСообщение было удалено успешно!", True)
    except Exception as e:
        await log(f"#error occured during message deletion: {e}", True)
        # await app.send_message(message.chat.id, f"Ошибка при удалении рекламы: {e}")

async def retry_message_forwarding(message): #yeah code duplication but imo it's cleaner like this
    log("trying to forward the message once more...")
    try:
        await message.forward(chat_id=FORWARD_DELETED_MESSAGES)
    except Exception as e:
        await log(e)
        
        if e != 'Telegram says: [400 PEER_ID_INVALID] - The peer id being used is invalid or not known yet. Make sure you meet the peer before interacting with it (caused by "messages.ForwardMessages")': return
        
        await log("refreshing all chat id's...")
        await initialize_chats()
        await log("succes!? (prob not)")

async def initialize_chats():
    async for dialog in app.get_dialogs():
        pass
    
    #^this is fix for the https://docs.pyrogram.org/faq/peer-id-invalid-error error
    #where the chat id refers to a user or chat client current session hasn’t met yet,
    #so in the beginning of each session I get all chats the user has so that this error has no chance of occuring

async def log(text: str, in_forwarded_chat_too: bool = False):
    
    print(text)
    
    if len(str(text)) > 4096:
        log("#the text is too long, it will be truncated for logging purposes")
        text = text[:4093] + "..."
    
    try:
    
        if in_forwarded_chat_too:
            if FORWARD_DELETED_MESSAGES: await app.send_message(FORWARD_DELETED_MESSAGES, text)
    
    except Exception as e:
        await print(f"#error occured during 1st stage of logging (into forwarded messages chat): {e}", True)
    
    
    if(not TELEGRAM_LOGS): return
    
    try:
    
        await app.send_message(TELEGRAM_LOGS, text)
    
    except Exception as e:
        await print(f"#error occured during 2nd stage of logging (into telegram log chat): {e}", True)

async def after_startup():
     
    print("Connecting to server...")
    
    async with app:
        
        print("Initializing chats...")
        
        await initialize_chats()

        await log("Application is online!")
       
        await idle()

app.run(after_startup())