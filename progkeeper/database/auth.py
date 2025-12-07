import bcrypt # password hashing
import secrets # ID generation
import json
from progkeeper.database.common import DatabaseSession
from datetime import datetime, timezone



# Utility functions

def now_utc() -> int:
	""" Returns the current UTC time as a Unix timestamp. """
	return int(datetime.now(timezone.utc).timestamp())



# Session functions

def validate_session_id(session_id: str) -> bool:
	""" Check if the provided session ID exists and is not expired. """

	if not isinstance(session_id, str):
		raise ValueError("Session ID must be a string.")
	
	if len(session_id) == 0:
		return False
	with DatabaseSession() as db:
		db.cursor.execute(
			"SELECT id FROM sessions WHERE id = ? AND expiry > ?",
			[session_id, now_utc()]
		)
		return db.cursor.fetchone() is not None

	return False

def refresh_session(session_id: str, user_ip: str) -> bool:
	""" Refresh the expiry time of a session and log any new IPs used to access it. """
	updated_expiry:int = now_utc() + (60 * 60 * 24 * 14)  # Sessions last 14 days without renewal
	with DatabaseSession() as db:
		db.cursor.execute(
			"SELECT expiry, user_ip FROM sessions WHERE id = ?",
			[session_id]
		)
		row:tuple = db.cursor.fetchone()
		if row is None:
			return False
		if not isinstance(row, tuple):
			raise TypeError('cursor.fetchone() provided an unexpected value type')
		current_expiry:int = row[0]
		ip_json:str = row[1]
		if current_expiry < now_utc():
			return False  # Session already expired
		ip_list:list = json.loads(ip_json)
		if user_ip not in ip_list:
			ip_list.append(user_ip)
		updated_ip_json:str = json.dumps(ip_list)

		db.cursor.execute(
			"UPDATE sessions SET expiry = ?, user_ip = ? WHERE id = ?",
			[updated_expiry, updated_ip_json, session_id]
		)
		db.connection.commit()
		if not isinstance(db.cursor.rowcount, int):
			raise TypeError('cursor.rowcount provided an unexpected value type')
		if db.cursor.rowcount > 0:
			return True
	return False

def generate_session_id() -> str:
	""" Generate a new session identifier. """
	session_id:str = secrets.token_hex(32)
	with DatabaseSession() as db:
		while session_id_is_in_use(db.cursor, session_id) == True:
			session_id = secrets.token_hex(32)
	return session_id

def session_id_is_in_use(cursor, session_id: str) -> bool:
	""" Check if the session ID is already in use. """
	cursor.execute(
		"SELECT id FROM sessions WHERE id = ?",
		[session_id]
	)
	return cursor.fetchone() is not None

def get_user_id_from_session(session_id: str) -> int:
	""" Get the user ID associated with a session ID. Raises a ValueError if not found. """
	with DatabaseSession() as db:
		db.cursor.execute(
			"SELECT user_id FROM sessions WHERE id = ?",
			[session_id]
		)
		row:tuple = db.cursor.fetchone()
		if row is None:
			raise ValueError('session not found in database')
		if not isinstance(row, tuple):
			raise TypeError('cursor.fetchone() provided an unexpected value type')
		if not isinstance(row[0], int):
			raise TypeError('mariadb column "user_id" provided an unexpected value type')
		return row[0]



# Password functions

def hash_password(password: str) -> str:
	""" Hash the password for secure storage. """
	password_bytes:bytes = password.encode('utf-8')
	salt:bytes = bcrypt.gensalt()
	hash:bytes = bcrypt.hashpw(password_bytes, salt)
	return hash.decode('utf-8')

def verify_password(plaintext_password: str, hashed_password: str) -> bool:
	""" Checks a plaintext password against a hashed password. """
	return bcrypt.checkpw(plaintext_password.encode('utf-8'), hashed_password.encode('utf-8'))



# Worker functions (called directly by API endpoints)

def create_user(username: str, unhashed_password: str, nickname: str | None = None) -> int:
	""" Create a new user in the database. Returns the new user's ID. """
	
	hashed_password:str = hash_password(unhashed_password)
	
	with DatabaseSession() as db:
		db.cursor.execute(
			"SELECT id FROM users WHERE username = ?",
			[username]
		)
		if db.cursor.fetchone() is not None:
			raise ValueError("Username already exists.")
		
		db.cursor.execute(
			"INSERT INTO users (username, password, nickname) VALUES (?, ?, ?)",
			[username, hashed_password, nickname]
		)
		db.connection.commit()
		if not isinstance(db.cursor.lastrowid, int):
			raise TypeError('cursor.lastrowid provided an unexpected value type')
		return db.cursor.lastrowid



def create_session(username: str, unhashed_password: str, ip_address: str) -> str:
	""" Verify user credentials and return user ID if valid, otherwise 0. """
	expiry_utc:int = now_utc() + (60 * 60 * 24 * 14)  # Sessions last 14 days without renewal
	ip_string:str = json.dumps([ip_address])
	with DatabaseSession() as db:
		db.cursor.execute(
			"SELECT id, password FROM users WHERE username = ?",
			[username]
		)
		row:tuple = db.cursor.fetchone()
		if row is None:
			raise ValueError("Invalid username.")
		if not isinstance(row, tuple):
			raise TypeError('cursor.fetchone() provided an unexpected value type')
		
		user_id, hashed_password = row
		if not verify_password(unhashed_password, hashed_password):
			raise ValueError("Invalid password.")
		
		session_id:str = generate_session_id()
		db.cursor.execute(
			"INSERT INTO sessions (id, user_id, user_ip, expiry) VALUES (?, ?, ?, ?)",
			[session_id, user_id, ip_string, expiry_utc]
		)
		db.connection.commit()
		return session_id
	

def delete_session(session_id: str) -> str:
	""" Delete a session from the database. """
	with DatabaseSession() as db:
		db.cursor.execute(
			"DELETE FROM sessions WHERE id = ?",
			[session_id]
		)
		db.connection.commit()
		if db.cursor.rowcount > 0:
			return session_id
	return ''

def delete_all_sessions_for_user(user_id_or_session: int|str) -> int:
	""" Delete all sessions for a given user ID. Returns the number of deleted sessions. """

	if isinstance(user_id_or_session, str):
		try:
			user_id:int = get_user_id_from_session(user_id_or_session)
		except ValueError:
			return 0
	elif isinstance(user_id_or_session, int):
		user_id:int = user_id_or_session
	else:
		raise ValueError("user_id_or_session must be an integer user ID or a string session ID.")
	
	with DatabaseSession() as db:
		db.cursor.execute(
			"DELETE FROM sessions WHERE user_id = ?",
			[user_id]
		)
		db.connection.commit()
		return db.cursor.rowcount
	return 0