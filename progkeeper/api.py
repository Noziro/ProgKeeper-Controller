from fastapi import FastAPI, HTTPException, Request, status, Depends, UploadFile, BackgroundTasks
from pydantic import BaseModel
from typing import Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from datetime import datetime

import progkeeper.database.auth as auth
import progkeeper.database.auth as auth
import progkeeper.database.user as user
import progkeeper.database.media as media
import progkeeper.database.export as export

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
def login(user: user.Login, request: Request):
	""" Begin a new user session (login). """
	try:
		session_id = auth.create_session(user.username, user.password, request.client.host)
		return APIResult("Created session successfully.", {"session_id": session_id})
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create session: {e}")



# User management

@app.get("/user/get/new_users")
def get_new_users(quantity: int = 10):
	""" Get the most recently signed up users. """
	data:list = user.get_new_users(quantity)
	return APIResult("Fetched user info successfully.", {"user_set": data})

@app.get("/user/get/{user_id}")
def get_user(user_id: int):
	""" Get info about a user. """
	user_data:dict = user.get_user_info(user_id)
	if user_data == {}:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
	return APIResult("Fetched user info successfully.", {"user": user_data})

@app.post("/user/update")
def update_user(new_data: user.Account, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Update user info. """

	user_id = auth.get_user_id_from_session(http_auth.credentials)
	updated = user.update_user(user_id, new_data)

	if not updated:
		return APIResult('No updates to user performed as all values are identical.', {'user_id': user_id})
	return APIResult('Updated user successfully.', {'user_id': user_id})

# TODO: add an admin endpoint for changing other users' data
#@app.post("/user/update/{user_id}")
#def update_user(target_user_id: int, new_data: user.Account, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	
# add extra confirmation step to prevent accidentally querying this endpoint
class UserDeleteConfirmation(BaseModel):
	obliterate_this_user: bool

@app.delete("/user/delete")
def delete_user(confirmation: UserDeleteConfirmation, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Permanently delete user. """
	
	user_id = auth.get_user_id_from_session(http_auth.credentials)

	deleted_data = user.obliterate_user(user_id)
	if deleted_data == {}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete user. They may not exist.")
	elif 'deleted_user_id' not in deleted_data:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete user, although some deletions succeeded.", data=deleted_data)
	return APIResult("Deleted user successfully.", deleted_data)

# TODO: add an admin endpoint for deleting other users'
#@app.delete("/user/delete/{user_id}")
#def delete_user(user_id: int, confirmation: UserDeleteConfirmation, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):

@app.post("/user/create", status_code=status.HTTP_201_CREATED)
def register(user: user.Registration):
	""" Register a new user. """
	try:
		user_id = auth.create_user(user.username, user.password, user.nickname)
		return APIResult("Created user successfully.", {"user_id": user_id})
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create user: {e}")

@app.post("/user/import", status_code=status.HTTP_202_ACCEPTED)
def import_internal_data(http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Import data that was exported directly from ProgKeeper. """
	return APIResult("Not implemented yet.")

from progkeeper.tasks.myanimelist import handle_file as handle_myanimelist
@app.post("/user/import/myanimelist", status_code=status.HTTP_202_ACCEPTED)
async def import_myanimelist_data(file: UploadFile, collection_id: int, tasks: BackgroundTasks, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Import data from MyAnimeList XML. """

	user_id = auth.get_user_id_from_session(http_auth.credentials)
	collection_data = media.get_collection_info(collection_id)
	if collection_data['user_id'] != user_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Specified collection does not belong to you.')
	
	tasks.add_task(handle_myanimelist, file, user_id, collection_id)

	return APIResult('Queued job for processing.')

@app.post("/user/import/anilist", status_code=status.HTTP_202_ACCEPTED)
def import_anilist_data(http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Import data from AniList GDPR files. """
	return APIResult("Not implemented yet.")

@app.get("/user/export")
def export_internal_data(http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]) -> JSONResponse:
	""" Export all data from your user account. """
	# TODO: add different export types i.e myanimelist xml
	user_id = auth.get_user_id_from_session(http_auth.credentials)
	exported_data = export.as_progkeeper(user_id)

	if exported_data == {}:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to export data."
		)

	response = JSONResponse(content=exported_data)
	datestamp = datetime.now().strftime("%Y-%m-%d")
	response.headers["Content-Disposition"] = f"attachment; filename=progkeeper_export_{datestamp}.json"
	return response

@app.get("/user/export/myanimelist")
def export_myanimelist_data(http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Export data to MyAnimeList XML. """
	return APIResult("Not implemented yet.")



# Media management

@app.post("/media/create", status_code=status.HTTP_201_CREATED)
def create_media(media_item: media.MediaItem, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Create a media item. """
	user_id:int = auth.get_user_id_from_session(http_auth.credentials)
	media_item.user_id = user_id
	if 'collection_id' not in media_item.model_fields_set:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='missing required field collection_id')
	collection_data = media.get_collection_info(media_item.collection_id)
	if collection_data == {}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='specified collection_id does not exist')
	if collection_data['user_id'] != user_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
	
	media_id:int = media.create_media_item(media_item)
	if media_id == 0:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create media.')
	return APIResult('Created media successfully.', {'media_id': media_id})

@app.get("/media/get/by/collection/{collection_id}")
def get_media_by_collection(collection_id: int, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Get info about a media item. """
	# TODO: add LIMIT support (pagination)
	user_id = auth.get_user_id_from_session(http_auth.credentials)
	collection = media.get_collection_info(collection_id)
	if collection == {}:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection does not exist.")
	if collection["user_id"] != user_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
	
	return APIResult('Fetched collection media items successfully.', {'media_set': media.get_media_info_by_collection(collection_id)})

@app.get("/media/get/{media_id}")
def get_media(media_id: int):
	""" Get info about a media item. """
	data:dict = media.get_media_info(media_id)
	if data == {}:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
	return APIResult("Fetched media info successfully.", {'media': data})

@app.post("/media/update/{media_id}")
def update_media(media_id: int, new_data: media.MediaItem, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Update info about a media item. """
	if len(new_data.model_fields_set) == 0:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Must provide at least 1 change.')
	
	old_data = media.get_media_info(media_id)
	if old_data == {}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
	if old_data['user_id'] != auth.get_user_id_from_session(http_auth.credentials):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
	
	updated = media.update_media(media_id, new_data)
	if not updated:
		return APIResult('No updates to media performed as all values are identical.', {'media_id': media_id})
	return APIResult('Updated media successfully.', {'media_id': media_id})

@app.delete("/media/delete/{media_id}")
def delete_media(media_id: int, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Delete a media item. """
	user_id:int = auth.get_user_id_from_session(http_auth.credentials) or 0
	media_data = media.get_media_info(media_id)
	if media_data == {}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Media does not exist.')
	if media_data['user_id'] != user_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
	deleted = media.delete_media(media_id)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	return APIResult("Deleted media successfully", {'deleted_media_id': media_id})



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

@app.get("/collection/get/by/user/{user_id}")
def get_collection_by_user(user_id: int, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Get all collections belonging to a user. """
	# TODO: add LIMIT support (pagination)
	user_id = auth.get_user_id_from_session(http_auth.credentials)
	target_user = user.get_user_info(user_id)
	if target_user == {}:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist.")
	
	return APIResult('Fetched collections successfully.', {'collection_set': media.get_collection_info_by_user(user_id)})

@app.post("/collection/update/{collection_id}", description="Updates info about a collection. Please see /collection/create endpoint for valid body fields. Invalid fields will be ignored.")
def update_collection(collection_id: int, new_data: media.Collection, http_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bridge)]):
	""" Update info about a collection. """

	if len(new_data.model_fields_set) == 0:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Must provide at least 1 change.')
	
	old_data = media.get_collection_info(collection_id)
	if old_data == {}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
	if old_data['user_id'] != auth.get_user_id_from_session(http_auth.credentials):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
	
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