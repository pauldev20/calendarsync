from calsync import CalendarSync
from datetime import timedelta
import configparser
import argparse
import logging
import time
import os

if __name__ == "__main__":
	# ------------------------------- Logging Setup ------------------------------ #
	logging.basicConfig(
		level=logging.INFO,
		format='[%(asctime)s] [%(levelname)s] - %(message)s',
	)

	# ------------------------------- Args Parsing ------------------------------- #
	parser = argparse.ArgumentParser(description="Syncs calendars from multiple services into one busy/free calendar")
	parser.add_argument("-c", "--config", help="Path to config file", default="config.ini")
	parser.add_argument("-i", "--interval", help="Interval in minutes to sync", default=int(os.environ.get("CALENDARSYNC_INTERVAL", 15)), type=int)
	parser.add_argument("-wb", "--weeks-back", help="Number of weeks to sync back", default=int(os.environ.get("CALENDARSYNC_WEEKS_BACK", 2)), type=int)
	parser.add_argument("-wf", "--weeks-forward", help="Number of weeks to sync forward", default=int(os.environ.get("CALENDARSYNC_WEEKS_FORWARD", 2)), type=int)
	args = parser.parse_args()

	# ------------------------------ Config Parsing ------------------------------ #
	cfgp = configparser.ConfigParser()
	cfgp.read(args.config)

	# ----------------------------------- Main ----------------------------------- #
	calsync = CalendarSync(cfgp)
	tdelta = timedelta(minutes=args.interval)
	while True:
		calsync.sync(args.weeks_back, args.weeks_forward)
		time.sleep(tdelta.total_seconds())
