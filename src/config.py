import os

class Config():
	DB_FILE = os.getenv('DB_FILE', 'database.db')
	SECRET_KEY = os.getenv('SECRET_KEY', 'topsecretkey').encode()