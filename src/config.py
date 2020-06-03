import os

class Config():
	PYTHONPATH = os.getenv('PYTHONPATH', 'src')
	DB_FILE = os.getenv('DB_FILE', 'database.db')
	SECRET_KEY = os.getenv('SECRET_KEY', 'topsecretkey').encode()
	UPLOAD_FOLDER = os.path.abspath(
		os.path.join(
			os.path.dirname(__file__),
			'..',
			os.getenv('UPLOAD_FOLDER', 'uploads')
		)
	)
	if not os.path.exists(UPLOAD_FOLDER):
		os.mkdir(UPLOAD_FOLDER)
