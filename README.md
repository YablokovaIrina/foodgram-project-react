# Foodgram

![example workflow](https://github.com/YablokovaIrina/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

## Продуктовый помошник
Foodgram, «Продуктовый помощник». Онлайн-сервис и API для него. На этом сервисе пользователи публикуют свои рецепты, подписываются на публикации других пользователей, добавляют понравившиеся рецепты в список «Избранное», а перед походом в магазин могут скачать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

Регистрация и авторизация реализованы с использованием authtoken. 

Проект упакован в три docker-контейнера.

Фронтенд реализован с использованием React.js
## Технологии:
- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org)
- [Docker](https://www.docker.com)
- [Docker-compose](https://docs.docker.com/compose/)
- [PosgreSQL](https://www.postgresql.org)
- [Nginx](https://nginx.org/)
- [Gunicorn](https://gunicorn.org)

## Установка и развертывание проекта:
- Клонировать репозиторий
- Создать виртуальное окружение и установить зависимости из requirements.txt
- Установить Docker и docker-compose
- Забилдить и поднять проект:
```
$ docker-compose up -d --build 
```
- Выполнить команды для миграции, создания суперюзера и сбора статики:
```
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input
```
- Загрузить список ингредиентов из csv файла:
```
docker-compose exec web python manage.py upload
```
Готово! Вы потрясающие!

### Пример наполнения env файла
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres (your password)
DB_HOST=db
DB_PORT=5432
```

### Foodgram развернут по адресу
http://158.160.25.151/recipes

### Для доступа в админку:
irishkarusakova@icloud.com
1234567890

### Authors
Яблокова Ирина
