from fastapi import FastAPI, HTTPException, Request, status, Depends, Body
from pydantic import BaseModel
from typing import Annotated, Any
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import progkeeper.database.auth as auth

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
	def __init__(self, detail: str, data: dict = {}):
		self.detail = detail
		self.data = data

class UserLogin(BaseModel):
	username: str
	password: str

class UserRegister(UserLogin):
	nickname: str | None = None



# Authenticate functions and data

SECURITY_SCHEME = HTTPBearer()

def security_bridge(http_auth: Annotated[HTTPAuthorizationCredentials, Depends(SECURITY_SCHEME)], request: Request) -> HTTPAuthorizationCredentials:
	""" Serves as a bridge between FastAPI security dependencies and functions I actually enjoy writing. """

	if not isinstance(http_auth, HTTPAuthorizationCredentials):
		raise ValueError("Invalid credentials object.")
	
	session_id = http_auth.credentials
	if not auth.validate_session_id(session_id):
		raise UNAUTHENTICATED
	
	auth.refresh_session(session_id, request.client.host)

	return http_auth

def only_allow_self_action(attempted_user_id:int, http_auth: HTTPAuthorizationCredentials) -> None:
	""" Determines if a user is performing an action upon their own user ID.	 
	If they are not, this function raises an HTTPException.
	
	Uses HTTP authentication to determine this."""

	if not isinstance(http_auth, HTTPAuthorizationCredentials):
		raise ValueError('http_auth must be an instance of HTTPAuthorizationCredentials')
	if not isinstance(attempted_user_id, int):
		raise ValueError('attempted_user_id must be an int')

	user_id:int = auth.get_user_id_from_session(http_auth.credentials)

	if user_id != attempted_user_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Attempted to perform an action for another user.')
	
	return



# Meta information

@app.get("/")
def api_status():
	return APIResult("API is running. Visit /docs for API documentation.")



# Session management

@app.get("/session/end")
def logout(http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Logout the current user session. """
	deleted_id:str = auth.delete_session(http_auth.credentials)
	if deleted_id == '':
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete session. It may not exist.")
	return APIResult("Deleted session successfully.", {"deleted_session_id": deleted_id})

@app.get("/session/end/all")
def logout_all(http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Logout from all sessions belonging to this user. """
	deleted_count:int = auth.delete_all_sessions_for_user(http_auth.credentials)
	return APIResult("Deleted all sessions for user.", {"deleted_session_count": deleted_count})

@app.post("/session/create")
def login(user: UserLogin, request: Request):
	""" Begin a new user session (login). """
	try:
		session_id = auth.create_session(user.username, user.password, request.client.host)
		return APIResult("Created session successfully.", {"session_id": session_id})
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create session: {e}")



# User management

import progkeeper.database.user as user

@app.get("/user/get/{user_id}")
def get_user(user_id: int):
	""" Get info about a user. """
	user_data:dict = user.get_user_info(user_id)
	if user_data == {}:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
	return APIResult("Fetched user info successfully.", {"user": user_data})

@app.post("/user/update/{user_id}")
def update_user(user_id: int, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Update user info. """
	
	return APIResult("Not implemented yet.")

# add extra confirmation step to prevent accidentally querying this endpoint
class UserDeleteConfirmation(BaseModel):
	obliterate_this_user: bool

@app.delete("/user/delete/{user_id}")
def delete_user(user_id: int, confirmation: UserDeleteConfirmation, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Permanently delete user. """
	
	# TODO: allow admins to delete other users
	only_allow_self_action(user_id, http_auth)

	deleted_data = user.obliterate_user(user_id)
	if deleted_data == {}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete user. They may not exist.")
	elif 'deleted_user_id' not in deleted_data:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete user, although some deletions succeeded.", data=deleted_data)
	return APIResult("Deleted user successfully.", deleted_data)


@app.post("/user/create", status_code=status.HTTP_201_CREATED)
def register(user: UserRegister):
	""" Register a new user. """
	try:
		user_id = auth.create_user(user.username, user.password, user.nickname)
		return APIResult("Created user successfully.", {"user_id": user_id})
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create user: {e}")

@app.post("/user/import", status_code=status.HTTP_202_ACCEPTED)
def import_data(http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Import a variety of data to your user account. """
	return APIResult("Not implemented yet.")

@app.get("/user/export")
def export_data(http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Import a variety of data to your user account. """
	return APIResult("Not implemented yet.")



# Media management

import progkeeper.database.media as media

@app.post("/media/create", status_code=status.HTTP_201_CREATED)
def create_media(media_item: media.MediaItem, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Create a media item. """
	# TODO: validate user_id
	return media.create_media_item(media_item)

@app.get("/media/get/{media_id}")
def get_media(media_id: int):
	""" Get info about a media item. """
	return APIResult("Not implemented yet.")

@app.post("/media/update/{media_id}")
def update_media(media_id: int, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Update info about a media item. """
	return APIResult("Not implemented yet.")

@app.delete("/media/delete/{media_id}")
def delete_media(media_id: int, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Delete a media item. """
	return APIResult("Not implemented yet.")



# Collection management

@app.post("/collection/create", status_code=status.HTTP_201_CREATED)
def create_collection(collection: media.Collection, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Create a collection. """
	# Override specified user_id with the currently authenticated user
	collection.user_id = auth.get_user_id_from_session(http_auth.credentials)
	try:
		collection_id = media.create_collection(collection)
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.__str__())
	return APIResult("Created collection successfully.", {'collection_id': collection_id})

@app.get("/collection/get/{collection_id}")
def get_collection(collection_id: int):
	""" Get info about a collection. """
	data:dict = media.get_collection_info(collection_id)
	if data == {}:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
	return APIResult("Fetched collection info successfully.", {'collection': data})

@app.post("/collection/update/{collection_id}", description="Updates info about a collection. Please see /collection/create endpoint for valid body fields. Invalid fields will be ignored.")
def update_collection(collection_id: int, new_data: media.Collection, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Update info about a collection. """

	if len(new_data.model_fields_set) == 0:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Must provide at least 1 change.')
	
	old_data = media.get_collection_info(collection_id)
	if old_data == {}:
		return HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
	if old_data['user_id'] != auth.get_user_id_from_session(http_auth.credentials):
		return HTTPException(status_code=status.HTTP_403_FORBIDDEN)
	
	updated = media.update_collection(collection_id, new_data)
	if not updated:
		return APIResult('No updates to collection performed as all values are identical.', {'collection_id': collection_id})
	return APIResult('Updated collection successfully.', {'collection_id': collection_id})

@app.delete("/collection/delete/{collection_id}")
def delete_collection(collection_id: int, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Delete a collection. """
	user_id:int = auth.get_user_id_from_session(http_auth.credentials) or 0
	collection_data = media.get_collection_info(collection_id)
	if collection_data == {}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Collection does not exist.')
	if collection_data['user_id'] != user_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
	deleted = media.delete_collection(collection_id)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	return APIResult("Deleted collection successfully", {'deleted_collection_id': collection_id})