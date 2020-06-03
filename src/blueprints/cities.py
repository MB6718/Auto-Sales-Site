from flask import (
	Blueprint,
	request,
	jsonify
)

from flask.views import MethodView

from db import db

bp = Blueprint('cities', __name__)

class CitiesView(MethodView):

	def get(self):
		""" Обработка получения списка всех городов из БД """
		# создаём соединение с БД
		con = db.connection
		
		# получим из БД и выдадим в JSON список городов
		cur = con.execute("""
			SELECT *
			FROM city
			"""
		)
		cities = cur.fetchall()
		
		return jsonify([dict(row) for row in cities])
	
	def post(self):
		""" Обработка добавления в БД нового города """
		# создаём соединение с БД
		con = db.connection		

		# получаем поле name из структуры JSON запроса c именем города
		request_json = request.json
		name = request_json.get('name')
		
		# если поле name не определено, возвращаем код 400
		if not name:
			return '', 400
		
		# проверяем, существует ли такой город в БД
		cur = con.execute("""
			SELECT *
			FROM city AS c
			WHERE c.name = ?
			""",
			(name,)
		)
		city = cur.fetchone()
		
		# если город отсутствует в БД, добавляем его
		if not city:
			cur = con.execute("""
				INSERT INTO city (name)
				VALUES (?)
				""",
				(name,)
			)
			con.commit()
			
			# получаем город, добавленный в БД
			cur = con.execute("""
				SELECT *
				FROM city AS c
				WHERE c.name = ?
				""",
				(name,)
			)
			city = cur.fetchone()
		
		return jsonify(dict(city))

bp.add_url_rule('', view_func=CitiesView.as_view('cities'))
