from flask import (
	Blueprint,
	request,
	session,
	jsonify
)

from werkzeug.security import (
	generate_password_hash,
	check_password_hash
)

from flask.views import MethodView

from db import db

bp = Blueprint('users', __name__)

class UsersView(MethodView):
	# ### POST #################################################################
	def post(self):
		""" Обработка регистрации нового пользователя """
		# получаем первостепенные поля из структуры JSON запроса
		request_json = request.json
		is_seller = request_json.get('is_seller')
		email = request_json.get('email')
		password = request_json.get('password')
		first_name = request_json.get('first_name')
		last_name = request_json.get('last_name')
		
		# если хотя бы одно поле пусто или не определено, возвращаем код 400
		if not email or not password or not first_name or not last_name \
			or is_seller is None:
			return '', 400
		
		# создаём соединение с БД
		con = db.connection
		
		# email - является уникальным ИД пользователя при регистрации
		# означает что не может существовать 2 пользователя с одним email адресом !
		# а значит проверим, зарегистрирован ли в БД такой e-mail
		cur = con.execute("""
			SELECT ac.email
			FROM account AS ac
			WHERE ac.email IN (?)
			""",
			(email,)
		)
		check_email = cur.fetchone()
		
		# и если он уже существует, возвращаем код 409
		if check_email is not None:
			return '', 409
		
		# преобразуем строку с паролем в хэш-пароль, который сохраним в БД
		password_hash = generate_password_hash(password)
		
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
			if not phone or not zip_code or not city_id or not street \
				or not home:
				return '', 400
				
			# регистрируем (с записью в БД) пользователя как продавца
			cur = con.execute("""
				INSERT INTO account (first_name,
									 last_name,
									 email,
									 password)
				VALUES (?, ?, ?, ?)
				""",
				(first_name, last_name, email, password_hash)
			)
			con.commit()
			
			# получаем id зарегистрированного пользователя
			cur = con.execute("""
				SELECT ac.id AS id
				FROM account AS ac
				WHERE ac.email = ?
				""",
				(email,)
			)
			user_id = cur.fetchone()['id']
			
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
				(zip_code, street, home, phone, user_id)
			)
			con.commit()
			
			# возвращаем ответ из БД в виде JSON объекта зарег. пользователя
			cur = con.execute("""
				SELECT ac.id, ac.first_name, ac.last_name, ac.email,
					   slr.zip_code, slr.street, slr.home, slr.phone,
					   zc.city_id
				FROM account AS ac
					JOIN seller AS slr ON slr.account_id = ac.id
					JOIN zipcode AS zc ON zc.zip_code = slr.zip_code
				WHERE ac.email = ?
				""",
				(email,)
			)
			user = dict(cur.fetchone())
			user['is_seller'] = 'true'
		else:
			# иначе, регистрируем (с записью в БД) простого пользователя
			cur = con.execute("""
				INSERT INTO account (first_name,
									 last_name,
									 email,
									 password)
				VALUES (?, ?, ?, ?)
				""",
				(first_name, last_name, email, password_hash)
			)
			con.commit()
			
			# если успех, возвращаем ответ в виде JSON объекта
			# зарегистрированного пользователя
			cur = con.execute("""
				SELECT ac.id, ac.first_name, ac.last_name, ac.email
				FROM account AS ac
				WHERE ac.email = ?
				""",
				(email,)
			)
			user = dict(cur.fetchone())
			user['is_seller'] = 'false'
		
		return jsonify(user), 201

