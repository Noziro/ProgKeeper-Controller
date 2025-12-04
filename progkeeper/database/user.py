from progkeeper.database.common import DatabaseSession

def get_user_info(user_id: int) -> dict:
	""" Get information about a user by their ID. Returns an empty dict if not found. """
	with DatabaseSession() as db:
		rows = db.get_assoc(
			"SELECT id, username, created_at FROM users WHERE id = ?",
			[user_id]
		)
		return {} if len(rows) == 0 else rows[0]
	return {}