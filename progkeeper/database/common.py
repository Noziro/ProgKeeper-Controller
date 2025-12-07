import mariadb
import os
import typing
from types import TracebackType

SQL_CREDENTIALS:dict[str, str|int] = {
	"host": os.environ['DB_HOST'] if 'DB_HOST' in os.environ else 'localhost',
	"port": int(os.environ['DB_PORT']) if 'DB_PORT' in os.environ else 3306,
	"user": os.environ['DB_USER'] if 'DB_USER' in os.environ else 'progkeeper',
	"pass": os.environ['DB_PASSWORD'] if 'DB_PASSWORD' in os.environ else 'change_me',
	"dbname": os.environ['DB_DATABASE'] if 'DB_DATABASE' in os.environ else 'progkeeper'
}

def is_database_ready(cursor:mariadb.Cursor) -> bool:
	cursor.execute("SHOW TABLES")
	return cursor.fetchone() != None

class DatabaseSession:
	def __init__(self):
		# TODO: catch connection errors
		self.connection:mariadb.Connection = mariadb.connect(
			host=SQL_CREDENTIALS['host'],
			port=SQL_CREDENTIALS['port'],
			user=SQL_CREDENTIALS['user'],
			password=SQL_CREDENTIALS['pass'],
			database=SQL_CREDENTIALS['dbname']
		)
		self.cursor:mariadb.Cursor = self.connection.cursor()

	def __enter__(self):
		return self

	def __exit__(self, exception_type: BaseException|None, exception_value: BaseException|None, traceback: TracebackType|None) -> None:
		self.connection.close()

	def get_assoc(self, query: str, params: list = []) -> list[dict[str, typing.Any]]:
		""" Execute a query and return results as a list of associative arrays (dicts). """
		self.cursor.execute(query, params)
		columns:list[str] = [col[0] for col in self.cursor.description if isinstance(col[0], str)] if self.cursor.description else []
		results:list[dict[str, typing.Any]] = []
		for row in self.cursor.fetchall():
			results.append({columns[i]: row[i] for i in range(len(columns))})
		return results
	
	def easy_insert(self, table:str, column_values:dict[str, typing.Any]):
		""" Wrapper for INSERT statements to reduce dev effort.
		Just be aware this does use format strings, which in theory opens up injection attacks.
		Be sure the *table* variable and *column_values* **keys** are only used internally! """
		columns = [k for k in column_values.keys()]
		values = [v for v in column_values.values()]
		return self.cursor.execute(f"""
			INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join(['?' for c in columns])})
		""", values)