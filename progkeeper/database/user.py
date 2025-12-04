from progkeeper.database.common import DatabaseSession

def get_user_info(user_id: int) -> dict:
	""" Get information about a user by their ID. Returns an empty dict if not found. """
	with DatabaseSession() as db:
		db.cursor.execute(
			"SELECT id, username, created_at FROM users WHERE id = ?",
			[user_id]
		)
		row = db.cursor.fetchone()
		if row is None:
			return {}
		return {
			"id": row[0],
			"username": row[1],
			"created_at": row[2]
		}
	return {}