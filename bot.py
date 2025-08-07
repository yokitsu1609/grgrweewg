import asyncio
import logging
import sys


# from os import getenv
from aiogram.exceptions import TelegramNetworkError
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from commands import BOT_COMMANDS, FILMS_COMMAND

from data import edit_film, get_films, add_film, delete_film
from keyboards import films_keyboard_markup, FilmCallback

from models import Film
from aiogram.types import URLInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile

from commands import *
from external import async_log_function_call
from config import TOKEN_BOT as TOKEN


from aiogram import F
from kinopoisk import search_kinopoisk
from keyboards import get_kinopoisk_keyboard


class MovieRatingStates(StatesGroup):
    rate_query = State()
    set_rating = State()



class FilmForm(StatesGroup):
    name = State()
    description = State()
    rating = State()
    genre = State()
    actors = State()
    poster = State()


dp = Dispatcher()

#команда старт
@dp.message(Command("start"))
@async_log_function_call
async def start(message: Message) -> None:
    await message.answer(
        f"Вітаю, {message.from_user.full_name}!\n"
        "Я перший бот Python розробника user."
    )

#список
@dp.message(FILMS_COMMAND)
@async_log_function_call
async def films_list(message: Message) -> None:
    data = get_films()
    markup = films_keyboard_markup(films_list=data)
    await message.answer(
        f"Перелік фільмів. Натисніть на назву фільму для отримання деталей.",
        reply_markup=markup
    )

#кнопки
@dp.callback_query(FilmCallback.filter())
@async_log_function_call
async def callb_film(callback: CallbackQuery, callback_data: FilmCallback) -> None:
    print(callback_data)
    film_id = callback_data.id
    film_data = get_films(film_id=film_id)
    film = Film(**film_data)

    text = f"Фільм: {film.name}\n" \
           f"Опис: {film.description}\n" \
           f"Рейтинг: {film.rating}\n" \
           f"Жанр: {film.genre}\n" \
           f"Актори: {', '.join(film.actors)}\n"
    try:
        await callback.message.answer_photo(
            caption=text,
            photo=URLInputFile(
                film.poster,
                filename=f"{film.name}_poster.{film.poster.split('.')[-1]}"
            )
        )
    except TelegramNetworkError:
        await callback.message.answer_photo(
            caption=text,
            photo=FSInputFile(
                "no-image.png",
                filename=f"{film.name}_poster.{film.poster.split('.')[-1]}"
            )
        )

#новий фiльм в список
@dp.message(FILM_CREATE_COMMAND)
@async_log_function_call
async def film_create(message: Message, state: FSMContext) -> None:
    await state.set_state(FilmForm.name)
    await message.answer(
        f"Введіть назву фільму.",
        reply_markup=None,
    )

#описання
@dp.message(FilmForm.name)
@async_log_function_call
async def film_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(FilmForm.description)
    await message.answer(
        f"Введіть опис фільму.",
        reply_markup=None,
    )

#рейтинг
@dp.message(FilmForm.description)
@async_log_function_call
async def film_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    await state.set_state(FilmForm.rating)
    await message.answer(
        f"Вкажіть рейтинг фільму від 0 до 10.",
        reply_markup=None,
    )

#жанр
@dp.message(FilmForm.rating)
@async_log_function_call
async def film_rating(message: Message, state: FSMContext) -> None:
    try:
        float(message.text)
    except ValueError:
        await message.answer(
            f"Введіть число",
            reply_markup=None,
        )
        return
    await state.update_data(rating=message.text)
    await state.set_state(FilmForm.genre)
    await message.answer(
        f"Введіть жанр фільму.",
        reply_markup=None,
    )

#актори фильма
@dp.message(FilmForm.genre)
@async_log_function_call
async def film_genre(message: Message, state: FSMContext) -> None:
    await state.update_data(genre=message.text)
    await state.set_state(FilmForm.actors)
    await message.answer(
        text=f"Введіть акторів фільму через роздільник ', '\n"
        + html.bold("Обов'язкова кома та відступ після неї."),
        reply_markup=None,
    )

#постер
@dp.message(FilmForm.actors)
@async_log_function_call
async def film_actors(message: Message, state: FSMContext) -> None:
    await state.update_data(actors=[actor for actor in message.text.split(', ')])
    await state.set_state(FilmForm.poster)
    await message.answer(
        f"Введіть посилання на постер фільму.",
        reply_markup=None,
    )

#просьба проверки
@dp.message(FilmForm.poster)
@async_log_function_call
async def film_poster(message: Message, state: FSMContext) -> None:
    data = await state.update_data(poster=message.text)
    film = Film(**data)
    add_film(film.model_dump())
    await state.clear()
    await message.answer(
        f"Фільм збережено \n Натисніть /films для перегляду списку",
        reply_markup=None,
    )


