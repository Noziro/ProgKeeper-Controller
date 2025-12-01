import mariadb
import os

SQL_CREDENTIALS = {
	"host": os.environ['DB_HOST'] or 'localhost',
	"port": int(os.environ['DB_PORT']) or 3306,
	"user": os.environ['DB_USER'] or 'progkeeper',
	"pass": os.environ['DB_PASSWORD'] or 'change_me',
	"dbname": os.environ['DB_DATABASE'] or 'progkeeper'
}

def is_database_ready(cursor) -> bool:
	cursor.execute("SHOW TABLES")
	return cursor.fetchone() != None

class DatabaseSession:
	def __init__(self):
		# TODO: catch connection errors
		self.connection = mariadb.connect(
			host=SQL_CREDENTIALS['host'],
			port=SQL_CREDENTIALS['port'],
			user=SQL_CREDENTIALS['user'],
			password=SQL_CREDENTIALS['pass'],
			database=SQL_CREDENTIALS['dbname']
		)
		self.cursor = self.connection.cursor()

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, traceback):
		self.connection.close()