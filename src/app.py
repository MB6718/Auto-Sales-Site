from flask import (
	Flask,
	request,
	session,
	jsonify,
	render_template
)

import datetime

from db import (
	get_db,
	close_db
)

from werkzeug.security import (
	generate_password_hash,
	check_password_hash
)

app = Flask(__name__, static_folder='templates\static')
#app.teardown_appcontext(close_db)
app.secret_key = '1234567890'

# ##############################################################################
# ### [/]
# ### [/index]
# ##############################################################################
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

# ##############################################################################
# ### [/auth/login]
# ##############################################################################
@app.route('/auth/login', methods=["POST"])
def login():
	""" Обработка авторизации на сайте"""
	# получаем поля email(логин) и password(пароль) из структуры JSON запроса
	request_json = request.json
	email = request_json.get('email')
	password = request_json.get('password')
	
	# если хотя бы одно поле пусто или не определено, возвращаем код 400
	if not email or not password :
		return '', 400
	
	# создаём соединение с БД
	con = get_db()
	
	# получаем пользователя из БД 
	cur = con.execute("""
		SELECT *
		FROM account
		WHERE email = ?
		""",
		(email,)
	)
	user = cur.fetchone()
	
	# если пользователь не найден в БД, возвращаем код 403
	if user is None:
		return '', 403
	
	# если пароль пользователя введён не корректный, возвращаем код 403
	if user['password'] != password:
		return '', 403
	
	# открываем сессию
	session['user_id'] = user['id']
	return '', 200

# ##############################################################################
# ### [/auth/logout]
# ##############################################################################
@app.route('/auth/logout', methods=["POST"])
def logout():
	""" Обработка выхода из авторизации"""
	# прекращаем сессию
	session.pop('user_id', None)
	return '', 200

