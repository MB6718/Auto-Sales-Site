from flask import (
	Blueprint,
	render_template
)

import datetime

from db import db

bp = Blueprint('index', __name__)

@bp.route('/')
@bp.route('/index')
def index():
	""" Обработка запроса главной страницы нашего сайта объявлений """
	now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
	return render_template(
		'index.html',
		app_title='Auto Sales (Beta)',
		date_time_stamp=now
	)
