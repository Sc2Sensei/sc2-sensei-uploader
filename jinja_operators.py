from datetime import datetime
import updater_app_settings

from jinja2 import pass_context

from settings import Settings
from flask import url_for
import Environment_Variables
from loguru import logger

appdata_directory = Environment_Variables.APPDATA_DIRECTORY

settings = Settings(appdata_directory)

class JinjaOperators:

	race_colors = {"T": "#55aaff", "P": "#e8cb00", "Z": "#b400ff"}
	race_icons = {
		"T": "icons/terran_logo.png", 
		"P": "icons/protoss_logo.png",
		"Z": "icons/zerg_logo.png"
	}

	def register_custom_jinja_operators(jinja_env):
		logger.info('register jinja operators')

		jinja_env.filters['start_with_windows'] = JinjaOperators.check_start_with_windows
		jinja_env.filters['get_formatted_timestamp'] = JinjaOperators.get_formatted_timestamp_12h_AM_PM
		jinja_env.filters['get_player_race_icon'] = lambda player: url_for('static', filename=JinjaOperators.race_icons[player['race'][0]])
		jinja_env.filters['get_sc2_sensei_url'] = lambda _: Environment_Variables.SC2_SENSEI_URL
		jinja_env.filters['replays_dir_is_set'] = JinjaOperators.replays_dir_is_set
		jinja_env.filters['get_replay_url'] = JinjaOperators.get_replay_url
		jinja_env.filters['get_app_version'] = lambda _ : JinjaOperators.get_app_version()



	@pass_context
	def replays_dir_is_set(context, _):
		rslt = settings.load().get('replays_directory', '') != ''
		return rslt

	@pass_context
	def check_start_with_windows(context, _):
		return settings.load().get('start_with_windows', False)

	# @pass_context
	# def get_app_version(context, _):
	def get_app_version():
		return updater_app_settings.APP_VERSION

	def get_formatted_timestamp_old(timestamp):
		rslt = datetime.fromtimestamp(int(timestamp))
		return str(rslt)[:-3]
	
	def get_formatted_timestamp_24h(timestamp):
		# Convert the timestamp to a datetime object
		dt_object = datetime.fromtimestamp(int(timestamp))
		
		# Format the datetime object to the desired string format
		formatted_time = dt_object.strftime("%H:%M - %d %b")
		
		return formatted_time

	def get_formatted_timestamp_12h_AM_PM(timestamp):
		# Convert the timestamp to a datetime object
		dt_object = datetime.fromtimestamp(int(timestamp))
		
		# Format the datetime object to the desired string format
		formatted_time = dt_object.strftime("%I:%M %p - %d %b")
		
		return formatted_time

	def get_replay_url(replay_id):
		url = f'{Environment_Variables.SC2_SENSEI_URL}/replay_analysis?replay_id={replay_id}' 
		return url

