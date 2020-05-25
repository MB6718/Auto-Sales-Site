from flask import Flask, request, session, jsonify
from db import get_db, close_db

app = Flask(__name__) 
app.teardown_appcontext(close_db)

@app.route('/')
@app.route('/index')
def index():
	""" Обработка запроса главной страницы нашего сайта объявлений """
	return '', 200

@app.route('/auth/login', methods=["POST"])
def login():
	""" Обработка авторизации на сайте"""
	pass

@app.route('/auth/logout', methods=["POST"])
def logout():
	""" Обработка выхода из авторизации"""
	pass

@app.route('/users', methods=["POST"])
def users():
	""" Обработка регистрации нового пользователя"""
	pass

@app.route('/users/<int:id>', methods=["GET", "PATCH"])
def users_id():
	""" Обработка получения сведений о пользователе по его ID
		Обработка частичного редактирования сведений о пользователе по его ID
	"""
	pass

@app.route('/users/<int:id>/ads', methods=["GET", "POST"])
def users_ads():
	""" Обработка получения всех объявлений пользователя по его ID
		Обработка добавления нового объявления от пользователя
	"""
	pass

@app.route('/ads', methods=["GET", "POST"])
def ads():
	""" Обработка получения всех объявлений
		Обработка добавления нового объявления на сайт
	"""
	pass

@app.route('/ads/<int:id>', methods=["GET", "DELETE", "PATCH"])
def ads_id():
	""" Обработка получения объявления по его ID
		Обработка удаления объявления с сайта по его ID
		Обработка частичного редактирования объявления по его ID
	"""
	pass

@app.route('/cities', methods=["GET", "POST"])
def cities():
	""" Обработка получения списка всех городов из БД
		Обработка добавления в БД нового города
	"""
	pass

@app.route('/colors', methods=["GET", "POST"])
def colors():
	""" Обработка получения списка всех цветов из БД
		Обработка добавления в БД нового цвета
	"""
	pass

@app.route('/images', methods=["POST"])
def images():
	""" Обработка добавления в БД URL ссылки на изображение """
	pass

@app.route('/images/<name>')
def get_image():
	""" Обработка получения ссылки из БД на изображение по его имени """
	pass
	