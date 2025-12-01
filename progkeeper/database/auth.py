import bcrypt
from progkeeper.database.common import DatabaseSession

def hash_password(password: str) -> str:
	""" Hash the password for secure storage. """
	bytes:bytes = password.encode('utf-8')
	salt = bcrypt.gensalt()
	hash = bcrypt.hashpw(bytes, salt)
	return hash

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