class UsersIDView(MethodView):
	# ### GET ##################################################################
	def get(self, id):
		""" Обработка получения сведений о пользователе по его ID """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 401
		if user_id is None:
			return '', 401	
		
		# создаём соединение с БД
		con = db.connection

		# проверяем в БД, существует ли выбранный пользователь
		cur = con.execute("""
			SELECT *
			FROM account AS ac
			WHERE ac.id = ?
			""",
			(id,)
		)
		user_exist = cur.fetchone()
		
		# если пользователь с таким ID не существует, вернём код 404
		if not user_exist:
			return '', 404
		
		# проверим, является ли пользователь под ID продавцом
		cur = con.execute("""
			SELECT slr.id
			FROM account AS ac
				JOIN seller AS slr ON slr.account_id = ac.id
			WHERE ac.id = ?
			""",
			(id,)
		)
		is_seller = cur.fetchone()
		
		if is_seller is not None:
			# если является, то выводим полную информацию
			cur = con.execute("""
				SELECT ac.id, ac.first_name, ac.last_name, ac.email,
					   slr.zip_code, slr.street, slr.home, slr.phone,
					   zc.city_id
				FROM account AS ac
					JOIN seller AS slr ON slr.account_id = ac.id
					JOIN zipcode AS zc ON zc.zip_code = slr.zip_code
				WHERE ac.id = ?
				""",
				(id,)
			)
			user = dict(cur.fetchone())
			user['is_seller'] = 'true'
		else:
			# иначе, выводим основную информацию
			cur = con.execute("""
				SELECT ac.id, ac.first_name, ac.last_name, ac.email
				FROM account AS ac
				WHERE ac.id = ?
				""",
				(id,)
			)
			user = dict(cur.fetchone())
			user['is_seller'] = 'false'
			
		return jsonify(user)
	
	# ### PATCH ################################################################
	def patch(self, id):
		""" Обработка частичного редактирования сведений о пользователе
		    по его ID """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 401
		if user_id is None:
			return '', 401
		
		# проверим, может ли текущий авторизованный пользователь редактировать
		# информацию аккаунта под полученным ID и если не может, вернём код 409
		if user_id != id:
			return '', 409
		
		# создаём соединение с БД
		con = db.connection

		# проверим, является ли пользователь продавцом
		cur = con.execute("""
			SELECT slr.id
			FROM account AS ac
				JOIN seller AS slr ON slr.account_id = ac.id
			WHERE ac.id = ?
			""",
			(id,)
		)
		user_as_seller = cur.fetchone()
		
		if user_as_seller is not None:
			seller_id = dict(user_as_seller)['id']
		
		# получаем возможные основные поля из структуры JSON запроса
		request_json = request.json
		first_name = request_json.get('first_name')
		last_name = request_json.get('last_name')

		if first_name is not None:
			cur = con.execute("""
				UPDATE account 
				SET first_name = ?
				WHERE account.id = ?
				""",
				(first_name, id,)
			)
		if last_name is not None:
			cur = con.execute("""
				UPDATE account 
				SET last_name = ?
				WHERE account.id = ?
				""",
				(last_name, id,)
			)
		con.commit()
		
		is_seller = request_json.get('is_seller')
		# проверим, отмечен ли пользователь продавцом в JSON запросе
		if is_seller is not None and not is_seller and user_as_seller:
			# и если не отмечен, но является продавцом, удалим его как продавца
			
			# сначала, получим ID всех тэгов, связанных с объявлениями продавца
			cur = con.execute("""
				SELECT adtag.id
				FROM adtag
					JOIN ad ON ad.id = adtag.ad_id
					JOIN seller ON seller.id = ad.seller_id
				WHERE seller.id = ?
				""",
				(seller_id,)
			)
			tags = [dict(row)['id'] for row in cur.fetchall()]

			# удалим все связанные с объявлениями продавца, теги
			for tag in tags:
				cur = con.execute("""
					DELETE FROM adtag
					WHERE adtag.id = ?
					""",
					(tag,)
				)
			
			# удалим все объявления, связанные с ID продавца
			cur = con.execute("""
				DELETE FROM ad
				WHERE ad.seller_id = ?
				""",
				(seller_id,)
			)
			
			# удалим ID продавца
			cur = con.execute("""
				DELETE FROM seller
				WHERE seller.id = ?
				""",
				(seller_id,)
			)
			con.commit()
			
		elif user_as_seller is not None:
			# если текущий пользователь является продавцом, получаем возможные,
			# для "продавца", поля из структуры JSON запроса
			phone = request_json.get('phone')
			zip_code = request_json.get('zip_code')
			city_id = request_json.get('city_id')
			street = request_json.get('street')
			home = request_json.get('home')

			# и обновляем соответствующие поля в БД			
			if phone is not None:
				cur = con.execute("""
					UPDATE seller 
					SET phone = ?			
					WHERE seller.id = ?
					""",
					(phone, seller_id,)
				)
			if zip_code is not None:
				cur = con.execute("""
					UPDATE seller 
					SET zip_code = ?			
					WHERE seller.id = ?
					""",
					(zip_code, seller_id,)
				)
			if city_id is not None:
				cur = con.execute("""
					UPDATE seller 
					SET city_id = ?			
					WHERE seller.id = ?
					""",
					(city_id, seller_id,)
				)
			if street is not None:
				cur = con.execute("""
					UPDATE seller
					SET street = ?			
					WHERE seller.id = ?
					""",
					(street, seller_id,)
				)
			if home is not None:
				cur = con.execute("""
					UPDATE seller 
					SET home = ?				
					WHERE seller.id = ?
					""",
					(home, seller_id,)
				)		
			con.commit()
		
		# проверим, является ли пользователь под ID продавцом
		cur = con.execute("""
			SELECT slr.id
			FROM account AS ac
				JOIN seller AS slr ON slr.account_id = ac.id
			WHERE ac.id = ?
			""",
			(id,)
		)
		is_seller = cur.fetchone()
		
		if is_seller is not None:
			# если является, то выводим полную информацию
			cur = con.execute("""
				SELECT ac.id, ac.first_name, ac.last_name, ac.email,
					   slr.zip_code, slr.street, slr.home, slr.phone,
					   zc.city_id
				FROM account AS ac
					JOIN seller AS slr ON slr.account_id = ac.id
					JOIN zipcode AS zc ON zc.zip_code = slr.zip_code
				WHERE ac.id = ?
				""",
				(id,)
			)
			user = dict(cur.fetchone())
			user['is_seller'] = 'true'
		else:
			# иначе, выводим основную информацию
			cur = con.execute("""
				SELECT ac.id, ac.first_name, ac.last_name, ac.email
				FROM account AS ac
				WHERE ac.id = ?
				""",
				(id,)
			)
			user = dict(cur.fetchone())
			user['is_seller'] = 'false'
			
		return jsonify(user)

