import os
import json
from loguru import logger

class FileHandle:
	def __init__(self, dir_path):
		self.path = None

		self.dir_path = dir_path
		self.data_path = f"{self.dir_path}/data"
		self.logs_path = f"{self.dir_path}/logs"

		dirs = [self.dir_path, self.data_path, self.logs_path]

		for i in dirs:
			if not os.path.exists(i):
				os.mkdir(i)


class JSONHandle(FileHandle):
	def __init__(self, dir_path):
		super().__init__(dir_path)

	def load(self):
		result = None
		with open(self.path, "r") as file:
			try:
				result = json.load(file)
			except Exception as e:
				logger.info(f"Can't load json: {e}")
		
		result['user_id'] = 'MockUserId' # This line is commented in production

		return result
		
	def save(self, data):
		with open(self.path, "w") as file:
			json.dump(data, file, indent=2)