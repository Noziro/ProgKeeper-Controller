import mariadb
import os
from pathlib import Path
from .common import is_database_ready

SQL_ROOT_CREDENTIALS = {
	"host": os.environ['DB_HOST'] or 'localhost',
	"port": int(os.environ['DB_PORT']) or 3306,
	"user": 'root',
	"pass": os.environ['DB_ROOT_PASSWORD'] or 'root_password_change_me',
	"dbname": os.environ['DB_DATABASE'] or 'progkeeper'
}

def setup_database() -> bool:
	""" Sets up database with required tables if they do not exist. """
	connection = mariadb.connect(
		host=SQL_ROOT_CREDENTIALS['host'],
		port=SQL_ROOT_CREDENTIALS['port'],
		user=SQL_ROOT_CREDENTIALS['user'],
		password=SQL_ROOT_CREDENTIALS['pass'],
		database=SQL_ROOT_CREDENTIALS['dbname']
	)
	cursor = connection.cursor()

	# Failsafe check to avoid attempting illegal operations
	if is_database_ready(cursor):
		return False
	
	# Read and execute schema SQL file
	schema_file:Path = Path(__file__).parent.parent.parent / 'schema.sql'

	with open(schema_file, 'r') as file:
		schema_sql:str = file.read()
		commands:list[str] = schema_sql.split(';')
		for command in commands:
			command = command.strip()
			if command:
				cursor.execute(command)

	connection.commit()
	connection.close()
	return True

if __name__ == '__main__':
	setup_database()