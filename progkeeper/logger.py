import logging
from pathlib import Path

class Logger:
	def __init__(self, log_directory:Path = Path('/app/logs'), log_filename:str = 'app.log'):
		log_directory.mkdir(exist_ok=True)
		log_path:Path = log_directory / log_filename
		
		# Configure the logger
		self.logger = logging.getLogger('ProgKeeperLogger')
		self.logger.setLevel(logging.DEBUG)

		# Create file handler
		file_handler = logging.FileHandler(log_path)
		file_handler.setLevel(logging.DEBUG)

		# Create console handler
		console_handler = logging.StreamHandler()
		console_handler.setLevel(logging.DEBUG)

		# Define formatter
		formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

		# Add formatter to handlers
		file_handler.setFormatter(formatter)
		console_handler.setFormatter(formatter)

		# Add handlers to logger
		self.logger.addHandler(file_handler)
		self.logger.addHandler(console_handler)

	def info(self, message):
		self.logger.info(message)

	def debug(self, message):
		self.logger.debug(message)

	def warn(self, message):
		self.logger.warning(message)

	def error(self, message):
		self.logger.error(message)