import os

class Config():
	PYTHONPATH = os.getenv('PYTHONPATH', 'src')
	DB_FILE = os.getenv('DB_FILE', 'database.db')
	SECRET_KEY = os.getenv('SECRET_KEY', 'topsecretkey').encode()
	UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
	upload_path = os.path.join(PYTHONPATH, UPLOAD_FOLDER)
	if not os.path.exists(upload_path):
		os.mkdir(upload_path)
