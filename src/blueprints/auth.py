from flask import (
	Blueprint,
	request,
	session
)

from werkzeug.security import (
	generate_password_hash,
	check_password_hash
)

from flask.views import MethodView

from db import db

bp = Blueprint('auth', __name__)

class LoginView(MethodView):
	# ### POST #################################################################	
	def post(self):
		""" Обработка авторизации на сайте """
		# получаем поля email(логин) и password(пароль) из
		# структуры JSON запроса
		request_json = request.json
		email = request_json.get('email')
		password = request_json.get('password')
		
		# если хотя бы одно поле пусто или не определено, возвращаем код 400
		if not email or not password :
			return '', 400
		
		# создаём соединение с БД
		con = db.connection
		
		# получаем пользователя из БД 
		cur = con.execute("""
			SELECT *
			FROM account
			WHERE email = ?
			""",
			(email,)
		)
		user = cur.fetchone()
		
		# если пользователь не найден в БД, возвращаем код 404
		if user is None:
			return '', 404

		# если пароль пользователя введён не корректный, возвращаем код 403
		if not check_password_hash(user['password'], password):
			return '', 403
		
		# открываем сессию (авторизуемся)
		session['user_id'] = user['id']
		
		return '', 200

class LogoutView(MethodView):
	# ### POST #################################################################	
	def post(self):
		""" Обработка выхода из авторизации """
		# прекращаем сессию
		session.pop('user_id', None)
		return '', 200
	
bp.add_url_rule('/login', view_func=LoginView.as_view('login'))
bp.add_url_rule('/logout', view_func=LogoutView.as_view('logout'))
