from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from progkeeper.database.auth import create_user

app = FastAPI(
	title="ProgKeeper API",
	version="0.1.0",
	description="API for controlling all ProgKeeper functions, including frontend data and backend tasks.",
)

class APIResult:
	def __init__(self, ok:bool, message:str, data = None):
		if not isinstance(ok, bool):
			raise ValueError("APIResult.ok must be a boolean value")
		if not isinstance(message, str):
			raise ValueError("APIResult.message must be a string")
		self.ok = ok
		self.message = message
		self.data = {} if data is None else data

class UserLogin(BaseModel):
	username: str
	password: str

class UserRegister(UserLogin):
	nickname: str | None = None



# Meta information

@app.get("/")
def status():
	return APIResult(True, "API is running. Visit /docs for API documentation.")



# Session management

@app.get("/session/end")
def logout():
	""" Logout the current user session. """
	return APIResult(False, "Not implemented yet.")

@app.get("/session/end/all")
def logout_all():
	""" Logout from all sessions belonging to this user. """
	return APIResult(False, "Not implemented yet.")

@app.post("/session/create")
def login(user: UserLogin):
	""" Begin a new user session (login). """
	return APIResult(False, "Not implemented yet.")



# User management

@app.get("/user/get/{user_id}")
def get_user(user_id: int):
	""" Get info about a user. """
	return APIResult(False, "Not implemented yet.")

@app.post("/user/update/{user_id}")
def update_user(user_id: int):
	""" Update user info. """
	return APIResult(False, "Not implemented yet.")

@app.delete("/user/delete/{user_id}")
def delete_user(user_id: int):
	""" Delete user. """
	return APIResult(False, "Not implemented yet.")

@app.post("/user/create")
def register(user: UserRegister):
	""" Register a new user. """
	try:
		user_id = create_user(user.username, user.password, user.nickname)
		return APIResult(True, "Created user successfully.", {"user_id": user_id})
	except ValueError as e:
		return APIResult(False, f"Failed to create user: {e}")

@app.post("/user/import")
def import_data():
	""" Import a variety of data to your user account. """
	return APIResult(False, "Not implemented yet.")

@app.get("/user/export")
def export_data():
	""" Import a variety of data to your user account. """
	return APIResult(False, "Not implemented yet.")



# Media management

@app.post("/media/create")
def create_media():
	""" Create a media item. """
	return APIResult(False, "Not implemented yet.")

@app.get("/media/get/{media_id}")
def get_media(media_id: int):
	""" Get info about a media item. """
	return APIResult(False, "Not implemented yet.")

@app.post("/media/update/{media_id}")
def update_media(media_id: int):
	""" Update info about a media item. """
	return APIResult(False, "Not implemented yet.")

@app.delete("/media/delete/{media_id}")
def delete_media(media_id: int):
	""" Delete a media item. """
	return APIResult(False, "Not implemented yet.")



# Collection management

@app.post("/collection/create")
def create_collection():
	""" Create a collection. """
	return APIResult(False, "Not implemented yet.")

@app.get("/collection/get/{collection_id}")
def get_media(collection_id: int):
	""" Get info about a collection. """
	return APIResult(False, "Not implemented yet.")

@app.post("/collection/update/{collection_id}")
def update_media(collection_id: int):
	""" Update info about a collection. """
	return APIResult(False, "Not implemented yet.")

@app.delete("/collection/delete/{collection_id}")
def delete_media(collection_id: int):
	""" Delete a collection. """
	return APIResult(False, "Not implemented yet.")