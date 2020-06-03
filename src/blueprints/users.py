from flask import (
	Blueprint,
	request,
	session,
	jsonify
)

import time

from werkzeug.security import (
	generate_password_hash,
	check_password_hash
)

from flask.views import MethodView

from db import db

bp = Blueprint('users', __name__)

class UsersView(MethodView):
	
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
		
		# email - является уникальным ИД пользователя, а это означает,
		# что не может существовать 2 пользователя с одним email адресом !
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
		
		#регистрируем в БД пользователя
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
		
		# получаем основную информацию о пользователе
		cur = con.execute("""
			SELECT ac.id, ac.first_name, ac.last_name, ac.email
			FROM account AS ac
			WHERE ac.email = ?
			""",
			(email,)
		)
		user = dict(cur.fetchone())
		
		# извлекаем id зарегистрированного пользователя
		user_id = user['id']
		
		# проверяем, отмечен ли регистрируемый пользователь как "продавец"
		# если да, регистрируем в БД пользователя как продавца
		if is_seller:
			# получаем необходимые для "продавца" поля из структуры JSON запроса
			phone = request_json.get('phone')
			zip_code = request_json.get('zip_code')
			city_id = request_json.get('city_id')
			street = request_json.get('street')
			home = request_json.get('home')
			
			# если хотя бы одно поле пусто или не определено, возвращаем код 400
			if not phone or not zip_code or not city_id or not street \
				or not home:
				return '', 400
				
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
			
			# возвращаем полную информацию о пользователе
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
			# пользователь не является продавцом
			user['is_seller'] = 'false'
			
		# возвращаем ответ из БД в виде JSON объекта зарег. пользователя
		return jsonify(user), 201

