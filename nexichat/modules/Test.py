from pyrogram import Client, filters
from pyrogram.types import Message
from nexichat import nexichat as app, mongo, db
from MukeshAPI import api
from nexichat.modules.helpers import chatai, CHATBOT_ON, languages

lang_db = db.ChatLangDb.LangCollection
message_cache = {}

async def get_chat_language(chat_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else None

@app.on_message(filters.text, group=2)
async def store_messages(client, message: Message):
    global message_cache

    chat_id = message.chat.id
    chat_lang = await get_chat_language(chat_id)

    if not chat_lang:
        if message.from_user and message.from_user.is_bot:
            return

        if chat_id not in message_cache:
            message_cache[chat_id] = []

        message_cache[chat_id].append(message)

        if len(message_cache[chat_id]) >= 10:
            # Prepare message history
            history = "\n".join(
                [f"{i + 1}. \"{msg.text}\"" for i, msg in enumerate(message_cache[chat_id])]
            )

            # Updated prompt
            user_input = f"""
Niche diye gaye 10 messages ko carefully analyze karo. Har message ka language detect karo aur unhe count karo.

Jis language ka count sabse zyada hoga, us language ka ISO 639-1 lang code output me do. Sirf lang code return karo, aur kuch nahi.

Yeh rahe messages:
{history}

Lang code sirf un languages ka output karo jo niche diye gaye supported languages ke list me hain:
{{'af': 'afrikaans', 'sq': 'albanian', 'am': 'amharic', 'ar': 'arabic', 'hy': 'armenian', 'as': 'assamese', 'ay': 'aymara', 'az': 'azerbaijani', 'bm': 'bambara', 'eu': 'basque', 'be': 'belarusian', 'bn': 'bengali', 'bho': 'bhojpuri', 'bs': 'bosnian', 'bg': 'bulgarian', 'ca': 'catalan', 'ceb': 'cebuano', 'ny': 'chichewa', 'zh-CN': 'chinese (simplified)', 'zh-TW': 'chinese (traditional)', 'co': 'corsican', 'hr': 'croatian', 'cs': 'czech', 'da': 'danish', 'dv': 'dhivehi', 'doi': 'dogri', 'nl': 'dutch', 'en': 'english', 'eo': 'esperanto', 'et': 'estonian', 'ee': 'ewe', 'tl': 'filipino', 'fi': 'finnish', 'fr': 'french', 'fy': 'frisian', 'gl': 'galician', 'ka': 'georgian', 'de': 'german', 'el': 'greek', 'gn': 'guarani', 'gu': 'gujarati', 'ht': 'haitian creole', 'ha': 'hausa', 'haw': 'hawaiian', 'iw': 'hebrew', 'hi': 'hindi', 'hmn': 'hmong', 'hu': 'hungarian', 'is': 'icelandic', 'ig': 'igbo', 'ilo': 'ilocano', 'id': 'indonesian', 'ga': 'irish', 'it': 'italian', 'ja': 'japanese', 'jw': 'javanese', 'kn': 'kannada', 'kk': 'kazakh', 'km': 'khmer', 'rw': 'kinyarwanda', 'gom': 'konkani', 'ko': 'korean', 'kri': 'krio', 'ku': 'kurdish (kurmanji)', 'ckb': 'kurdish (sorani)', 'ky': 'kyrgyz', 'lo': 'lao', 'la': 'latin', 'lv': 'latvian', 'ln': 'lingala', 'lt': 'lithuanian', 'lg': 'luganda', 'lb': 'luxembourgish', 'mk': 'macedonian', 'mai': 'maithili', 'mg': 'malagasy', 'ms': 'malay', 'ml': 'malayalam', 'mt': 'maltese', 'mi': 'maori', 'mr': 'marathi', 'mni-Mtei': 'meiteilon (manipuri)', 'lus': 'mizo', 'mn': 'mongolian', 'my': 'myanmar', 'ne': 'nepali', 'no': 'norwegian', 'or': 'odia (oriya)', 'om': 'oromo', 'ps': 'pashto', 'fa': 'persian', 'pl': 'polish', 'pt': 'portuguese', 'pa': 'punjabi', 'qu': 'quechua', 'ro': 'romanian', 'ru': 'russian', 'sm': 'samoan', 'sa': 'sanskrit', 'gd': 'scots gaelic', 'nso': 'sepedi', 'sr': 'serbian', 'st': 'sesotho', 'sn': 'shona', 'sd': 'sindhi', 'si': 'sinhala', 'sk': 'slovak', 'sl': 'slovenian', 'so': 'somali', 'es': 'spanish', 'su': 'sundanese', 'sw': 'swahili', 'sv': 'swedish', 'tg': 'tajik', 'ta': 'tamil', 'tt': 'tatar', 'te': 'telugu', 'th': 'thai', 'ti': 'tigrinya', 'ts': 'tsonga', 'tr': 'turkish', 'tk': 'turkmen', 'ak': 'twi', 'uk': 'ukrainian', 'ur': 'urdu', 'ug': 'uyghur', 'uz': 'uzbek', 'vi': 'vietnamese', 'cy': 'welsh', 'xh': 'xhosa', 'yi': 'yiddish', 'yo': 'yoruba', 'zu': 'zulu'}}.

Agar kisi message ki language supported list me nahi ho to usko ignore karo.
"""

            
            response = api.gemini(user_input)
            lang_code = response["results"]

            
            await message.reply_text(f"Lang code detected for this chat:- {lang_code}")

            
            message_cache[chat_id].clear()
