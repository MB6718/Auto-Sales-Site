from flask import (
	Blueprint,
	render_template
)

import datetime

from flask.views import MethodView

from db import db

bp = Blueprint('index', __name__)

class IndexView(MethodView):
	def get(self):
		""" Обработка запроса главной страницы нашего сайта объявлений """
		now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
		return render_template(
			'index.html',
			app_title='Auto Sales',
			date_time_stamp=now
		)

bp.add_url_rule('/', view_func=IndexView.as_view('root'))
bp.add_url_rule('/index', view_func=IndexView.as_view('index'))
