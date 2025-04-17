# Foodgram - Продуктовый помощник

Foodgram - это веб-приложение для публикации рецептов, создания списков покупок и подписки на любимых авторов.
Адрес сайта - https://kattygram.duckdns.org

## Основные возможности

- Создание и публикация рецептов
- Добавление рецептов в избранное
- Создание списка покупок
- Подписка на авторов
- Фильтрация рецептов по тегам и другим параметрам
- Поиск ингредиентов

## Технологии

### Backend

- Python 3.9
- Django 3.2
- Django REST Framework
- PostgreSQL
- Docker
- Nginx
- Gunicorn

### Frontend

- React
- Redux
- TypeScript

## Установка и запуск проекта

### Требования

- Docker
- Docker Compose

### Локальный запуск

1. Клонируйте репозиторий:

```bash
git clone https://github.com/kateschka/foodgram.git
cd foodgram
```

2. Создайте файл `.env` в директории `backend/` со следующими переменными:

```
DB_ENGINE
DB_NAME
POSTGRES_USER
POSTGRES_PASSWORD
DB_HOST
DB_PORT
SECRET_KEY
```

3. Запустите контейнеры:

```bash
cd infra/
docker-compose up -d
```

4. Выполните миграции:

```bash
docker-compose exec backend python manage.py migrate
```

5. Создайте суперпользователя:

```bash
docker-compose exec backend python manage.py createsuperuser
```

6. Соберите статические файлы:

```bash
docker-compose exec backend python manage.py collectstatic --no-input
```

7. Заполните базу данных начальными данными:

```bash
docker-compose exec backend python manage.py load_ingredients_from_csv
```

После выполнения этих шагов проект будет доступен по адресу:

- Backend: http://localhost/api/
- Frontend: http://localhost/
- Админ-панель: http://localhost/admin/
- Документация: http://localhost/api/docs/

## API Endpoints

### Рецепты

- `GET /api/recipes/` - список рецептов
- `GET /api/recipes/{id}/` - детали рецепта
- `POST /api/recipes/` - создание рецепта
- `PATCH /api/recipes/{id}/` - обновление рецепта
- `DELETE /api/recipes/{id}/` - удаление рецепта

### Теги

- `GET /api/tags/` - список тегов
- `GET /api/tags/{id}/` - детали тега

### Ингредиенты

- `GET /api/ingredients/` - список ингредиентов
- `GET /api/ingredients/{id}/` - детали ингредиента

### Пользователи

- `GET /api/users/` - список пользователей
- `GET /api/users/{id}/` - профиль пользователя
- `POST /api/users/` - регистрация
- `GET /api/users/me/` - текущий пользователь
- `POST /api/users/set_password/` - смена пароля

### Подписки

- `GET /api/users/subscriptions/` - список подписок
- `POST /api/users/{id}/subscribe/` - подписка на пользователя
- `DELETE /api/users/{id}/subscribe/` - отписка от пользователя

### Избранное

- `POST /api/recipes/{id}/favorite/` - добавление в избранное
- `DELETE /api/recipes/{id}/favorite/` - удаление из избранного

### Список покупок

- `GET /api/recipes/download_shopping_cart/` - скачать список покупок
- `POST /api/recipes/{id}/shopping_cart/` - добавление в список покупок
- `DELETE /api/recipes/{id}/shopping_cart/` - удаление из списка покупок
