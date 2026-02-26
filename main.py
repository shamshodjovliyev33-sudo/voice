import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import edge_tts

# O'zingizning bot tokeningizni shu yerga qo'ying
BOT_TOKEN = "8621556358:AAHJWE7_Jng10A_5g84ylKG6m4LGx9Gjs2w"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Foydalanuvchi holatini saqlash uchun FSM
class TTSState(StatesGroup):
    waiting_for_text = State()


# Personajlar va ularning edge-tts dagi kodlari
# Personajlar va ularning edge-tts dagi to'g'ri kodlari
VOICES = {
    "🇺🇿 O'zbek (O'g'il bola)": "uz-UZ-SardorNeural",
    "🇺🇿 O'zbek (Qiz bola)": "uz-UZ-MadinaNeural",
    "🇷🇺 Rus (Erkak)": "ru-RU-DmitryNeural",
    "🇷🇺 Rus (Ayol)": "ru-RU-SvetlanaNeural",
    "🇬🇧 Ingliz (Erkak)": "en-US-ChristopherNeural",
    "🇬🇧 Ingliz (Ayol)": "en-US-JennyNeural",
    "🇹🇷 Turk (Erkak)": "tr-TR-AhmetNeural",
    "🇹🇷 Turk (Ayol)": "tr-TR-EmelNeural"
}


# 8 ta personaj uchun ReplyKeyboard
def get_voices_keyboard():
    kb = [
        [KeyboardButton(text="🇺🇿 O'zbek (O'g'il bola)"), KeyboardButton(text="🇺🇿 O'zbek (Qiz bola)")],
        [KeyboardButton(text="🇷🇺 Rus (Erkak)"), KeyboardButton(text="🇷🇺 Rus (Ayol)")],
        [KeyboardButton(text="🇬🇧 Ingliz (Erkak)"), KeyboardButton(text="🇬🇧 Ingliz (Ayol)")],
        [KeyboardButton(text="🇹🇷 Turk (Erkak)"), KeyboardButton(text="🇹🇷 Turk (Ayol)")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# /start komandasi uchun handler
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Salom! Matnni ovozga aylantiruvchi botga xush kelibsiz.\n"
        "Iltimos, o'zingizga yoqqan personajni (ovozni) tanlang:",
        reply_markup=get_voices_keyboard()
    )


# Tugma bosilganda ovozni tanlash handleri
@dp.message(F.text.in_(VOICES.keys()))
async def set_voice(message: Message, state: FSMContext):
    selected_voice = VOICES[message.text]
    # Tanlangan ovozni xotirada saqlaymiz
    await state.update_data(voice=selected_voice)
    await state.set_state(TTSState.waiting_for_text)

    await message.answer(
        f"✅ Siz **{message.text}** personajini tanladingiz!\n\nEndi menga istalgan matn yuboring, men uni shu ovozda o'qib beraman.",
        parse_mode="Markdown")


# Matn kelganda uni ovozga aylantirish handleri
@dp.message(TTSState.waiting_for_text)
async def generate_audio(message: Message, state: FSMContext):
    # Agar foydalanuvchi matn emas, rasm yoki video tashlasa
    if not message.text:
        return await message.answer("Iltimos, faqat matn yuboring.")

    user_data = await state.get_data()
    voice = user_data.get("voice")
    text = message.text

    # Unikal fayl nomi (bir vaqtda ko'p odam ishlatsa fayllar aralashib ketmasligi uchun)
    file_name = f"voice_{message.from_user.id}_{message.message_id}.ogg"

    processing_msg = await message.answer("⏳ Ovoz yozib olinmoqda...")

    try:
        # Edge-tts orqali audioni yaratish va saqlash
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(file_name)

        # Audioni Telegramga 'voice' (golos) sifatida yuborish
        audio = FSInputFile(file_name)
        await message.answer_voice(voice=audio)

    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")
    finally:
        # Xotira to'lib ketmasligi uchun jo'natib bo'lingach faylni o'chiramiz
        if os.path.exists(file_name):
            os.remove(file_name)
        await processing_msg.delete()


# Matn yuborganda agar ovoz tanlanmagan bo'lsa
@dp.message(~F.state(TTSState.waiting_for_text))
async def prompt_voice_selection(message: Message):
    await message.answer(
        "⚠️ Avval quyidagi menyudan personajni (ovozni) tanlang!",
        reply_markup=get_voices_keyboard()
    )


async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