class MovieStates(StatesGroup):
    search_query = State()
    filter_criteria = State()
    delete_query = State()
    edit_query = State()
    edit_description = State()


# Пошук фільму за назвою
@dp.message(FILM_SEARCH_COMMAND)
@async_log_function_call
async def search_movie(message: Message, state: FSMContext):
    await message.reply("Введіть назву фільму для пошуку:")
    await state.set_state(MovieStates.search_query)


@dp.message(MovieStates.search_query)
@async_log_function_call
async def get_search_query(message: Message, state: FSMContext):
    query = message.text.lower()
    films = get_films()
    results = [film for film in films if query in film['name'].lower()]

    if results:
        for film in results:
            await message.reply(f"Знайдено: {film['name']} - {film['description']}")
    else:
        await message.reply("Фільм не знайдено.")

    await state.clear()



# Фільтрація фільмів за жанром або роком
@dp.message(FILM_FILTER_COMMAND)
@async_log_function_call
async def filter_movies(message: Message, state: FSMContext):
    await message.reply("Введіть жанр для фільтрації:")
    await state.set_state(MovieStates.filter_criteria)


@dp.message(MovieStates.filter_criteria)
@async_log_function_call
async def get_filter_criteria(message: Message, state: FSMContext):
    films = get_films()
    criteria = message.text.lower()
    filtered = list(filter(
        lambda film: criteria in film['genre'].lower() == criteria, films
    ))

    if filtered:
        for film in filtered:
            await message.reply(f"Знайдено: {film['name']} - {film['description']}")
    else:
        await message.reply("Фільм не знайдено за цими критеріями.")

    await state.clear()


# Видалення фільму за назвою
@dp.message(FILM_DELETE_COMMAND)
@async_log_function_call
async def delete_movie(message: Message, state: FSMContext):
    await message.reply("Введіть назву фільму, який бажаєте видалити:")
    await state.set_state(MovieStates.delete_query)


@dp.message(MovieStates.delete_query)
@async_log_function_call
async def get_delete_query(message: Message, state: FSMContext):
    films = get_films()

    film_to_delete = message.text.lower()
    for film in films:
        if film_to_delete == film['name'].lower():
            delete_film(film)
            await message.reply(f"Фільм '{film['name']}' видалено.")
            await state.clear()
            return
    await message.reply("Фільм не знайдено.")
    await state.clear()


# Редагування опису фільму за назвою
@dp.message(FILM_EDIT_COMMAND)
@async_log_function_call
async def edit_movie(message: Message, state: FSMContext):
    await message.reply("Введіть назву фільму, який бажаєте редагувати:")
    await state.set_state(MovieStates.edit_query)


@dp.message(MovieStates.edit_query)
@async_log_function_call
async def get_edit_query(message: Message, state: FSMContext):
    film_to_edit = message.text.lower()
    films = get_films()

    for film in films:
        if film_to_edit == film['name'].lower():
            await state.update_data(film=film)
            await message.reply("Введіть новий опис фільму:")
            await state.set_state(MovieStates.edit_description)
            return
    await message.reply("Фільм не знайдено.")
    await state.clear()


@dp.message(MovieStates.edit_description)
@async_log_function_call
async def update_description(message: Message, state: FSMContext):
    data = await state.get_data()
    film = data['film']
    film['description'] = message.text
    edit_film(film)
    await message.reply(f"Фільм '{film['name']}' оновлено.")
    await state.clear()



#кинопоиск
@dp.message(F.text & F.text.startswith("/kinopoisk "))
async def kinopoisk_search(message: Message):
    query = message.text.replace("/kinopoisk ", "")
    data = await search_kinopoisk(query)
    
    if not data or not data.get("docs"):
        await message.reply("Фильм не найден 😢")
        return
    
    film = data["docs"][0] 
    info = (
        f"🎬 <b>{film.get('name', '?')}</b> ({film.get('year', '?')})\n"
        f"⭐ Рейтинг: {film.get('rating', {}).get('kp', '?')}/10\n"
        f"📖 Описание: {film.get('description', 'Нет данных')}"
    )
    
    if film.get("poster", {}).get("url"):
        await message.answer_photo(
            film["poster"]["url"],
            caption=info,
            reply_markup=get_kinopoisk_keyboard(film),
            parse_mode="HTML"
        )
    else:
        await message.answer(info, parse_mode="HTML")


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await bot.set_my_commands(BOT_COMMANDS)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

