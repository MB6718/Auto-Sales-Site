from flask import (
	Blueprint,
	request,
	session,
	jsonify
)

from flask.views import MethodView

from db import db

bp = Blueprint('images', __name__)

class ImagesView(MethodView):
	# ### POST #################################################################
	def post(self):
		""" Обработка добавления в БД URL ссылки на изображение """
		# получаем user_id из текущей сессии
		user_id = session.get('user_id')
		
		# если, user_id не существует, значит сессия не создана,
		# возвращаем код 401
		if user_id is None:
			return '', 401
		
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
		
		if is_seller:
			return f'User ID: {user_id}, OK', 200
		
		# иначе пользователь не зарегистрирован как продавец, то вернём код 403
		return '', 403

class GetImagesView(MethodView):
	# ### GET ##################################################################
	def get(self, img_name):
		""" Обработка получения ссылки из БД на изображение по его имени """
		# создаём соединение с БД
		con = db.connection
		
		return f'{img_name}', 200

bp.add_url_rule('', view_func=ImagesView.as_view('images'))
bp.add_url_rule('/<img_name>', view_func=GetImagesView.as_view('get_images'))
