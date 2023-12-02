import requests
import settings
import os
import Environment_Variables

get_replay_upload_count_url = Environment_Variables.GET_REPLAY_UPLOAD_COUNT_URL
appdata_directory = Environment_Variables.APPDATA_DIRECTORY
settings_handle = settings.Settings(appdata_directory)

def get_uploaded_replays_this_month():
	user_id = settings_handle.load()['user_id']
	
	resp = requests.get(get_replay_upload_count_url, 
		params={'user_id':user_id}
	)
	uploaded_replays_this_month = resp.json()['uploaded']
	limit = resp.json()['limit']

	return (uploaded_replays_this_month, limit)