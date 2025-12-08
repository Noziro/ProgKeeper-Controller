# This file marks the directory as a Python package.

from progkeeper.database.common import DatabaseSession, is_database_ready

with DatabaseSession() as db:
	if not is_database_ready(db.cursor):
		from progkeeper.database.setup import setup_database
		setup_database()