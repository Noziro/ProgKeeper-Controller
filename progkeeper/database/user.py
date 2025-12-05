from progkeeper.database.common import DatabaseSession

def get_user_info(user_id: int) -> dict:
	""" Get information about a user by their ID. Returns an empty dict if not found. """
	with DatabaseSession() as db:
		rows = db.get_assoc(
			"SELECT id, username, created_at FROM users WHERE id = ?",
			[user_id]
		)
		return {} if len(rows) == 0 else rows[0]

# imports specifically for obliterate_user
from progkeeper.database.auth import delete_all_sessions_for_user

def obliterate_user(user_id: int) -> {}:
	""" Deletes a user and all of their content. "To shreds, you say?"
	
	Returns a dictionary containing data of all performed changes, with the primary attribute {"deleted_user_id": user_id} """
	
	data = {}

	# remove all references to user ID in other tables to allow user deletion
	# TODO: as other functions are added such as media and collections, you will have to delete these too.
	data['deleted_session_count'] = delete_all_sessions_for_user(user_id)

	with DatabaseSession() as db:
		db.cursor.execute(
			"UPDATE users SET deleted=true WHERE id = ? AND deleted=false",
			[user_id]
		)
		db.connection.commit()
		if db.cursor.rowcount > 0:
			data['deleted_user_id'] = user_id
	
	return data