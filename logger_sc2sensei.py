from loguru import logger
import notifiers
from notifiers.logging import NotificationHandler

def init():
	params = {
		"from" : "bug-tracking@sc2sensei.top",
		"to": "sc2sensei@gmail.com",
		"subject": "[Uploader App] Bug Report",
		"username": '007ee6e031396e',
		"password": '87e6c1e14155ba',
		"port" : 2525,
		"host" : 'sandbox.smtp.mailtrap.io',
		"tls" : True,
		"ssl" : False
	}

	# Send a single notification
	notifier = notifiers.get_notifier("email")

	# Be alerted on each error message
	handler = NotificationHandler("gmail", defaults=params)
	logger.add(handler, level="ERROR")

	logger.add('sc2_sensei.log', rotation='2.5 MB', retention="20 days", enqueue=True, backtrace=True, diagnose=True)


# logger.info('info')
# logger.error('AA not found in BB. Please give me 78 bytes')
# logger.critical('critical')
# logger.warning('warning')
# logger.debug('debug')