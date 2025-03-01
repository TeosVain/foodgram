# FoodGram

**FoodGram** — это проект на базе Django с фронтендом на JavaScript, это социальная сеть помогающая людям делиться и находить рецепты. На сайте вы можете создать аккаунт, выкладывать свои рецепты, подписываться на других пользователей. Рецепты можно добавить в избраное или в список покупок. В любой момент можно скачать списко покупок, где будут перечислены все необходимые ингредиенты.

Проект контейнеризован с помощью Docker и управляется через `docker-compose`. В качестве прокси-сервера используется Nginx, backend работает под управлением gunicorn, а база данных реализована на Postgres. Все контейнеры работают через единый gateway на сервере, где настроен порт **8000** для доступа к сайту.

## Особенности проекта

- **Функциональность:**
  - Регистрация и авторизация пользователей.
  - Загрузка рецептов с описанием и картинками.
  - Возможность подписки на пользователей.
  - Возможность скачать список покупок.
  
- **Микросервисная архитектура контейнеров:**
  - **backend** — Django-приложение, запускаемое с помощью gunicorn.
  - **frontend** — клиентская часть на JavaScript.
  - **db** — база данных Postgres.
  - **nginx** — Nginx, выполняющий роль обратного прокси и перенаправляющий запросы на порт **8000**.

- **Docker Volumes:**  
  Для сохранения данных созданы volume:
  - **media** — для загруженных пользователями файлов.
  - **static** — для собранных статических ресурсов.
  - **pg_data** — для хранения данных базы данных.

- **CI/CD с GitHub Actions:**  
  Автоматизация тестирования, сборки и деплоя:
  - Автоматический запуск тестов при каждом коммите.
  - Сборка и перезапись Docker-образов на DockerHub.
  - Подключение к удалённому серверу, где сайт перезапускается после обновления.
  
- **Конфигурация через переменные окружения:**  
  На удалённом сервере для работы проекта необходим файл `.env`, который создаётся на основе файла `env.example` из репозитория. Для автоматизации деплоя настроены секреты в GitHub с вашими личными данными (например, SSH-ключи, учетные данные DockerHub и т.д.).

## Требования

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Аккаунт на [DockerHub](https://hub.docker.com/)
- Аккаунт на [GitHub](https://github.com/) (для работы с GitHub Actions)
- Удалённый сервер с настроенным доступом через порт **9000** для деплоя проекта

## Установка и запуск

1. **Клонируйте репозиторий:**
```
   git clone https://github.com/yourusername/foodgram.git
   cd foodgram
```
2.	Создайте файл .env на удалённом сервере:
На сервере, где будет работать проект, создайте файл .env на основе env.example:
```
cp env.example .env
```
Отредактируйте файл, указав необходимые переменные окружения (например, настройки базы данных, секретные ключи и т.д.).

3.	Запустите контейнеры:
Используя docker-compose, запустите все сервисы в фоне:
docker-compose up -d
Контейнеры будут автоматически созданы и запущены:
-	backend — Django с gunicorn.
-	frontend — сборка и запуск JS-приложения.
-	db — Postgres база данных.
-	nginx — Nginx, обеспечивающий работу в качестве прокси на порту 9000.

Тестирование и деплой с помощью GitHub Actions
В проекте настроены GitHub Actions для автоматической интеграции и доставки:
-	Тестирование:
При каждом коммите запускаются тесты для проверки корректности работы приложения.
- Сборка Docker образов:
После успешного прохождения тестов образы собираются и перезаписываются на DockerHub.
-	Деплой:
GitHub Actions подключается к удалённому серверу, где обновлённый образ разворачивается, а сайт перезапускается.
Важно: Перед деплоем убедитесь, что в настройках репозитория GitHub корректно настроены секреты (SSH ключи, учетные данные DockerHub и другие переменные).

## Заключение

Проект FoodGram предоставляет готовую инфраструктуру для разработки, тестирования и деплоя Django-приложения с современным стеком технологий. Благодаря использованию Docker, Nginx, gunicorn и GitHub Actions, процесс развертывания автоматизирован и масштабируем. Следуйте инструкциям выше для быстрой установки и настройки проекта, и не забудьте корректно настроить переменные окружения и секреты для успешного деплоя на сервере, где приложение будет доступно через порт 8000.

## Автор
TeosVain