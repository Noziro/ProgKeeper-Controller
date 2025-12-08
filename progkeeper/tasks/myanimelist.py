from fastapi import UploadFile
import progkeeper.database.media as media
from progkeeper.logger import Logger
import gzip
import xml.etree.ElementTree as ET
from datetime import date
from progkeeper.database.common import DatabaseSession

log = Logger(log_filename='background.log')

async def handle_file(file: UploadFile, user_id: int, collection_id: int):
	file_content:bytes = await file.read()
	if file_content[:2] == b'\x1f\x8b' or file.filename != None and file.filename.endswith('.gz'): # Check for gzip magic number
		unzip_gzip(file_content, user_id, collection_id)
	elif file_content.strip().startswith(b'<?xml') or file.filename != None and file.filename.endswith('.xml'):  # Check for XML declaration
		handle_mal_xml(file_content, user_id, collection_id)
	else:
		log.error(f'file type is unknown for file: {file.filename if file.filename != None else "?"}')
		raise ValueError('file type is unknown')
	
def unzip_gzip(file_content:bytes, user_id: int, collection_id: int):
	try:
		unzipped_content:bytes = gzip.decompress(file_content)
		handle_mal_xml(unzipped_content, user_id, collection_id)
	except gzip.BadGzipFile as e:
		log.error(f"Failed to unzip gzip file: {e}")
		raise ValueError("Invalid gzip file")

def handle_mal_xml(file_content:bytes, user_id: int, collection_id: int):
	decoded = file_content.decode('utf-8')

	try:
		xml:ET.Element = ET.fromstring(decoded)
	except ET.ParseError as e:
		log.error(f"Failed to parse XML: {e}")
		raise ValueError("Invalid XML file")
	
	myinfo:ET.Element|None = xml.find('myinfo')
	if xml.tag != 'myanimelist' or myinfo is None or myinfo.find('user_export_type') is None:
		log.error("missing required keys <user_export_type>")
		raise ValueError("missing <user_export_type>")

	
	export_type:int = int(myinfo.find('user_export_type').text) if myinfo.find('user_export_type').text != None else 0

	media_type:str = 'unknown'
	if export_type == 1:
		media_type = 'anime'
		media_entries = {anime for anime in xml.findall('anime')}
	elif export_type == 2:
		media_type = 'manga'
		media_entries = {manga for manga in xml.findall('manga')}
	else:
		log.error("invalid user_export_type")
		raise ValueError("invalid user_export_type")

	date_format:str = ''
	# get date format (Y-m-d or Y-d-m) by checking ahead
	media_entries = [m for m in media_entries]
	i:int = -1
	while i < len(media_entries) and date_format == '':
		i += 1
		entry_xml = media_entries[i]
		start_date:str|None = entry_xml.find('my_start_date').text if entry_xml.find('my_start_date') != None else None
		finish_date:str|None = entry_xml.find('my_finish_date').text if entry_xml.find('my_finish_date') != None else None

		for date_str in [start_date, finish_date]:
			if not isinstance(date_str, str):
				continue
			if date_str == '0000-00-00':
				continue
			parts = date_str.split('-')
			month:int = int(parts[1])
			day:int = int(parts[2])
			if month > 12:
				date_format = '%Y-%d-%m'
				break
			elif day > 12:
				date_format = '%Y-%m-%d'
				break

	for entry_xml in media_entries:
		entry:dict = {child.tag: child.text for child in entry_xml}

		status:media.Status
		status_text:str = entry['my_status'].lower() if 'my_status' in entry and isinstance(entry['my_status'], str) else ''
		if 'plan' in status_text:
			status = media.Status.planned
		elif status_text == 'watching' or status_text == 'reading':
			status = media.Status.current
		elif status_text == 'completed':
			status = media.Status.completed
		elif status_text == 'dropped':
			status = media.Status.dropped
		elif status_text == 'on-hold':
			status = media.Status.paused
		else:
			raise ValueError('unknown status')

		title_key:str = 'series_title' if media_type == 'anime' else 'manga_title'
		title:str = entry[title_key] if title_key in entry and entry[title_key] != None else '<Failed to Read Title>'

		total_key:str = 'series_episodes' if media_type == 'anime' else 'manga_volumes'
		total:int = int(entry[total_key]) if total_key in entry else 0

		progress_key:str = 'my_watched_episodes' if media_type == 'anime' else 'my_read_chapters'
		progress:int = int(entry[progress_key]) if progress_key in entry else 0

		rewatched_key = 'my_times_watched' if media_type == 'anime' else 'my_times_read'
		rewatched_times:int = int(entry[rewatched_key])
		rewatched_count:int = total * rewatched_times

		media_display:media.MediaTypes = media.MediaTypes.many if total > 1 else media.MediaTypes.single

		score:int|None = int(entry['my_score']) if 'my_score' in entry and entry['my_score'] != None else None
		if score == 0:
			score = None
		
		user_start:str|None = entry['my_start_date'] if 'my_start_date' in entry and entry['my_start_date'] != '0000-00-00' else None
		user_finish:str|None = entry['my_finish_date'] if 'my_finish_date' in entry and entry['my_finish_date'] != '0000-00-00' else None
		if user_start != None:
			try:
				date.strptime(user_start, date_format)
			except:
				user_start = None
		if user_finish != None:
			try:
				date.strptime(user_finish, date_format)
			except:
				user_finish = None

		comments:str = entry['my_comments'] if 'my_comments' in entry and isinstance(entry['my_comments'], str) else ''

		tags:str = entry['my_tags'] if 'my_tags' in entry and isinstance(entry['my_tags'], str) else ''

		if tags != '':
			comments += f'\n\n{tags}'

		mal_key:str = 'series_animedb_id' if media_type == 'anime' else 'manga_mangadb_id'
		mal_id:int = int(entry[mal_key]) if mal_key in entry else 0
		mal_link = f'{media_type}/{mal_id}'

		media_item = media.MediaItem(
			user_id=user_id,
			collection_id=collection_id,
			name=title,
			type=media_display.value,
			status=status.value,
			score=score,
			count_progress=progress,
			count_total=total,
			count_rewatched=rewatched_count,
			user_started_at=user_start,
			user_finished_at=user_finish,
			link_myanimelist=mal_link,
			comments=comments
		)

		with DatabaseSession() as db:
			db.cursor.execute("SELECT link_myanimelist FROM media WHERE link_myanimelist=?", [media_item.link_myanimelist])
			if db.cursor.rowcount > 0:
				log.debug(f'Skipped {media_item.name}, belonging to {media_item.user_id} to avoid duplication.')
				continue

		log.debug(f'Created {media_item.name}, belonging to {media_item.user_id}')
		import mariadb
		try:
			media.create_media_item(media_item)
		except mariadb.OperationalError as e:
			log.debug(e)
			log.debug(media_item)
			log.debug(type(media_item.name))
			