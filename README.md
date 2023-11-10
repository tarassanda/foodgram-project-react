
## Описание проекта:

Проект foodgram - это сервис для просмотра, добавления и редактирования рецептов различных блюд. С помощью foodgram можно изучать рецепты, ингредиенты, время приготовления, и конечно же фотографии блюд. foodgram - это учебный дипломный проект курса "backend-python" от Яндекс-Практикума.


### Как запустить проект:

1.  Клонировать репозиторий и перейти в него в командной строке:
    
    -   git clone git@github.com:tarassanda/foodgram-project-react.git
    -   cd foodgram/backend
2.  Cоздать и активировать виртуальное окружение:
    
    -   python3 -m venv venv
    -   source venv/bin/activate

для windows систем: - python -m venv venv - source/Scripts/activate

3.  Обновить pip:
    -   python3 -m pip install --upgrade pip

для windows систем: - python -m pip install --upgrade pip

4.  установить зависимости из файла requirements.txt
    
    -   pip install -r requirements.txt
5.  Выполнить миграции:
    
    -   python3 manage.py migrate

для windows систем: - python manage.py migrate

6.  Запустить проект:
    -   python3 manage.py runserver

для windows систем: - python manage.py runserver

### Основные доступные эндпоинты:

1.  https://foodgram-tarassanda.ddns.net :
    -   Главная страница проекта 
2.  https://foodgram-tarassanda.ddns.net/signin :
    -   Регистрация и вход

3.  https://foodgram-tarassanda.ddns.net/recipes/1 :
    -   Информация о рецепте

4.  https://foodgram-tarassanda.ddns.net/admin/ :
    -   Страница администрирования проекта

5.  https://foodgram-tarassanda.ddns.net/api/ :
    -   Информация об api
