import os
import pathlib
import sys

FLASK_RUN_PORT = 5078 # This always stays the same
DEBUG = True
# DEBUG = False
USE_PRODUCTION_ROUTES = True
# USE_PRODUCTION_ROUTES = False


print('[Env] Debug mode is '+('ON' if DEBUG else 'OFF'))
print('[Env] USE_PRODUCTION_ROUTES '+('ON' if USE_PRODUCTION_ROUTES else 'OFF'))

if USE_PRODUCTION_ROUTES:
	# Production
	import os
	SC2_SENSEI_URL = "https://sc2sensei.top"
	APPDATA_DIRECTORY = os.path.expandvars("%APPDATA%/Sc2Sensei_Auto_Uploader")
	GET_REPLAY_UPLOAD_COUNT_URL = "REDACTED"
else:
	# Development
	SC2_SENSEI_URL = "http://127.0.0.1:5000"
	APPDATA_DIRECTORY = f"{os.getcwd()}/testing"
	GET_REPLAY_UPLOAD_COUNT_URL = "http://127.0.0.1:5000/get_replay_upload_count"


UPLOAD_ENDPOINT = f"REDACTED"

# Are we running in a PyInstaller bundle?
FROZEN = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

SC2SENSEI_ICONS_DIR = pathlib.Path(os.getcwd())
if FROZEN:
	SC2SENSEI_ICONS_DIR = SC2SENSEI_ICONS_DIR / '_internal'

SC2SENSEI_ICONS_DIR = SC2SENSEI_ICONS_DIR / 'static' / 'icons'
SC2SENSEI_ICON_PATH_GREEN = SC2SENSEI_ICONS_DIR / "sc2_sensei_logo_green_v2.png"
SC2SENSEI_ICON_PATH_RED = SC2SENSEI_ICONS_DIR / "sc2_sensei_logo_red_v2.png"