class UsersAdsView(MethodView):
	# ### GET ##################################################################
	def get(self, id):
		""" Обработка получения всех объявлений пользователя по его ID """
		# создаём соединение с БД
		con = db.connection
		
		# получаем список всех объявлений пользователя по его ID
		cur = con.execute("""
			SELECT ad.id
			FROM ad
				JOIN seller AS slr ON slr.id = ad.seller_id
				JOIN account AS ac ON ac.id = slr.account_id
			WHERE ac.id = ?
			""",
			(id,)
		)
		user_ads_id = cur.fetchall()
		user_ads_id = [row['id'] for row in user_ads_id]
		
		result = []
		for i in range(len(user_ads_id)):
			ad_id = user_ads_id[i]
			
			# получаем из БД JSON объект объявления по его ID
			cur = con.execute("""
				SELECT *
				FROM ad
				WHERE ad.id = ?
				""",
				(ad_id,)
			)
			ad = dict(cur.fetchone())
			
			# получаем из БД список тегов строками, привязанных к ID объявления
			cur = con.execute("""
				SELECT t.name
				FROM adtag AS at
					JOIN tag AS t ON t.id = at.tag_id
				WHERE at.ad_id = ?
				""",
				(ad_id,)
			)
			tags = cur.fetchall()
			ad['tags'] = [row['name'] for row in tags]
			
			# получаем из БД JSON объект авто, привязанный к ID объявления
			cur = con.execute("""
				SELECT car.make, car.model, car.mileage,
					   car.num_owners, car.reg_number
				FROM car
					JOIN ad ON ad.car_id = car.id
				WHERE ad.id = ?
				""",
				(ad_id,)
			)
			car = dict(cur.fetchone())
			
			# получаем из БД список цветов, привязанных к ID авто
			cur = con.execute("""
				SELECT c.id, c.name, c.hex
				FROM carcolor AS caco
					JOIN color AS c ON c.id = caco.color_id
				WHERE caco.car_id = ?
				""",
				(ad['car_id'],)
			)		
			colors = cur.fetchall()
			car['colors'] = [dict(row) for row in colors]
			
			# получаем из БД список изображений, привязанных к ID авто
			cur = con.execute("""
				SELECT im.title, im.url
				FROM image AS im
				WHERE im.car_id = ?
				""",
				(ad['car_id'],)
			)		
			images = cur.fetchall()
			car['images'] = [dict(row) for row in images]
			
			ad['car'] = car
			result.append(ad)

		return jsonify(result)
	
	# ### POST #################################################################
	def post(self, id):
		""" Обработка добавления нового объявления от пользователя по его ID """
		pass

bp.add_url_rule('', view_func=UsersView.as_view('users'))
bp.add_url_rule('<int:id>', view_func=UsersIDView.as_view('users_id'))
bp.add_url_rule('<int:id>/ads', view_func=UsersAdsView.as_view('users_ads'))
