from pydantic import BaseModel
from enum import Enum
from progkeeper.database.common import DatabaseSession

class Status(Enum):
	current = 'current'
	completed = 'completed'
	paused = 'paused'
	dropped = 'dropped'
	planned = 'planned'

class MediaItem(BaseModel):
	name: str
	user_id: int
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




def create_media_item(data: MediaItem) -> int:
	""" Create a new media item and return it's ID """
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