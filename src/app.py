from flask import Flask, request, session, jsonify, render_template
import datetime
from db import get_db, close_db

app = Flask(__name__, static_folder='templates\static')
app.teardown_appcontext(close_db)

@app.route('/')
@app.route('/index')
def index():
	""" Обработка запроса главной страницы нашего сайта объявлений """
	now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
	return render_template(
		'index.html',
		app_title='Auto Sales',
		date_time_stamp=now
	)

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
	# получаем первостепенные поля из структуры JSON запроса
	request_json = request.json
	email = request_json.get('email')
	password = request_json.get('password')
	first_name = request_json.get('first_name')
	last_name = request_json.get('last_name')
	
	# если хотя бы одно поле пусто или не определено, возвращаем код 400
	if not email or not password or not first_name or not last_name:
		return '', 400

	# создаём соединение с БД
	con = get_db()
	
	# email - является уникальным ИД пользователя при регистрации
	# означает что не может существовать 2 пользователя с одним email адресом !
	# а значит проверим, зарегистрирован ли в БД такой e-mail
	cur = con.execute(f"""
		SELECT ac.email
		FROM account as ac
		WHERE ac.email IN ('{email}')
		"""
	)
	result = cur.fetchone()
	
	# и если он уже существует, возвращаем код 409
	if result is not None:
		return '', 409

	# проверяем, отмечен ли регистрируемый пользователь как "продавец"
	if request_json.get('is_seller'):
		# и если отмечен, то получаем необходимые для "продавца" поля 
		# из структуры JSON запроса
		phone = request_json.get('phone')
		zip_code = request_json.get('zip_code')
		city_id = request_json.get('city_id')
		street = request_json.get('street')
		home = request_json.get('home')
		
		# если хотя бы одно поле пусто или не определено, возвращаем код 400
		if not phone or not zip_code or not city_id or not street or not home:
			return '', 400
			
		# регистрируем (с записью в БД) пользователя как продавца
		cur = con.execute("""
			INSERT INTO account (first_name,
								 last_name,
								 email,
								 password)
			VALUES (?, ?, ?, ?)
			""",
			(first_name, last_name, email, password)
		)
		con.commit()
		
		# получаем id зарегистрированного пользователя
		cur = con.execute(f"""
			SELECT ac.id as id
			FROM account as ac
			WHERE ac.email = '{email}'
			"""
		)
		result = cur.fetchone()['id']
		
		# регистрируем почтовый индекс и связываем с указанным ID города
		cur = con.execute("""
			INSERT OR IGNORE INTO zipcode (zip_code, city_id)
			VALUES (?, ?)
			""",
			(zip_code, city_id,)
		)
		con.commit()
		
		# добавляем нового продавца и привязываем его к аккаунту пользователя
		cur = con.execute("""
			INSERT INTO seller (zip_code, street, home, phone, account_id)
			VALUES (?, ?, ?, ?, ?)
			""",
			(zip_code, street, home, phone, int(result))
		)
		con.commit()
		
		# если успех, возвращаем ответ в виде JSON объекта
		cur = con.execute(f"""
			SELECT ac.id, ac.first_name, ac.last_name, ac.email, ac.password,
				   slr.zip_code, slr.street, slr.home, slr.phone,
				   zc.city_id
			FROM account as ac
				JOIN seller as slr ON slr.account_id = ac.id
				JOIN zipcode as zc ON zc.zip_code = slr.zip_code
			WHERE ac.email = '{email}'
			"""
		)
		result = cur.fetchall()
		
		result = [dict(row) for row in result]
		result = result[0]
		result['is_seller'] = 'true'
		
		return jsonify([result])
	else:
		# иначе, регистрируем (с записью в БД) простого пользователя
		cur = con.execute("""
			INSERT INTO account (first_name,
								 last_name,
								 email,
								 password)
			VALUES (?, ?, ?, ?)
			""",
			(first_name, last_name, email, password)
		)
		con.commit()
		
		# если успех, возвращаем ответ в виде JSON объекта
		cur = con.execute(f"""
			SELECT *
			FROM account as ac
			WHERE ac.email = '{email}'
			"""
		)
		result = cur.fetchall()
		
		result = [dict(row) for row in result]
		result = result[0]
		result['is_seller'] = 'false'
		
		return jsonify([result])

@app.route('/users/<int:id>', methods=["GET", "PATCH"])
def users_id():
	""" Обработка получения сведений о пользователе по его ID
		Обработка частичного редактирования сведений о пользователе по его ID
	"""
	# if request.method=='GET':
		# con = get_db()
		# cur = con.execute("""
			# SELECT *
			# FROM account
			# WHERE account.id = 1
			# """
		# )
		# result = cur.fetchone()
		
		# return jsonify([dict(row) for row in result])

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
	# получаем список всех объявлений
	if request.method=='GET':
		con = get_db()
		cur = con.execute("""
			SELECT * 
			FROM ad
			"""
		)
		result = cur.fetchall()
		
		return jsonify([dict(row) for row in result])

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
	# при GET запросе выдадим JSON список городов
	if request.method=='GET':
		con = get_db()
		cur = con.execute("""
			SELECT *
			FROM city
			"""
		)
		result = cur.fetchall()

		return jsonify([dict(row) for row in result])
	
	# при POST запросе добавим новый город, если он не существует,
	# иначе вернём его
	if request.method=='POST':
		# получаем поле name из структуры JSON запроса c именем города
		request_json = request.json
		name = request_json.get('name')
		
		# если поле name не определено, возвращаем код 400
		if not name:
			return '', 400
		
		# создаём соединение с БД
		con = get_db()
		
		# проверяем, существует ли такой город в БД
		cur = con.execute(f"""
			SELECT *
			FROM city as c
			WHERE c.name = '{name}'
			"""
		)
		result = cur.fetchall()

		# если город отсутствует в БД, добавляем его
		if not result:
			cur = con.execute("""
				INSERT INTO city (name)
				VALUES (?)
				""",
				(name,)
			)
			con.commit()

			cur = con.execute(f"""
				SELECT *
				FROM city as c
				WHERE c.name = '{name}'
				"""
			)
			result = cur.fetchall()
		
		return jsonify([dict(row) for row in result])

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
	