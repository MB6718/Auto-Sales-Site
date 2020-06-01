# Auto Sales Site

![Auto-Sales-Site](logo/as-beta-logo.png)

[![version](https://img.shields.io/badge/Version-v0.1-BrightGreen)](https://github.com/MB6718/Auto-Sales-Site/)
[![python-version](https://img.shields.io/badge/Python-v3.8-blue)](https://www.python.org/downloads/release/python-383rc1/)
[![platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-LightGray)](https://ru.wikipedia.org/wiki/%D0%9A%D1%80%D0%BE%D1%81%D1%81%D0%BF%D0%BB%D0%B0%D1%82%D1%84%D0%BE%D1%80%D0%BC%D0%B5%D0%BD%D0%BD%D0%BE%D1%81%D1%82%D1%8C)
[![license](https://img.shields.io/badge/license-GPL_v3.0-yellow)](https://github.com/MB6718/Auto-Sales-Site/blob/master/LICENSE)
[![framework](https://img.shields.io/badge/framework-Flask_1.1.12-ff69b4)](https://flask.palletsprojects.com/en/1.1.x/)

### Содержание
* [Краткое описание](#description)
* [Подготовка к запуску](#firstrun)
* [Формат описания API запросов/ответов](#apiformat)
	* [POST /auth/login](#login)
	* [POST /auth/logout](#logout)
	* [POST /users](#users)
	* [GET /users/&lt;id&gt;](#get_users_id)
	* [PATCH /users/&lt;id&gt;](#patch_users_id)
	* [GET /ads](#get_ads)
	* [GET /users/&lt;id&gt;/ads](#get_users_ads)
	* [POST /ads](#post_ads)
	* [POST /users/&lt;id&gt;/ads](#post_users_ads)
	* [GET /ads/&lt;id&gt;](#get_ads_id)
	* [PATCH /ads/&lt;id&gt;](#patch_ads_id)
	* [DELETE /ads/&lt;id&gt;](#delete_ads_id)
	* [GET /cities](#get_cities)
	* [POST /cities](#post_cities)
	* [GET /colors](#get_colors)
	* [POST /colors](#post_colors)
	* [POST /images](#post_images)
	* [GET /images/&lt;name&gt;](#get_images)
* [Примеры API запросов](#example)
* [Лицензия](#license)

### Краткое описание <a name="description"></a>
Данное приложение Auto Sales Site, (REST API) сервис по продаже автомобилей, а точнее его серверная часть.

Приложение реализовано с помощью web-фреймворка Flask.

### Подготовка и запуск <a name="firstrun"></a>
Пошаговая инструкция по запуску приложения на локальном компьютере:
1. Скачать архив с релизом приложения и распаковать в любую удобную папку
2. В корне проекта создать файл .env, содержащий четыре строки:
    ```bash
    PYTHONPATH=src # путь к исходнику проекта
    DB_FILE=database.db # путь к файлу бзы данных SQLite
    SECRET_KEY=1234567890 # секретный ключь (!) заменить на свой
	UPLOAD_FOLDER=uploads # имя папки для загружаемых на сервер файлов
    ```
3. создать и запустить виртуальное окружение в корне проекта, подтянуть необходимые зависимости
    ```bash
    python -m venv .venv # создаём виртуальное окружение
    .venv\Scripts\activate.bat # активируем виртуальное окружение
    (.venv) python -V # проверяем версию интерпретатора Python, убеждаясь в работе окружения
    (.venv) pip install -r requirements.txt # устанавливаем необходимые пакеты и формируем зависимости
    (.venv) flask run # запустим локальный сервер Flask
    ```
4. в браузере проверим работоспособность приложения, зайдя на локальный адрес:
    ```bash
    http://localhost:5000/
    ```
5. Если виден логотип проекта, можно приступать к тестированию API функционала приложения

### Формат описания API запросов/ответов: <a name="apiformat"></a>
* запросы и ответы представлены в JSON-подобной структуре и описывают JSON-документы
* через двоеточие указываются типы полей
* запись вида type? обозначает, что поле необязательное и может отсутствовать
* запись вида [type] обозначает список значений типа type

<a name="login"></a> 
&#9660; Авторизация: вход и выход.  

**POST** &rArr; `/auth/login`  
Request:
```json
{
  "email": str,
  "password": str
}
```
<a name="logout"></a>
**POST** &rArr; `/auth/logout`
  
<a name="users"></a>
&#9660; Регистрация пользователя. Поле is_seller показывает, является ли пользователь продавцом. Поля phone, zip_code, city_id, street, home указываются, только если пользователь является продавцом.  

**POST** &rArr; `/users`  
Request:
```json
{
  "email": str,
  "password": str,
  "first_name": str,
  "last_name": str,
  "is_seller": bool,
  "phone": str?,
  "zip_code": int?,
  "city_id": int?,
  "street": str?,
  "home": str?
}
```
Response:
```json
{
  "id": int,
  "email": str,
  "first_name": str,
  "last_name": str,
  "is_seller": bool,
  "phone": str?,
  "zip_code": int?,
  "city_id": int?,
  "street": str?,
  "home": str?
}
```

<a name="get_users_id"></a>
&#9660; Получение пользователя. Доступно только авторизованным пользователям.

**GET** &rArr; `/users/<id>`  
Response:
```json
{
  "id": int,
  "email": str,
  "first_name": str,
  "last_name": str,
  "is_seller": bool,
  "phone": str?,
  "zip_code": int?,
  "city_id": int?,
  "street": str?,
  "home": str?
}
```
<a name="patch_users_id"></a>
&#9660; Частичное редактирование пользователя. Доступно только текущему авторизованному пользователю. Поля phone, zip_code, city_id, street, home указываются, только если пользователь является продавцом. При установке флага is_seller в false должно происходить удаление сущностей продавца.

**PATCH** &rArr; `/users/<id>`  
Request:
```json
{
  "first_name": str?,
  "last_name": str?,
  "is_seller": bool?,
  "phone": str?,
  "zip_code": int?,
  "city_id": int?,
  "street": str?,
  "home": str?
}
```
Response:
```json
{
  "id": int,
  "email": str,
  "first_name": str,
  "last_name": str,
  "is_seller": bool,
  "phone": str?,
  "zip_code": int?,
  "city_id": int?,
  "street": str?,
  "home": str?
}
```

<a name="get_ads"></a> <a name="get_users_ads"></a>
&#9660; Получение списка объявлений: всех и принадлежащих пользователю. Список можно фильтровать с помощью query string параметров, все параметры необязательные.

**GET** &rArr; `/ads`  
**GET** &rArr; `/users/<id>/ads`  
Query string:
```
  seller_id: int?
  tags: str?
  make: str?
  model: str?
```
Response:
```json
[
  {
    "id": int,
    "seller_id": int,
    "title": str,
    "date": str,
    "tags:": [str], // Список тегов строками
    "car": {
      "make": str,
      "model": str,
      "colors": [
        {
          "id": int,
          "name": str,
          "hex": str
        }
      ],
      "mileage": int,
      "num_owners": int,
      "reg_number": str,
      "images": [
        {
          "title": str,
          "url": str
        }
      ]
    }
  }
]
```
<a name="post_ads"></a> <a name="post_users_ads"></a>
&#9660; Публикация объявления. Доступно только авторизованным пользователям. Доступно только если пользователь является продавцом.

**POST** &rArr; `/ads`  
**POST** &rArr; `/users/<id>/ads`  
Request:
```json
{
  "title": str,
  "tags": [str, ...], // Список тегов строками
  "car": {
    "make": str,
    "model": str,
    "colors": [int], // Список ID цветов
    "mileage": int,
    "num_owners": int?,
    "reg_number": str,
    "images": [
      {
        "title": str,
        "url": str
      }
    ]
  }
}
```
Response:
```json
[
  {

    "id": int,
    "seller_id": int,
    "title": str,
    "date": str,
    "tags:": [str], // Список тегов строками
    "car": {
      "make": str,
      "model": str,
      "colors": [
        {
          "id": int,
          "name": str,
          "hex": str
        }
      ],
      "mileage": int,
      "num_owners": int,
      "reg_number": str,
      "images": [
        {
          "title": str,
          "url": str
        }
      ]
    }
  }
]
```
<a name="get_ads_id"></a>
&#9660; Получение объявления.

**GET** &rArr; `/ads/<id>`  
Response:
```json
{
  "id": int,
  "seller_id": int,
  "title": str,
  "date": str,
  "tags:": [str], // Список тегов строками
  "car": {
    "make": str,
    "model": str,
    "colors": [
      {
        "id": int,
        "name": str,
        "hex": str
      }
    ],
    "mileage": int,
    "num_owners": int,
    "reg_number": str,
    "images": [
      {
        "title": str,
        "url": str
      }
    ]
  }
}
```
<a name="patch_ads_id"></a>
&#9660; Частичное редактирование объявления. Доступно только авторизованным пользователям. Может совершать только владелец объявления.

**PATCH** &rArr; `/ads/<id>`  
Request:
```json
{
  "title": str?,
  "tags": [str]?, // Список тегов строками
  "car": {
    "make": str?,
    "model": str?,
    "colors": [int]?, // Список ID цветов
    "mileage": int?,
    "num_owners": int?,
    "reg_number": str?,
    "images": [
      {
        "title": str,
        "url": str
      }
    ]?
  }
}
```

<a name="delete_ads_id"></a>
&#9660; Удаление объявления. Доступно только авторизованным пользователям. Может совершать только владелец объявления.

**DELETE** &rArr; `/ads/<id>`

<a name="get_cities"></a>
&#9660; Получение списка городов.

**GET** &rArr; `/cities`  
Response:
```json
[
  {
    "id": int,
    "name": str
  }
]
```

<a name="post_cities"></a>
&#9660; Создание города. При попытке создать уже существующий город (проверка по названию), должен возвращаться существующий объект.

**POST** &rArr; `/cities`  
Request:
```json
{
  "name": str
}
```
Response:
```json
{
  "id": int,
  "name": str
}
```

<a name="get_colors"></a>
&#9660; Получение списка цветов. Доступно только авторизованным пользователям. Доступно только если пользователь является продавцом.

**GET** &rArr; `/colors`  
Response:
```json
[
  {
    "id": int,
    "name": str,
    "hex": str
  }
]
```

<a name="post_colors"></a>
&#9660; Создание цвета. Доступно только авторизованным пользователям. Доступно только если пользователь является продавцом. При попытке создать уже существующий цвет (проверка по названию), должен возвращаться существующий объект.

**POST** &rArr; `/colors`  
Request:
```json
{
  "name": str,
  "hex": str
}
```
Response:
```json
{
  "id": int,
  "name": str,
  "hex": str
}
```

<a name="post_images"></a>
&#9660; Загрузка изображения. Доступно только авторизованным пользователям. Доступно только если пользователь является продавцом.

**POST** &rArr; `/images`  
Request:
```
файл изображения в поле формы file
```
Response:
```json
{
  "url": str
}
```

<a name="get_images"></a>
&#9660; Получение изображения.

**GET** &rArr; `/images/<name>`  
Response:
```
файл изображения
```

### Примеры API запросов <a name="example"></a>

&#9660; Регистрация пользователя и авторизация:

**POST** &rArr; `/users`
```json
{
  "email": "johndoe@example.com",
  "password": "password",
  "first_name": "John",
  "last_name": "Doe",
  "is_seller": false
}
```
**POST** &rArr; `/auth/login`
```json
{
  "email": "johndoe@example.com",
  "password": "password"
}
```
**GET** &rArr; `/users/<id нового пользователя>`

&#9660; Регистрация продавца, авторизация, создание объявления и необходимых сущностей.

**POST** &rArr; `/cities`
```json
{
  "name": "Москва"
}
```

**POST** &rArr; `/users`
```json
{
  "email": "janedoe@example.com",
  "password": "password",
  "first_name": "Jane",
  "last_name": "Doe",
  "is_seller": true,
  "phone": "+75551112233",
  "zip_code": 555123,
  "city_id": <id города>,
  "street": "Пушкина",
  "home": 42
}
```

**POST** &rArr; `/auth/login`
```json
{
  "email": "janedoe@example.com",
  "password": "password"
}
```

**POST** &rArr; `/colors`
```json
{
  "name": "red",
  "hex": "ff1122"
}
```

**POST** &rArr; `/images`  
```фото1```

**POST** &rArr; `/images`  
```фото2```

**POST** &rArr; `/ads`
```json
{
  "title": "Продам жигуль",
  "tags": ["жигуль", "ваз", "таз", "машинамечты"],
  "car": {
    "make": "ВАЗ",
    "model": "2101",
    "colors": [<id цвета>],
    "mileage": 200000,
    "num_owners": 7,
    "reg_number": "В666АЗ",
    "images": [
      {"title": "Перед", "url": "<url фото1>"},
      {"title": "Зад", "url": "<url фото2>"}
    ]
  }
}
```
**GET** &rArr; `/ads/<id объявления>`

### Лицензия <a name="license"></a>

Auto Sales Site распространяется под лицензией GNU GPL v3.0. Смотрите LICENSE.md для получения более полных сведений.

&copy; 2020 MB6718