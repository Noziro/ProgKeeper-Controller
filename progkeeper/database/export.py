import progkeeper.database.user as user
import progkeeper.database.media as media

def as_progkeeper(user_id: int) -> dict:
	""" Exports all user data in a format custom to this program. """
	# TODO: allow asynchronous execution, as this could get slow

	data = {}
	data['user'] = user.get_user_info(user_id)

	collection_set = media.get_collection_info_by_user(user_id)
	
	if len(collection_set) > 0 and 'collection_set' not in data:
		data['collection_set'] = []
	for coll in collection_set:
		coll = media.get_collection_info(coll['id'])
		coll['media_set'] = media.get_media_info_by_collection(coll['id'])
		data['collection_set'].append(coll)

	return data