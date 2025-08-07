from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData



class FilmCallback(CallbackData, prefix="films", sep=","):
    id: int
    name: str
    
    


def films_keyboard_markup(films_list:list[dict], offset:int|None = None, skip:int|None = None):
    """
    Створює клавіатуру на основі отриманого списку фільмів
    Приклад використання
    >>> await message.answer(
            text="Some text",
            reply_markup=films_keyboard_markup(films_list)
        )
    """

    # Створюємо та налаштовуємо клавіатуру
    builder = InlineKeyboardBuilder()
    builder.adjust(1, repeat=True)

    for index, film_data in enumerate(films_list):
        # Створюємо об'єкт CallbackData
        print(film_data)
        callback_data = FilmCallback(id=index, **film_data)
        # Додаємо кнопку до клавіатури
        builder.button(
            text=f"{callback_data.name}",
            callback_data=callback_data.pack()
        )
    # Повертаємо клавіатуру у вигляді InlineKeyboardMarkup
    builder.adjust(1, repeat=True)
    return builder.as_markup()


from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_kinopoisk_keyboard(film_data: dict):
    builder = InlineKeyboardBuilder()
    if film_data.get("videos", {}).get("trailers"):
        builder.button(
            text="Трейлер 🎥", 
            url=film_data["videos"]["trailers"][0]["url"]
        )
    builder.button(
        text="Подробнее на Кинопоиске", 
        url=f"https://www.kinopoisk.ru/film/{film_data.get('id')}/"
    )
    return builder.as_markup()