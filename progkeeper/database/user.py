from progkeeper.database.common import DatabaseSession
from typing import Any
from typing_extensions import Self
from pydantic import BaseModel, field_validator, model_validator, ModelWrapValidatorHandler
from zoneinfo import ZoneInfo

class Login(BaseModel):
	username: str = ''
	password: str = ''

	@field_validator('username')
	@classmethod
	def validate_username(cls, value: str) -> str:
		valid_username_chars:str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
		value = value.strip().lower()
		if len(value) < 1 or len(value) > 50:
			raise ValueError("Username must be between 1 and 50 characters.")
		for char in value:
			if char not in valid_username_chars:
				raise ValueError("Username contains invalid characters.")
		
		return value

	@field_validator('password')
	@classmethod
	def validate_password(cls, value: str) -> str:
		if len(value) < 6 or len(value) > 72:
			raise ValueError("Password must be between 6 and 72 characters long.")
	
		return value

class Registration(Login):
	nickname: str | None = None

	@model_validator(mode='wrap')
	@classmethod
	def nickname_from_username(cls, data: Any, handler: ModelWrapValidatorHandler) -> Self:
		""" If `username` is set and `nickname` is not set, stores the raw value of `username` and transfers it to `nickname`. """
		if 'username' not in data:
			return handler(data)
		
		nickname = data['nickname'].strip() if 'nickname' in data and isinstance(data['nickname'], str) and data['nickname'].strip() != '' else None
		if nickname != None:
			return handler(data)
		
		data['nickname'] = data['username']

		return handler(data)

	@field_validator('nickname')
	@classmethod
	def validate_nickname(cls, value) -> str|None:
		if not isinstance(value, str):
			return None
		
		if len(value) < 1 or len(value) > 50:
			raise ValueError("Nickname must be between 1 and 50 characters.")
		
		return value

class Account(Registration):
	#profile_image:
	#banner_image:
	about: str = ''
	timezone: str = 'UTC'

	@field_validator('timezone')
	@classmethod
	def validate_timezone(cls, value: str) -> str:
		ZoneInfo(value)
		return value


def get_user_info(user_id: int) -> dict[str, Any]:
	""" Get information about a user by their ID. Returns an empty dict if not found. """
	with DatabaseSession() as db:
		rows = db.get_assoc(
			"SELECT id, username, nickname, about, timezone FROM users WHERE id = ?",
			[user_id]
		)
		return {} if len(rows) == 0 else rows[0]

def get_new_users(quantity: int) -> list[dict[str, Any]]:
	with DatabaseSession() as db:
		rows = db.get_assoc(
			"SELECT id, username, nickname FROM users ORDER BY created_at DESC LIMIT ?",
			[quantity]
		)
		return [] if len(rows) == 0 else rows

# imports specifically for obliterate_user
from progkeeper.database.auth import delete_all_sessions_for_user

def obliterate_user(user_id: int) -> dict[str, Any]:
	""" Deletes a user and all of their content. "To shreds, you say?"
	
	Returns a dictionary containing data of all performed changes, with the primary attribute {"deleted_user_id": user_id} """
	
	data:dict[str, Any] = {}

	# remove all references to user ID in other tables to allow user deletion
	# TODO: as other functions are added such as media and collections, you will have to delete these too.
	data['deleted_session_count'] = delete_all_sessions_for_user(user_id)

	with DatabaseSession() as db:
		db.cursor.execute(
			"DELETE FROM users WHERE id = ?",
			[user_id]
		)
		db.connection.commit()
		if db.cursor.rowcount > 0:
			data['deleted_user_id'] = user_id
	
	return data
	
def update_user(user_id: int, user_data: Account) -> bool:
	# TODO: consider returning changed fields instead of bool

	if not isinstance(user_data, Account):
		raise ValueError('user_data must be instance of Account class')

	with DatabaseSession() as db:
		# this line is very important! if you do not sure model_dump() with exclude_unset=True
		# (or an equivalent expression) then you may end up overwriting values that were not requested
		# to be overwritten!
		data:dict[str, Any] = user_data.model_dump(exclude_unset=True)

		# prevent any changes to reference columns
		if 'user_id' in data:
			del data['user_id']
		if 'id' in data:
			del data['id']
		if 'username' in data:
			del data['username']

		db.easy_update('users', data, ('id', user_id))
		successful:bool = db.cursor.rowcount > 0
		db.connection.commit()
		return successful