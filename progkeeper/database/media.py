from pydantic import BaseModel, field_validator
from enum import Enum
from typing import Any, Annotated
from progkeeper.database.common import DatabaseSession
from datetime import date
import re



class RatingSystems(Enum):
	three_star = 3
	five_star = 5
	ten_point = 10
	twenty_point = 20
	hundred_point = 100

class Status(Enum):
	current = 'current'
	completed = 'completed'
	paused = 'paused'
	dropped = 'dropped'
	planned = 'planned'

class MediaTypes(Enum):
	single = 'single'
	many = 'many'

class MediaItem(BaseModel):
	name: str = 'Untitled Media'
	collection_id: int = 0
	type: str = MediaTypes.many.value
	user_id: int | None = None
	status: str = Status.planned.value
	score: int | None = None
	image: str = ''
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

	@field_validator("name")
	@classmethod
	def validate_name(cls, value):
		value = value.strip()
		if len(value) == 0:
			raise ValueError('name cannot be empty')
		return value

	@field_validator("score")
	@classmethod
	def validate_score(cls, value):
		if value < 0 or value > 100:
			raise ValueError('score must be an integer matching or between 0 and 100')
		return value

	@field_validator("count_total", "count_progress", "count_rewatched")
	@classmethod
	def validate_counts(cls, value):
		if value < 0:
			raise ValueError('counts must be a positive integer')
		return value

	@field_validator("user_started_at", "user_finished_at", "media_started_at", "media_finished_at")
	@classmethod
	def validate_dates(cls, value):
		# let date do the error raising
		date.strptime(value, '%Y-%m-%d')
		return value

	@field_validator("type")
	@classmethod
	def validate_type(cls, value):
		# let enum do the error raising
		MediaTypes(value)
		return value

	@field_validator("status")
	@classmethod
	def validate_status(cls, value):
		# let enum do the error raising
		Status(value)
		return value

	@field_validator("comments")
	@classmethod
	def validate_comments(cls, value):
		maxlen:int = pow(2, 16) - 1
		if len(value) > maxlen:
			raise ValueError(f'value cannot be longer than {maxlen} characters')
		return value

	@field_validator("link_anilist", "link_myanimelist")
	@classmethod
	def validate_anilist(cls, value):
		regex:str = r'^(?:anime|manga)\/\d+$'
		if not re.fullmatch(regex, value, re.IGNORECASE):
			raise ValueError(f'AniList and MyAnimeList links must match the regular expression: {regex}')
		return value

	@field_validator("link_imdb")
	@classmethod
	def validate_imdb(cls, value):
		regex:str = r'^tt\d+$'
		if not re.fullmatch(regex, value, re.IGNORECASE):
			raise ValueError(f'IMDB links must match the regular expression: {regex}')
		return value

	@field_validator("link_tmdb")
	@classmethod
	def validate_tmdb(cls, value):
		regex:str = r'^(?:movie|tv)\/\d+$'
		if not re.fullmatch(regex, value, re.IGNORECASE):
			raise ValueError(f'TMDB links must match the regular expression: {regex}')
		return value

class Collection(BaseModel):
	# TODO: add validation for fields - name should have length and character limits, etc
	user_id: int | None = None
	name: str = 'Untitled Collection'
	display_image: bool = True
	display_score: bool = True
	display_progress: bool = True
	display_user_started: bool = True
	display_user_finished: bool = True
	display_days: bool = True
	rating_system: int = RatingSystems.ten_point.value
	private: bool = False

	@field_validator("rating_system")
	@classmethod
	def validate_rating_system(cls, value):
		# error from an invalid Enum will propogate automatically, no need for a wrapper
		RatingSystems(value)
		return value
	

def common_delete(table:str, id:int) -> bool:
	""" Common function for deleting from tables that use `id` columns as unique keys.
	
	`table` variable is used in a format string and thus MUST ONLY allow internal codebase use. """
	with DatabaseSession() as db:
		db.cursor.execute(f"""
			DELETE FROM {table} WHERE id = ?
		""", [id])
		is_successful:bool = True if db.cursor.rowcount == 1 else False
		db.connection.commit()
		return is_successful



