from flask import (
	Blueprint,
	request,
	session,
	jsonify
)

import time

from flask.views import MethodView

from db import db

import json

bp = Blueprint('ads', __name__)

class AdsView(MethodView):

	def get(self):
		""" Обработка получения всех объявлений """
		# получаем query параметры из запроса
		seller_id_query = request.args.get('seller_id')
		tags_query = request.args.get('tags')
		make_query = request.args.get('make')
		model_query = request.args.get('model')
		
		# создаём соединение с БД
		con = db.connection
		
		# получаем из БД кол-во всех ID объявлений, зарегистрированных в БД
		cur = con.execute("""
			SELECT ad.id
			FROM ad
			"""
		)
		ads = [row['id'] for row in cur.fetchall()]
		
		result = []
		for ad_id in ads:
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

	def post(self):
		""" Обработка добавления нового объявления на сайт """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 403
		if user_id is None:
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

class AdIdView(MethodView):
	
	def get(self, ad_id):
		""" Обработка получения объявления по его ID """
		# создаём соединение с БД
		con = db.connection
		
		# проверяем в БД, существует ли объявление под ID
		cur = con.execute("""
			SELECT ad.id
			FROM ad
			WHERE ad.id = ?
			""",
			(ad_id,)
		)
		ad_exist = cur.fetchone()
		
		# если не существует объявление с таким ID, возвратим код 404
		if ad_exist is None:
			return '', 404
		
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
	
	def patch(self, ad_id):
		""" Обработка частичного редактирования объявления по его ID """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 401
		if user_id is None:
			return '', 403

		# создаём соединение с БД
		con = db.connection
			
		# проверим, может ли текущий авторизованный пользователь редактировать
		# информацию объявления под полученным ID и если не может,
		# вернём код 403
		cur = con.execute("""
			SELECT ad.id AS ad_id, ac.id AS user_id
			FROM ad
				JOIN seller AS slr ON slr.id = ad.seller_id
				JOIN account AS ac ON ac.id = slr.account_id
			WHERE ad.id = ?
			""",
			(ad_id,)
		)
		user_as_seller = dict(cur.fetchone())
		
		if user_as_seller['user_id'] != user_id:
			return '', 403
		
		# получаем возможные основные поля из структуры JSON запроса
		request_json = request.json
		title = request_json.get('title')
		tags = request_json.get('tags')
		car = request_json.get('car')

		# если информация по авто указанна в запросе
		if car is not None:
			# разберём объект "car" на составляющие
			make = car.get('make')
			model = car.get('model')
			colors = car.get('colors')
			mileage = car.get('mileage')
			num_owners = car.get('num_owners')
			reg_number = car.get('reg_number')
			images = car.get('images')
			
			# получаем из БД id авто
			cur = con.execute("""
				SELECT ad.car_id
				FROM ad
				WHERE ad.id = ?
				""",
				(ad_id,)
			)
			car_id = dict(cur.fetchone())['car_id']
		
		# если заголовок объявления указан, обновим его в БД
		if title is not None:
			cur = con.execute("""
				UPDATE ad
				SET title = ?
				WHERE ad.id = ?
				""",
				(title, ad_id,)
			)
			con.commit()

		# если указаны новые или уже существующие теги, то добавим новые или
		# обновим связи с объявлением
		if tags is not None:
			# сначала удалим все связи тегов с объявлением под данным ID
			cur = con.execute("""
				DELETE FROM adtag
				WHERE adtag.ad_id = ?
				""",
				(ad_id,)
			)
			
			# добавим новые теги в БД и свяжем их с объявлением
			for tag in tags:
				cur = con.execute("""
					INSERT OR IGNORE INTO tag (name)
					VALUES (?)
					""",
					(tag,)
				)
				cur = con.execute("""
					SELECT tag.id
					FROM tag
					WHERE tag.name = ?
					""",
					(tag,)
				)
				tag_id = dict(cur.fetchone())['id']
				cur = con.execute("""
					INSERT INTO adtag (tag_id, ad_id)
					VALUES (?, ?)
					""",
					(tag_id, ad_id)
				)
			con.commit()
		
		# обновляем соответствующие поля авто в БД
		if make is not None:
			cur = con.execute("""
				UPDATE car
				SET make = ?
				WHERE car.id = ?
				""",
				(make, car_id,)
			)
		if model is not None:
			cur = con.execute("""
				UPDATE car
				SET model = ?
				WHERE car.id = ?
				""",
				(model, car_id,)
			)
		if mileage is not None:
			cur = con.execute("""
				UPDATE car
				SET mileage = ?
				WHERE car.id = ?
				""",
				(mileage, car_id,)
			)
		if num_owners is not None:
			cur = con.execute("""
				UPDATE car
				SET num_owners = ?
				WHERE car.id = ?
				""",
				(num_owners, car_id,)
			)
		if reg_number is not None:
			cur = con.execute("""
				UPDATE car
				SET reg_number = ?
				WHERE car.id = ?
				""",
				(reg_number, car_id,)
			)
		con.commit()
		
		# обновим связи цветов и авто
		if colors is not None:
			# сначала удалим все старые связи цветов с авто
			cur = con.execute("""
				DELETE FROM carcolor
				WHERE carcolor.car_id = ?
				""",
				(car_id,)
			)
			
			# добавим новые цвета и свяжем их с авто
			for color in colors:
				cur = con.execute("""
					INSERT INTO carcolor (color_id, car_id)
					VALUES (?, ?)
					""",
					(color, car_id)
				)
			con.commit()
		
		# заменим картинки новыми из переданного списка
		if images is not None:
			# Удалим все зависимости картинок и объявления
			cur = con.execute("""
				DELETE FROM image
				WHERE image.car_id = ?
				""",
				(car_id,)
			)
			
			# добавим новые картинки и свяжем их с авто
			for image in images:
				img_title = image.get('title')
				img_url = image.get('url')
				
				cur = con.execute("""
					INSERT INTO image (title, url, car_id)
					VALUES (?, ?, ?)
					""",
					(img_title, img_url, car_id)
				)
			con.commit()
		
		return '', 200
	
	def delete(self, ad_id):
		""" Обработка удаления объявления с сайта по его ID """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 403
		if user_id is None:
			return '', 403
		
		# создаём соединение с БД
		con = db.connection
		
		# проверяем в БД, существует ли объявление под ID
		cur = con.execute("""
			SELECT ad.id
			FROM ad
			WHERE ad.id = ?
			""",
			(ad_id,)
		)
		ad_exist = cur.fetchone()
		
		# если не существует объявление с таким ID, возвратим код 404
		if ad_exist is None:
			return '', 404
		
		# проверяем в БД, является ли выбранный пользователь
		# владельцем объявления под данным ID
		cur = con.execute("""
			SELECT ad.id AS ad_id, ac.id AS user_id
			FROM ad
				JOIN seller AS slr ON slr.id = ad.seller_id
				JOIN account AS ac ON ac.id = slr.account_id
			WHERE ad.id = ?
			""",
			(ad_id,)
		)
		is_owner = dict(cur.fetchone())

		if is_owner['user_id'] == user_id:
			# и если является, то сначала удалим все связи тегов
			# с объявлением под данным ID
			cur = con.execute("""
				DELETE FROM adtag
				WHERE adtag.ad_id = ?
				""",
				(ad_id,)
			)
			
			# удалим объявление под ID
			cur = con.execute("""
				DELETE FROM ad
				WHERE ad.id = ?
				""",
				(ad_id,)
			)
			con.commit()
			return '', 200
		
		# иначе, пользователь не является владельцем объявления, вернём код 403
		return '', 403

bp.add_url_rule('', view_func=AdsView.as_view('ads'))
bp.add_url_rule('/<int:ad_id>', view_func=AdIdView.as_view('ad_id'))
