from fastapi import FastAPI, HTTPException, Request, status, Depends
from pydantic import BaseModel
from typing import Annotated
from enum import Enum
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from progkeeper.database.auth import \
	create_user as auth_create_user, \
	create_session as auth_create_session, \
	delete_session as auth_delete_session, \
	validate_session_id, \
	refresh_session

app = FastAPI(
	title="ProgKeeper API",
	version="0.1.0",
	description="API for controlling all ProgKeeper functions, including frontend data and backend tasks.",
)

UNAUTHENTICATED = HTTPException(
	status_code=status.HTTP_401_UNAUTHORIZED,
	detail="Invalid or missing authentication credentials.",
	headers={"WWW-Authenticate": "Bearer"},
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

class Status(Enum):
	current = 'current'
	completed = 'completed'
	paused = 'paused'
	dropped = 'dropped'
	planned = 'planned'

class MediaItem(BaseModel):
	name: str
	collection_id: int
	status: Status = Status.planned
	score: int | None = None
	image: str | None = None
	description: str | None = None
	comments: str | None = None	
	count_total: int = 0
	count_progress: int = 0
	count_rewatched: int = 0
	user_started_at: str | None = None
	user_finished_at: str | None = None
	media_started_at: str | None = None
	media_finished_at: str | None = None
	link_anilist: str | None = None
	link_myanimelist: str | None = None
	link_imdb: str | None = None
	link_tmdb: str | None = None
	adult: bool = False
	favourite: bool = False
	private: bool = False
	deleted: bool = False



SECURITY_SCHEME = HTTPBearer()

def security_bridge(http_auth: Annotated[HTTPAuthorizationCredentials, Depends(SECURITY_SCHEME)], request: Request) -> HTTPAuthorizationCredentials:
	""" Serves as a bridge between FastAPI security dependencies and functions I actually enjoy writing. """

	if not isinstance(http_auth, HTTPAuthorizationCredentials):
		raise ValueError("Invalid credentials object.")
	
	session_id = http_auth.credentials
	if not validate_session_id(session_id):
		raise UNAUTHENTICATED
	
	print(refresh_session(session_id, request.client.host))

	return http_auth


# Meta information

@app.get("/")
def status():
	return APIResult(True, "API is running. Visit /docs for API documentation.")



# Session management

@app.get("/session/end")
def logout(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Logout the current user session. """
	#deleted = auth_delete_session()
	return APIResult(False, "Not implemented yet.")

@app.get("/session/end/all")
def logout_all(request: Request):
	""" Logout from all sessions belonging to this user. """
	return APIResult(False, "Not implemented yet.")

@app.post("/session/create")
def login(user: UserLogin, request: Request):
	""" Begin a new user session (login). """
	try:
		session_id = auth_create_session(user.username, user.password, request.client.host)
		return APIResult(True, "Created session successfully.", {"session_id": session_id})
	except ValueError as e:
		return APIResult(False, f"Failed to create session: {e}")



# User management

@app.get("/user/get/{user_id}")
def get_user(user_id: int):
	""" Get info about a user. """
	return APIResult(False, "Not implemented yet.")

@app.post("/user/update/{user_id}")
def update_user(user_id: int, credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Update user info. """
	
	return APIResult(False, "Not implemented yet.")

@app.delete("/user/delete/{user_id}")
def delete_user(user_id: int, credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Delete user. """
	return APIResult(False, "Not implemented yet.")

@app.post("/user/create")
def register(user: UserRegister):
	""" Register a new user. """
	try:
		user_id = auth_create_user(user.username, user.password, user.nickname)
		return APIResult(True, "Created user successfully.", {"user_id": user_id})
	except ValueError as e:
		return APIResult(False, f"Failed to create user: {e}")

@app.post("/user/import")
def import_data(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Import a variety of data to your user account. """
	return APIResult(False, "Not implemented yet.")

@app.get("/user/export")
def export_data(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Import a variety of data to your user account. """
	return APIResult(False, "Not implemented yet.")



# Media management

@app.post("/media/create")
def create_media(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Create a media item. """
	return APIResult(False, "Not implemented yet.")

@app.get("/media/get/{media_id}")
def get_media(media_id: int):
	""" Get info about a media item. """
	return APIResult(False, "Not implemented yet.")

@app.post("/media/update/{media_id}")
def update_media(media_id: int, credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Update info about a media item. """
	return APIResult(False, "Not implemented yet.")

@app.delete("/media/delete/{media_id}")
def delete_media(media_id: int, credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Delete a media item. """
	return APIResult(False, "Not implemented yet.")



# Collection management

@app.post("/collection/create")
def create_collection(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Create a collection. """
	return APIResult(False, "Not implemented yet.")

@app.get("/collection/get/{collection_id}")
def get_collection(collection_id: int):
	""" Get info about a collection. """
	return APIResult(False, "Not implemented yet.")

@app.post("/collection/update/{collection_id}")
def update_collection(collection_id: int, credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Update info about a collection. """
	return APIResult(False, "Not implemented yet.")

@app.delete("/collection/delete/{collection_id}")
def delete_collection(collection_id: int, credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Delete a collection. """
	return APIResult(False, "Not implemented yet.")