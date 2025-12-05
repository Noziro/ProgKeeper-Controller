from pydantic import BaseModel
from enum import Enum
from progkeeper.database.common import DatabaseSession

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
	name: str
	user_id: int | None = None
	collection_id: int
	type: MediaTypes
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

class Collection(BaseModel):
	# TODO: add validation for fields - name should have length and character limits, etc
	user_id: int | None = None
	name: str
	display_image: bool = True
	display_score: bool = True
	display_progress: bool = True
	display_user_started: bool = True
	display_user_finished: bool = True
	display_days: bool = True
	rating_system: RatingSystems = RatingSystems.ten_point
	private: bool = False




def create_media_item(data: MediaItem) -> int:
	""" Create a new media item and return its ID """
	return # need to make collection first
	with DatabaseSession() as db:
		db.cursor.execute("""
			INSERT INTO media (
				name, user_id, collection_id, status, score, image, description, comments,
				count_total, count_progress, count_rewatched, user_started_at,
				user_finished_at, media_started_at, media_finished_at, link_anilist,
				link_myanimelist, link_imdb, link_tmdb, adult, favourite, private
			) VALUES (
				?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
			)
			""",
			[
				data.name, data.user_id, data.collection_id, data.status.value, data.score, data.image, data.description, data.comments,
				data.count_total, data.count_progress, data.count_rewatched, data.user_started_at,
				data.user_finished_at, data.media_started_at, data.media_finished_at, data.link_anilist,
				data.link_myanimelist, data.link_imdb, data.link_tmdb, data.adult, data.favourite, data.private
			]
		)
		db.connection.commit()
		return db.cursor.lastrowid



def get_collection_info(collection_id: int) -> dict:
	# TODO: add safety check to not return if private == True and request_user_id != collection_user_id
	with DatabaseSession() as db:
		rows = db.get_assoc("""
			SELECT id, user_id, name, display_image, display_score, display_progress, display_user_started, display_user_finished, display_days, rating_system, private
			FROM collections
			WHERE id = ?
		""", [collection_id])
		return {} if len(rows) == 0 else rows[0]
	

def create_collection(data: Collection) -> int:
	""" Create a new collection and return its ID """
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
			'rating_system': data.rating_system.value,
			'private': data.private
		})
		db.connection.commit()
		return db.cursor.lastrowid