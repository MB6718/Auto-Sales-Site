from flask import (
	Blueprint,
	request,
	session,
	jsonify,
	current_app,
	url_for,
	send_from_directory
)

import uuid

import os

from werkzeug.utils import secure_filename

from db import db

# Список разрешённых к передаче расширений файлов
ALLOWED_EXTENSIONS = set(['.png', '.jpg', '.jpeg', '.gif'])

bp = Blueprint('images', __name__)

@bp.route('', methods=["POST"])
def images():
	""" Обработка добавления в БД URL ссылки на изображение """
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
			file = request.files['image']
		except:
			# файла в запросе нет, вернём код 400
			return '', 400
		
		# если файл получен, сохраним его в папку
		if file:
			orig_fn = secure_filename(file.filename)
			file_ext = os.path.splitext(orig_fn)[1]
			filename = f'{uuid.uuid4()}{file_ext}'			
			upload_path = current_app.config['UPLOAD_FOLDER']
			
			# проверим расширение передаваемого файла на соответствие
			if file_ext in ALLOWED_EXTENSIONS:
				file.save(os.path.join(upload_path, filename))
				return jsonify(
					{'url' : url_for('images.get_images', filename=filename)}
				), 200
		
		return '', 400
	
	# иначе пользователь не зарегистрирован как продавец, то вернём код 403
	return '', 403

@bp.route('/<filename>')
def get_images(filename):
	""" Обработка получения по имени и Url пути изображения """
	# получим путь папки с файлами загружаемых картинок
	upload_path = current_app.config['UPLOAD_FOLDER']

	# проверим, есть ли указанный файл по пути
	if os.path.exists(upload_path):
		# указанный файл найден, вернём его
		return send_from_directory(
			upload_path,
			filename,
			as_attachment=True
		)
	
	# указанный файл не найден, вернём код 404
	return '', 404