class UsersIDView(MethodView):
	
	def get(self, id):
		""" Обработка получения сведений о пользователе по его ID """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 403
		if user_id is None:
			return '', 403
		
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
			# если является, то получаем полную информацию о пользователе
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
			# иначе, получаем основную информацию о пользователе
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
	
	def patch(self, id):
		""" Обработка частичного редактирования сведений о пользователе
		    по его ID """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 403
		if user_id is None:
			return '', 403
		
		# проверим, может ли текущий авторизованный пользователь редактировать
		# информацию аккаунта под полученным ID и если не может, вернём код 403
		if user_id != id:
			return '', 403
		
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
		# и при их наличие обновляем соответствие в БД
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
		
		# получим основную информацию о пользователе из БД
		cur = con.execute("""
			SELECT ac.id, ac.first_name, ac.last_name, ac.email
			FROM account AS ac
			WHERE ac.id = ?
			""",
			(id,)
		)
		user = dict(cur.fetchone())
		user['is_seller'] = 'false'
		
		is_seller = request_json.get('is_seller')
		# проверим, отмечен ли пользователь продавцом в JSON запросе
		if is_seller is not None and not is_seller and user_as_seller:
			# и если не отмечен, но является продавцом, удалим его как продавца
			
			# удалим все связанные с объявлениями продавца, теги
			cur = con.execute("""
				DELETE FROM adtag
				WHERE adtag.id IN (
					SELECT adtag.id
					FROM adtag
						JOIN ad ON ad.id = adtag.ad_id
						JOIN seller ON seller.id = ad.seller_id
					WHERE seller.id = ?
				)
				""",
				(seller_id,)
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
			if zip_code is not None:
				cur = con.execute("""
					SELECT s.zip_code
					FROM seller AS s
					WHERE s.id = ?
					""",
					(seller_id,)
				)
				old_zip_code = dict(cur.fetchone())['zip_code']
				cur = con.execute("""
					UPDATE seller
					SET zip_code = ?
					WHERE seller.id = ?
					""",
					(zip_code, seller_id,)
				)
				cur = con.execute("""
					UPDATE zipcode
					SET zip_code = ?
					WHERE zip_code = ?
					""",
					(zip_code, old_zip_code)
				)
			if city_id is not None:
				cur = con.execute("""
					UPDATE zipcode
					SET city_id = ?	
					WHERE zip_code = ?
					""",
					(city_id, zip_code,)
				)
			con.commit()
			
			# получим полную информацию о пользователе из БД
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
		
		return jsonify(user)

class UsersAdsView(MethodView):
	
	def get(self, id):
		""" Обработка получения всех объявлений пользователя по его ID """
		# получаем query параметры из запроса
		seller_id_query = request.args.get('seller_id')
		tags_query = request.args.get('tags')
		make_query = request.args.get('make')
		model_query = request.args.get('model')
		
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
		user_ads_id = [row['id'] for row in cur.fetchall()]
		
		result = []
		for ad_id in user_ads_id:
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
			
			# фильтруем по query параметру "make"
			if make_query is not None:
				if car['make'].lower() != make_query.lower():
					continue
			# фильтруем по query параметру "seller_id"
			if seller_id_query is not None:
				if int(ad['seller_id']) != int(seller_id_query):
					continue
			# фильтруем по query параметру "model"
			if model_query is not None:
				if car['model'].lower() != model_query.lower():
					continue
			# фильтруем по query параметру "tags"
			if tags_query is not None:
				if tags_query.lower() not in ad['tags']:
					continue
			
			result.append(ad)

		return jsonify(result)
	
	def post(self, id):
		""" Обработка добавления нового объявления от пользователя по его ID """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 403
		if user_id is None or user_id != id:
			return '', 403
			
		# получаем обязательные поля из JSON запроса
		request_json = request.json
		title = request_json.get('title')
		tags = request_json.get('tags')
		car = request_json.get('car')
		
		# если хотя бы одно поле пусто или не определено, возвращаем код 400
		if not title or not tags or not car:
			return '', 400
		
		# разберём на составные части объект "car"
		make = car.get('make')
		model = car.get('model')
		colors = car.get('colors')
		mileage = car.get('mileage')
		num_owners = car.get('num_owners')
		reg_number = car.get('reg_number')
		images = car.get('images')
		
		# если хотя бы одно основное поле пусто или не определено,
		# возвращаем код 400
		if not make or not model or not colors or not mileage \
			or not reg_number:
			return '', 400
		
		if not num_owners:
			num_owners = 1
		
		date = int(time.time())
		
		# создаём соединение с БД
		con = db.connection
		
		# проверяем в БД, является ли текущий пользователь продавцом
		cur = con.execute("""
			SELECT slr.id
			FROM account AS ac
				JOIN seller AS slr ON slr.account_id = ac.id
			WHERE ac.id = ?
			""",
			(user_id,)
		)
		is_seller = cur.fetchone()
		
		if is_seller is not None:
			# текущий пользователь определён как продавец
			
			# получим Seller.ID текущего пользователя
			seller_id = dict(is_seller)['id']
			
			# проверим существование авто в БД
			cur = con.execute("""
				SELECT car.id
				FROM car
				WHERE car.reg_number = ?
					AND car.make = ?
					AND car.model = ?
				""",
				(reg_number, make, model)
			)
			car_exist = cur.fetchone()
			
			if not car_exist:
				# если такого авто не найдено, регистрируем в БД
				# указанное в запросе авто
				cur = con.execute("""
					INSERT INTO car (make, model, mileage, num_owners, reg_number)
					VALUES (?, ?, ?, ?, ?)
					""",
					(make, model, mileage, num_owners, reg_number)
				)
				con.commit()
			
				# получаем ID зарегистрированного авто
				cur = con.execute("""
					SELECT car.id
					FROM car
					WHERE car.reg_number = ?
						AND car.make = ?
						AND car.model = ?
					""",
					(reg_number, make, model)
				)
				car_id = cur.fetchone()['id']
				
				# связываем каждый заданный в запросе цвет с созданным авто
				for color in colors:
					cur = con.execute("""
						INSERT OR IGNORE INTO carcolor (color_id, car_id)
						VALUES (?, ?)
						""",
						(color, car_id)
					)
				con.commit()
			
				# регистрируем в БД объявление
				# и связываем его с продавцом и авто
				cur = con.execute("""
					INSERT INTO ad (title, date, seller_id, car_id)
					VALUES (?, ?, ?, ?)
					""",
					(title, date, seller_id, car_id)
				)
				con.commit()
				
				# получаем ID зарегистрированного объявления
				cur = con.execute("""
					SELECT ad.id
					FROM ad
					WHERE ad.seller_id = ?
						AND ad.car_id = ?
						AND ad.title = ?
					""",
					(seller_id, car_id, title)
				)
				ad_id = cur.fetchone()['id']
			
				# регистрируем в БД указанные в запросе теги
				for tag in tags:
					cur = con.execute("""
						INSERT OR IGNORE INTO tag (name)
						VALUES (?)
						""",
						(tag,)
					)
					con.commit()
					
					# получаем ID зарегистрированного тега
					cur = con.execute("""
						SELECT tag.id
						FROM tag
						WHERE tag.name = ?
						""",
						(tag,)
					)
					tag_id = cur.fetchone()['id']
				
					# связываем каждый тег с созданным объявлением
					cur = con.execute("""
						INSERT OR IGNORE INTO adtag (tag_id, ad_id)
						VALUES (?, ?)
						""",
						(tag_id, ad_id)
					)
					con.commit()
			
				# выведем созданное объявление
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
			
				return jsonify(ad)
			else:
				# если авто существует, вернём код 409
				return '', 409			
		else:
			# иначе, пользователь не определён как продавец, выдаём код 403
			return '', 403

bp.add_url_rule('', view_func=UsersView.as_view('users'))
bp.add_url_rule('<int:id>', view_func=UsersIDView.as_view('users_id'))
bp.add_url_rule('<int:id>/ads', view_func=UsersAdsView.as_view('users_ads'))