def create_media_item(data: MediaItem) -> int:
	""" Create a new media item and return its ID """
	if 'name' not in data.model_fields_set \
	or 'collection_id' not in data.model_fields_set:
		raise ValueError('Media data is missing a required field.')
	
	with DatabaseSession() as db:
		db.easy_insert('media', {
			"name": data.name,
			"user_id": data.user_id,
			"collection_id": data.collection_id,
			"status": data.status,
			"score": data.score,
			"image": data.image,
			"description": data.description,
			"comments": data.comments,
			"count_total": data.count_total,
			"count_progress": data.count_progress,
			"count_rewatched": data.count_rewatched,
			"user_started_at": data.user_started_at,
			"user_finished_at": data.user_finished_at,
			"media_started_at": data.media_started_at,
			"media_finished_at": data.media_finished_at,
			"link_anilist": data.link_anilist,
			"link_myanimelist": data.link_myanimelist,
			"link_imdb": data.link_imdb,
			"link_tmdb": data.link_tmdb,
			"adult": data.adult,
			"favourite": data.favourite,
			"private": data.private
		})
		media_id = db.cursor.lastrowid
		if not isinstance(media_id, int):
			raise TypeError('cursor.lastrowid provided an unexpected value type')
		db.connection.commit()
		return media_id
	
def update_media(media_id: int, media_data: MediaItem) -> bool:
	# TODO: consider returning changed fields instead of bool

	with DatabaseSession() as db:
		# this line is very important! if you do not sure model_dump() with exclude_unset=True
		# (or an equivalent expression) then you may end up overwriting values that were not requested
		# to be overwritten!
		data:dict[str, Any] = media_data.model_dump(exclude_unset=True)

		# prevent any changes to reference columns
		if 'user_id' in data:
			del data['user_id']
		if 'id' in data:
			del data['id']

		db.easy_update('media', data, ('id', media_id))
		successful:bool = db.cursor.rowcount > 0
		db.connection.commit()
		return successful
	
def get_media_info(media_id: int) -> dict[str, Any]:
	# TODO: add safety check to not return if private == True and request_user_id != media_user_id
	with DatabaseSession() as db:
		rows = db.get_assoc("""
			SELECT name, user_id, collection_id, status, score, image, description, comments, count_total, count_progress, count_rewatched, user_started_at, user_finished_at, media_started_at, media_finished_at, link_anilist, link_myanimelist, link_imdb, link_tmdb, adult, favourite, private
			FROM media
			WHERE id=?
		""", [media_id])
		return {} if len(rows) == 0 else rows[0]
	
def delete_media(media_id: int) -> bool:
	return common_delete('media', media_id)



def get_collection_info(collection_id: int) -> dict[str, Any]:
	# TODO: add safety check to not return if private == True and request_user_id != collection_user_id
	with DatabaseSession() as db:
		rows = db.get_assoc("""
			SELECT id, user_id, name, display_image, display_score, display_progress, display_user_started, display_user_finished, display_days, rating_system, private
			FROM collections
			WHERE id = ?
		""", [collection_id])
		return {} if len(rows) == 0 else rows[0]
	

def delete_collection(collection_id: int) -> bool:
	return common_delete('collections', collection_id)

def create_collection(data: Collection) -> int:
	""" Create a new collection and return its ID """
	if 'name' not in data.model_fields_set:
		raise ValueError('collection name must be set')
	with DatabaseSession() as db:
		db.easy_insert('collections', {
			'user_id': data.user_id,
			'name': data.name,
			'display_image': data.display_image,
			'display_score': data.display_score,
			'display_progress': data.display_progress,
			'display_user_started': data.display_user_started,
			'display_user_finished': data.display_user_finished,
			'display_days': data.display_days,
			'rating_system': data.rating_system,
			'private': data.private
		})
		db.connection.commit()
		if not isinstance(db.cursor.lastrowid, int):
			raise Exception('cursor.lastrowid provided an unexpected value')
		return db.cursor.lastrowid
	
def update_collection(collection_id: int, collection_data: Collection) -> bool:
	# TODO: consider returning changed fields instead of bool

	with DatabaseSession() as db:
		# this line is very important! if you do not sure model_dump() with exclude_unset=True
		# (or an equivalent expression) then you may end up overwriting values that were not requested
		# to be overwritten!
		data:dict[str, Any] = collection_data.model_dump(exclude_unset=True)

		# prevent any changes to reference columns
		if 'user_id' in data:
			del data['user_id']
		if 'id' in data:
			del data['id']

		db.easy_update('collections', data, ('id', collection_id))
		successful:bool = db.cursor.rowcount > 0
		db.connection.commit()
		return successful