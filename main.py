import logger_sc2sensei

logger = logger_sc2sensei.init()
# From now all, all scripts can import the logger with the following line
### from loguru import logger


import sys
from desktop_app_launcher import main



main(sys.argv[1:])
