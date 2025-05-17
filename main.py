import asyncio
import json
import random
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart

# 🔐 ТВОЇ ДАНІ
BOT_TOKEN = "8130153292:AAE1uS6TkFGgOZyXdppz_Li_1RiAL_7C5o0"
# 📲 Ініціалізація
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(
    parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# 📥 Завантаження питань із JSON-файлу
with open("questions.json", "r", encoding="utf-8") as f:
    all_questions = json.load(f)

# 🧠 FSM


class TestState(StatesGroup):
    current_question = State()
    answers = State()
    selected_questions = State()


# 🗂 Зберігання результатів
user_results = {}  # user_id: {"history": ["62%", "71%", "99%"]}

# 📋 Меню
menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🚀 Пройти тест", callback_data="start_test")],
    [InlineKeyboardButton(text="📊 Мої результати",
                          callback_data="show_results")],
    [InlineKeyboardButton(text="💡 Підказки по експлаатації",
                          callback_data="show_tips")]
])

# ▶️ Команда /start


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await bot.send_photo(
        chat_id=message.chat.id,
        # заміни на свій файл або шлях
        photo=types.FSInputFile("menu_image.png"),
        caption="❤️ Це тест на сумісність з Муляром Сергієм.\n"
                "В тесті будуть питання на знання його поведінки і про нього самого. Щасти!!!"
    )

    # Відправляємо кнопки
    await message.answer("👇 Вибирай:", reply_markup=menu_keyboard)
# ☑️ Меню вибір


@router.callback_query(lambda c: c.data in ["start_test", "show_results", "show_tips"])
async def handle_menu(callback: CallbackQuery, state: FSMContext):
    if callback.data == "start_test":
        await state.clear()
        selected = random.sample(all_questions, 10)
        await state.set_state(TestState.current_question)
        await state.update_data(answers=[], current=0, selected_questions=selected)
        await send_question(callback.message.chat.id, 0, state)

    elif callback.data == "show_results":
        history = user_results.get(
            callback.from_user.id, {}).get("history", [])
        if history:
            formatted = "\n".join(
                [f"{i+1}. {res}" for i, res in enumerate(history)])
            await callback.message.answer(f"<b>Останні результати:</b>\n{formatted}", parse_mode=ParseMode.HTML)
        else:
            await callback.message.answer("У тебе ще немає результатів. Пройди тест ✨")

    elif callback.data == "show_tips":
        tips = (
            "❤️ Долби його в дьосна як дика білка.\n"
            "📞 Не зли цього красунчика.\n"
            "🎭 Грайся, але не з бубенчиками...\n"
            "🍝 Годуй.(лоток купила?).\n"
            "🧠 І головне — не забувай кайфувати."
        )
        await callback.message.answer(tips)

    await callback.answer()

# ❓ Показ питання


async def send_question(chat_id, index, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_questions", [])
    q = selected[index]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=opt["text"], callback_data=f"answer_{index}_{i}")]
        for i, opt in enumerate(q["options"])
    ])
    await bot.send_message(chat_id, f"{index+1}/10: {q['text']}", reply_markup=keyboard)
    await state.set_state(TestState.current_question)
    await state.update_data(current=index)

# ✅ Обробка відповіді


@router.callback_query(lambda c: c.data and c.data.startswith("answer_"))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    question_index = int(parts[1])
    option_index = int(parts[2])

    data = await state.get_data()
    answers = data.get("answers", [])
    selected = data.get("selected_questions", [])
    answer_obj = selected[question_index]["options"][option_index]
    score = answer_obj.get("score", 0)

    answers.append(score)
    await state.update_data(answers=answers)
    await callback.message.delete()

    if question_index + 1 < len(selected):
        await send_question(callback.message.chat.id, question_index + 1, state)
    else:
        await show_result(callback.message.chat.id, answers, callback.from_user.id)

    await callback.answer()

# 🎯 Показ результату


async def show_result(chat_id, answers, user_id):
    total_score = sum(answers)
    percent = min(100, int(total_score * 100 / (10 * 10)))
    bar = int(percent / 10) * "█" + (10 - int(percent / 10)) * "░"

    if percent >= 90:
        result_phrase = "Бейбі я уже стою дибом!!!"
    elif percent >= 70:
        result_phrase = "Їбать уже жахає трохи від такого конекта"
    elif percent >= 50:
        result_phrase = "Є хімія. Але не потрібно почитати біологію."
    elif percent >= 30:
        result_phrase = "Краще, ніж нічого..."
    else:
        result_phrase = "Це токсичний і романтичний мікс. Може, це й є любов."

    text = f"<b>Тест покзує сумісність: {percent}%</b>\n{bar}\n\n{result_phrase}"

    history = user_results.get(user_id, {}).get("history", [])
    history = ([f"{percent}%"] + history)[:3]
    user_results[user_id] = {"history": history, "text": text}

    await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML, reply_markup=menu_keyboard)

# 🚀 Запуск


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
