import sqlite3

from flask import g

DB_FILE='database.db'

def get_db():
	""" Получить данные из БД """
	if 'db' not in g:
		g.db = sqlite3.connect(
			DB_FILE,
			detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
		)
		g.db.row_factory = sqlite3.Row
	return g.db

def close_db():
	""" Закрыть соединение с БД """
	db = g.pop('db', None)
	if db is not None:
		db.close()