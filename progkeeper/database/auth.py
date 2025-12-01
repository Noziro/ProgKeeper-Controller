import bcrypt # password hashing
import secrets # ID generation
import json
from progkeeper.database.common import DatabaseSession
from datetime import datetime, timezone

def generate_session_id() -> str:
	""" Generate a new session identifier. """
	session_id = secrets.token_hex(32)
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
		

def hash_password(password: str) -> str:
	""" Hash the password for secure storage. """
	bytes:bytes = password.encode('utf-8')
	salt = bcrypt.gensalt()
	hash = bcrypt.hashpw(bytes, salt)
	return hash

def verify_password(plaintext_password: str, hashed_password: str) -> bool:
	""" Checks a plaintext password against a hashed password. """
	return bcrypt.checkpw(plaintext_password.encode('utf-8'), hashed_password.encode('utf-8'))



def create_user(username: str, password: str, nickname: str | None = None) -> int:
	""" Create a new user in the database. Returns the new user's ID. """
	valid_username_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
	
	if len(password) < 6 or len(password) > 72:
		raise ValueError("Password must be between 6 and 72 characters long.")
	standardised_name = username.strip().lower()
	if len(standardised_name) < 1 or len(standardised_name) > 50:
		raise ValueError("Username must be between 1 and 50 characters.")
	for char in standardised_name:
		if char not in valid_username_chars:
			raise ValueError("Username contains invalid characters.")
	
	hashed_password = hash_password(password)
	if username != standardised_name and nickname is None:
		nickname = username
	nickname = nickname.strip() if nickname != None else None
	
	with DatabaseSession() as db:
		db.cursor.execute(
			"SELECT id FROM users WHERE username = ?",
			[standardised_name]
		)
		if db.cursor.fetchone() is not None:
			raise ValueError("Username already exists.")
		
		db.cursor.execute(
			"INSERT INTO users (username, password, nickname) VALUES (?, ?, ?)",
			[standardised_name, hashed_password, nickname]
		)
		db.connection.commit()
		return db.cursor.lastrowid



def create_session(username: str, password: str, ip_address: str) -> str:
	""" Verify user credentials and return user ID if valid, otherwise 0. """
	username = username.strip().lower()
	now_utc:int = int(datetime.now(timezone.utc).timestamp())
	expiry_utc:int = now_utc + (60 * 60 * 24 * 14)  # Sessions last 14 days without renewal
	ip_string:str = json.dumps([ip_address])
	with DatabaseSession() as db:
		db.cursor.execute(
			"SELECT id, password FROM users WHERE username = ?",
			[username]
		)
		row = db.cursor.fetchone()
		if row is None:
			raise ValueError("Invalid username.")
		
		user_id, hashed_password = row
		if not verify_password(password, hashed_password):
			raise ValueError("Invalid password.")
		
		session_id:str = generate_session_id()
		db.cursor.execute(
			"INSERT INTO sessions (id, user_id, user_ip, expiry) VALUES (?, ?, ?, ?)",
			[session_id, user_id, ip_string, expiry_utc]
		)
		db.connection.commit()
		return session_id