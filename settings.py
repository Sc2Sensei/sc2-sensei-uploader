import os
from files import JSONHandle

class Settings(JSONHandle):
	def __init__(self, dir_path=None):
		super().__init__(dir_path)
		self.path = f"{self.data_path}/settings.json"
		
		# First opening			
		if not os.path.exists(self.path):
			empty = { 
				"user_id" : "",
				"replays_directory" : "",
				"uploader_state" : False,
				"start_with_windows" : False
			}
			self.save(empty)

	def update(self, setting, new_value):
		new_settings = self.load()
		new_settings[setting] = new_value
		self.save(new_settings)