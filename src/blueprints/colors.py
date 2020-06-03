from flask import (
	Blueprint,
	request,
	session,
	jsonify
)

from flask.views import MethodView

from db import db

bp = Blueprint('colors', __name__)

class ColorsView(MethodView):

	def get(self):
		""" Обработка получения списка всех цветов из БД """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 403
		if user_id is None:
			return '', 403
		
		# создаём соединение с БД
		con = db.connection

		# проверяем в БД, является ли выбранный пользователь продавцом
		cur = con.execute("""
			SELECT *
			FROM account AS ac
				JOIN seller AS slr ON slr.account_id = ac.id
			WHERE ac.id = ?
			""",
			(user_id,)
		)
		is_seller = cur.fetchone()

		if is_seller is not None:
			# получаем список всех доступных в БД цветов
			cur = con.execute("""
				SELECT *
				FROM color
				"""
			)
			colors = cur.fetchall()
			
			# выводим JSON список
			return jsonify([dict(row) for row in colors])
		
		# иначе пользователь не зарегистрирован как продавец, то вернём код 403
		return '', 403
	
	def post(self):
		""" Обработка добавления в БД нового цвета """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 403
		if user_id is None:
			return '', 403	
		
		# создаём соединение с БД
		con = db.connection

		# проверяем в БД, является ли выбранный пользователь продавцом
		cur = con.execute("""
			SELECT *
			FROM account AS ac
				JOIN seller AS slr ON slr.account_id = ac.id
			WHERE ac.id = ?
			""",
			(user_id,)
		)
		is_seller = cur.fetchone()

		if is_seller is not None:
			# получаем поля name и hex из структуры JSON запроса c новым цветом
			request_json = request.json
			name = request_json.get('name')
			hex = request_json.get('hex')
			
			# если поле name или hex не определено, возвращаем код 400
			if not name or not hex:
				return '', 400
			
			# проверяем, существует ли такой цвет в БД
			cur = con.execute("""
				SELECT *
				FROM color AS c
				WHERE c.name = ?
				""",
				(name,)
			)
			color = cur.fetchone()

			# если цвет отсутствует в БД, добавляем его
			if color is not None:
				cur = con.execute("""
					INSERT INTO color (name, hex)
					VALUES (?, ?)
					""",
					(name, hex,)
				)
				con.commit()
				
				# получаем добавленный цвет из БД
				cur = con.execute("""
					SELECT *
					FROM color AS c
					WHERE c.name = ?
					""",
					(name,)
				)
				color = cur.fetchone()
		
			return jsonify(dict(color))
		
		# иначе пользователь не зарегистрирован как продавец, то вернём код 403
		return '', 403

bp.add_url_rule('', view_func=ColorsView.as_view('colors'))