# ##############################################################################
# ### [/users]
# ##############################################################################
@app.route('/users', methods=["POST"])
def users():
	""" Обработка регистрации нового пользователя"""
	# получаем первостепенные поля из структуры JSON запроса
	request_json = request.json
	is_seller = request_json.get('is_seller')
	email = request_json.get('email')
	password = request_json.get('password')
	first_name = request_json.get('first_name')
	last_name = request_json.get('last_name')
	
	# если хотя бы одно поле пусто или не определено, возвращаем код 400
	if not email or not password or not first_name or not last_name or \
		not is_seller:
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
	if is_seller:
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
		cur = con.execute("""
			SELECT ac.id as id
			FROM account as ac
			WHERE ac.email = ?
			""",
			(email,)
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
		cur = con.execute("""
			SELECT ac.id, ac.first_name, ac.last_name, ac.email, ac.password,
				   slr.zip_code, slr.street, slr.home, slr.phone,
				   zc.city_id
			FROM account as ac
				JOIN seller as slr ON slr.account_id = ac.id
				JOIN zipcode as zc ON zc.zip_code = slr.zip_code
			WHERE ac.email = ?
			""",
			(email,)
		)
		result = cur.fetchall()
		
		result = [dict(row) for row in result]
		result = result[0]
		result['is_seller'] = 'true'
		
		return jsonify(result), 201
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
		cur = con.execute("""
			SELECT *
			FROM account as ac
			WHERE ac.email = ?
			""",
			(email,)
		)
		result = cur.fetchall()
		
		result = [dict(row) for row in result]
		result = result[0]
		result['is_seller'] = 'false'
		
		return jsonify(result), 201

# ##############################################################################
# ### [/users/<id>]
# ##############################################################################
@app.route('/users/<int:id>', methods=["GET", "PATCH"])
def users_id(id):
	""" Обработка получения сведений о пользователе по его ID
		Обработка частичного редактирования сведений о пользователе по его ID
	"""
	# получаем user_id из текущей сессии
	user_id = session.get('user_id')
	# если, user_id не существует, значит сессия не создана, возвращаем код 403
	if user_id is None:
		return '', 403	
	
	# создаём соединение с БД
	con = get_db()

	# проверяем в БД, является ли выбранный пользователь продавцом
	cur = con.execute("""
		SELECT *
		FROM account as ac
			JOIN seller as slr ON slr.account_id = ac.id
		WHERE ac.id = ?
		""",
		(id,)
	)
	is_seller = cur.fetchall()
	
	# при GET запросе выдадим JSON объект пользователя по его ID
	if request.method == 'GET':
		if is_seller:
			# если является, то выводим полную информацию
			cur = con.execute("""
				SELECT ac.id, ac.first_name, ac.last_name, ac.email, ac.password,
					   slr.zip_code, slr.street, slr.home, slr.phone,
					   zc.city_id
				FROM account as ac
					JOIN seller as slr ON slr.account_id = ac.id
					JOIN zipcode as zc ON zc.zip_code = slr.zip_code
				WHERE ac.id = ?
				""",
				(id,)
			)
			result = cur.fetchall()
			
			result = [dict(row) for row in result]
			result = result[0]
			result['is_seller'] = 'true'
		else:
			# иначе, выводим основную информацию
			cur = con.execute("""
				SELECT *
				FROM account
				WHERE account.id = ?
				""",
				(id,)
			)
			result = cur.fetchall()
		
			result = [dict(row) for row in result]
			result = result[0]
			result['is_seller'] = 'false'
		return jsonify(result)
	
	# при PATCH запросе редактируем пользователя по его ID
	if request.method == 'PATCH':
		# проверим, может ли текущий авторизованный пользователь
		# редактировать информацию аккаунта под этим ID
		if user_id == id:
			if is_seller:
				pass

				# # проверим, отмечен ли пользователь продавцом в JSON запросе
				# if request_json.get('is_seller'):
					# # и если отмечен, то получаем необходимые для "продавца" поля 
					# # из структуры JSON запроса
					# phone = request_json.get('phone')
					# zip_code = request_json.get('zip_code')
					# city_id = request_json.get('city_id')
					# street = request_json.get('street')
					# home = request_json.get('home')
				# else:
					# # иначе, получаем основные поля из структуры JSON запроса
					# request_json = request.json
					# email = request_json.get('email')
					# password = request_json.get('password')
					# first_name = request_json.get('first_name')
					# last_name = request_json.get('last_name')
				
			else:
				pass
			return 'OK', 200
		else:
			return '', 401

# ##############################################################################
# ### [/users/<id>/ads]
# ##############################################################################
@app.route('/users/<int:id>/ads', methods=["GET", "POST"])
def users_ads(id):
	""" Обработка получения всех объявлений пользователя по его ID
		Обработка добавления нового объявления от пользователя
	"""
	# при GET запросе выводим JSON список объявлений пользователя по его ID
	if request.method == 'GET':
		pass
	
	# при POST запросе регистрируем новое объявление пользователя по его ID
	if request.method == 'POST':
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		# если, user_id не существует, значит сессия не создана, возвращаем код 403		
		if user_id == id:
			return 'OK', 200
		else:
			return '', 401

# ##############################################################################
# ### [/ads]
# ##############################################################################
@app.route('/ads', methods=["GET", "POST"])
def ads():
	""" Обработка получения всех объявлений
		Обработка добавления нового объявления на сайт
	"""
	# при GET запросе получаем JSON список всех объявлений
	if request.method == 'GET':
		con = get_db()
		cur = con.execute("""
			SELECT * 
			FROM ad
			"""
		)
		result = cur.fetchall()
		
		return jsonify([dict(row) for row in result])
	
	# при POST запросе 
	if request.method == 'POST':
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		# если, user_id не существует, значит сессия не создана, возвращаем код 403
		if user_id is None:
			return '', 403		
		
		return 'OK', 200

# ##############################################################################
# ### [/ads/<id>]
# ##############################################################################
@app.route('/ads/<int:id>', methods=["GET", "DELETE", "PATCH"])
def ads_id(id):
	""" Обработка получения объявления по его ID
		Обработка удаления объявления с сайта по его ID
		Обработка частичного редактирования объявления по его ID
	"""
	pass

# ##############################################################################
# ### [/cities]
# ##############################################################################
@app.route('/cities', methods=["GET", "POST"])
def cities():
	""" Обработка получения списка всех городов из БД
		Обработка добавления в БД нового города
	"""
	# создаём соединение с БД
	con = get_db()
	
	# при GET запросе выдадим JSON список городов
	if request.method == 'GET':
		cur = con.execute("""
			SELECT *
			FROM city
			"""
		)
		result = cur.fetchall()
		
		return jsonify([dict(row) for row in result])
	
	# при POST запросе добавим новый город, если он не существует,
	# иначе вернём его
	if request.method == 'POST':
		# получаем поле name из структуры JSON запроса c именем города
		request_json = request.json
		name = request_json.get('name')
		
		# если поле name не определено, возвращаем код 400
		if not name:
			return '', 400
		
		# проверяем, существует ли такой город в БД
		cur = con.execute("""
			SELECT *
			FROM city as c
			WHERE c.name = ?
			""",
			(name,)
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

			cur = con.execute("""
				SELECT *
				FROM city as c
				WHERE c.name = ?
				""",
				(name,)
			)
			result = cur.fetchall()
		
		return jsonify([dict(row) for row in result][0])

# ##############################################################################
# ### [/colors]
# ##############################################################################
@app.route('/colors', methods=["GET", "POST"])
def colors():
	""" Обработка получения списка всех цветов из БД
		Обработка добавления в БД нового цвета
	"""
	# получаем user_id из текущей сессии
	user_id = session.get('user_id')
	# если, user_id не существует, значит сессия не создана, возвращаем код 401
	if user_id is None:
		return '', 401	
	
	# создаём соединение с БД
	con = get_db()

	# проверяем в БД, является ли выбранный пользователь продавцом
	cur = con.execute("""
		SELECT *
		FROM account as ac
			JOIN seller as slr ON slr.account_id = ac.id
		WHERE ac.id = ?
		""",
		(user_id,)
	)
	is_seller = cur.fetchall()

	if is_seller:	
		if request.method == 'GET':
			# при GET запросе, выводим JSON список всех доступных в БД цветов
			cur = con.execute("""
				SELECT *
				FROM color
				"""
			)
			result = cur.fetchall()
			
			return jsonify([dict(row) for row in result])
		
		if request.method == 'POST':
			# при POST запросе получаем поля name и hex из структуры
			# JSON запроса c новым цветом
			request_json = request.json
			name = request_json.get('name')
			hex = request_json.get('hex')
			
			# если поле name или hex не определено, возвращаем код 400
			if not name or not hex:
				return '', 400
			
			# проверяем, существует ли такой цвет в БД
			cur = con.execute("""
				SELECT *
				FROM color as c
				WHERE c.name = ?
				""",
				(name,)
			)
			result = cur.fetchall()

			# если цвет отсутствует в БД, добавляем его
			if not result:
				cur = con.execute("""
					INSERT INTO color (name, hex)
					VALUES (?, ?)
					""",
					(name, hex,)
				)
				con.commit()

				cur = con.execute("""
					SELECT *
					FROM color as c
					WHERE c.name = ?
					""",
					(name,)
				)
				result = cur.fetchall()
		
			return jsonify([dict(row) for row in result][0])
	else:
		return '', 403

# ##############################################################################
# ### [/image]
# ##############################################################################
@app.route('/images', methods=["POST"])
def images():
	""" Обработка добавления в БД URL ссылки на изображение """
	pass

# ##############################################################################
# ### [/images/<name>]
# ##############################################################################
@app.route('/images/<name>')
def get_image(name):
	""" Обработка получения ссылки из БД на изображение по его имени """
	pass
	