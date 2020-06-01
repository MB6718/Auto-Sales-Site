from flask import (
	Blueprint,
	request,
	session,
	jsonify,
	current_app,
	url_for,
	send_from_directory
)

import os

from werkzeug.utils import secure_filename

from flask.views import MethodView

from db import db

# Список разрешённых к передаче расширений файлов
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

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
			SELECT slr.id
			FROM account AS ac
				JOIN seller AS slr ON slr.account_id = ac.id
			WHERE ac.id = ?
			""",
			(user_id,)
		)
		is_seller = cur.fetchone()
		
		# если пользователь является продавцом
		if is_seller is not None:
			# пробуем получить файл из запроса
			try:
				file = request.files['file']
			except:
				# файла в запросе нет, вернём код 400
				return '', 400
			
			if file:
				# если файл получен, сохраним его в папку
				filename = secure_filename(file.filename)
				# проверим расширение передаваемого файла на соответствие
				if '.' in filename and \
					filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS:
					
					# получим путь папки с файлами загружаемых картинок
					file_path = os.path.join(
						current_app.config['PYTHONPATH'],
						os.path.join(
							current_app.config['UPLOAD_FOLDER'],
							filename
						),
					)	
					file.save(file_path)
					
					# так и не удалось победить url_for !
					# я хз, почему он формирует строку c filename как query параметры
					# хотя, в доках написано что это будет как endpoint ?
					# url_for('.images', filename=filename, _external=True)
					
					# поэтому пока используем костыль !
					img_url = str(
						url_for(
							'.images',
							filename=filename,
							_external=True
						)
					).replace('?filename=', '/')
					
					return jsonify({'url' : img_url}), 200
			
			return '', 400
		
		# иначе пользователь не зарегистрирован как продавец, то вернём код 403
		return '', 403

class GetImagesView(MethodView):
	# ### GET ##################################################################
	def get(self, filename):
		""" Обработка получения ссылки из БД на изображение по его имени """
		# получим путь папки с файлами загружаемых картинок
		file_path = os.path.join(
			current_app.config['PYTHONPATH'],
			os.path.join(
				current_app.config['UPLOAD_FOLDER'],
				filename
			),
		)

		# проверим, есть ли указанный файл по пути
		if os.path.exists(file_path):
			# указанный файл найден, вернём его
			return send_from_directory(
				current_app.config['UPLOAD_FOLDER'],
				filename,
				as_attachment=True
			)
		
		# указанный файл не найден, вернём код 404
		return '', 404

bp.add_url_rule('', view_func=ImagesView.as_view('images'))
bp.add_url_rule('/<filename>', view_func=GetImagesView.as_view('get_images'))
