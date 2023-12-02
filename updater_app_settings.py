import logging
import os
import pathlib
import sys

from tufup.utils.platform_specific import ON_WINDOWS

logger = logging.getLogger(__name__)

# App info
APP_NAME = 'Sc2_Sensei_Uploader'  # BEWARE: app name cannot contain whitespace
APP_VERSION = '1.72'

## This is a google bucket with the contents of the repository app.
TUFUP_REPOSITORY_URL = 'REDACTED'
## We can serve the files locally for testing
# TUFUP_REPOSITORY_URL = 'http://localhost:8000'

# On Windows 10, a typical location for app data would be %PROGRAMDATA%\MyApp
# (per-machine), or %LOCALAPPDATA%\MyApp (per-user). Typical app installation
# locations are %PROGRAMFILES%\MyApp (per-machine) or
# %LOCALAPPDATA%\Programs\MyApp (per-user).

MODULE_DIR = pathlib.Path(__file__).resolve().parent

# Are we running in a PyInstaller bundle?
FROZEN = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# For development
DEV_DIR = MODULE_DIR / 'temp'

# App directories
if ON_WINDOWS:
	# Windows per-user paths
	PER_USER_DATA_DIR = pathlib.Path(os.getenv('LOCALAPPDATA'))
	PER_USER_PROGRAMS_DIR = PER_USER_DATA_DIR / 'Programs'
	# Windows per-machine paths (only for illustrative purposes):
	# PER_MACHINE_PROGRAMS_DIR = pathlib.Path(os.getenv('ProgramFiles'))
	# PER_MACHINE_DATA_DIR = pathlib.Path(os.getenv('PROGRAMDATA'))
else:
	raise NotImplementedError('Unsupported platform')

PROGRAMS_DIR = PER_USER_PROGRAMS_DIR if FROZEN else DEV_DIR
DATA_DIR = PER_USER_DATA_DIR if FROZEN else DEV_DIR

INSTALL_DIR = PROGRAMS_DIR / APP_NAME
UPDATE_CACHE_DIR = DATA_DIR / APP_NAME / 'update_cache'
METADATA_DIR = UPDATE_CACHE_DIR / 'metadata'
TARGET_DIR = UPDATE_CACHE_DIR / 'targets'

# Update-server urls
METADATA_BASE_URL = f'{TUFUP_REPOSITORY_URL}/metadata/'
TARGET_BASE_URL = f'{TUFUP_REPOSITORY_URL}/targets/'


# Location of trusted root metadata file
TRUSTED_ROOT_SRC = MODULE_DIR / 'root.json'
if not FROZEN:
	# for development, get the root metadata directly from local repo
	sys.path.insert(0, str(MODULE_DIR.parent.parent))
	TRUSTED_ROOT_SRC =  DEV_DIR / 'repository' / 'metadata' / 'root.json'
TRUSTED_ROOT_DST = METADATA_DIR / 'root.json'

