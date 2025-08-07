import json


def get_films(file_path: str = "film.json", film_id: int | None = None) -> list[dict] | dict:
    with open(file_path, 'r') as fp:
        films = json.load(fp)
        if film_id != None and film_id < len(films):
            return films[film_id]
        return films


def add_film(
   film: dict,
   file_path: str = "film.json",
):
   films = get_films(file_path=file_path, film_id=None)
   if films:
       films.append(film)
       with open(file_path, "w") as fp:
           json.dump(
               films,
               fp,
               indent=4,
               ensure_ascii=False,
           )
           

def delete_film(
    film_to_delete: dict,
    file_path: str = "film.json",

):
    films = get_films(file_path=file_path, film_id=None)
    for film in films:
        if film_to_delete["name"]==film["name"]:
            films.remove(film)
    with open(file_path, "w") as fp:
        json.dump(
            films,
            fp,
            indent=4,
            ensure_ascii=False,
        )



def edit_film(
    film_to_edit: dict,
    file_path: str = "film.json",

):
    films = get_films(file_path=file_path, film_id=None)
    for i, film in enumerate(films):
        if film_to_edit["name"]==film["name"]:
            films[i] = film_to_edit
    with open(file_path, "w") as fp:
        json.dump(
            films,
            fp,
            indent=4,
            ensure_ascii=False,
        )