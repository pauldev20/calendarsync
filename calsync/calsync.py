from models.base import BaseCalDav, BaseCalendar
from datetime import datetime, timedelta
from typing import Union
import configparser
import logging
import caldav

# ---------------------------------------------------------------------------- #
#                                 CalendarSync                                 #
# ---------------------------------------------------------------------------- #
class CalendarSync:
	def __init__(self, config: configparser.ConfigParser):
		self.logger = logging.getLogger(self.__class__.__name__)
		self.config = config

	def __check_config(self, section: str) -> bool:
		if section not in self.config.sections():
			return False
		if self.config[section].get("username") == None or self.config[section].get("password") == None:
			return False
		if self.config[section].get("calendars") == None:
			return False
		return True

	def __get_cal_dav(self, section: str) -> Union[BaseCalDav, None]:
		try:
			if self.__check_config(section):
				caldavmodule = __import__(f"modules.{section.lower()}", fromlist=[f"{section}CalDav"])
				return getattr(caldavmodule, f"{section}CalDav")(
					self.config[section]["username"],
					self.config[section]["password"]
				)
			else:
				self.logger.error(f"Invalid {section} config")
		except Exception:
			self.logger.error("Error while connecting to CalDAV server")
		return None
	
	def __get_aggregation_calendar(self) -> Union[BaseCalendar, None]:
		aggregates = [(self.config[section]["aggregate"], section) for section in self.config.sections() if "aggregate" in self.config[section]]
		if len(aggregates) == 1:
			cal = self.__get_cal_dav(aggregates[0][1])
			if cal == None:
				return None
			return cal.create_calendar(aggregates[0][0])
		elif len(aggregates) > 1:
			self.logger.error("Multiple aggregation calendars found")
		else:
			self.logger.error("Could not find aggregation calendar")
		return None

	def sync(self, weeks_back: int, weeks_forward: int) -> None:
		aggregation = self.__get_aggregation_calendar()
		if aggregation == None:
			return
		self.logger.info(f"Clearing Aggregation Calendar")
		aggregation.clear()
		
		for section in self.config.sections():
			cldav = self.__get_cal_dav(section)
			if cldav == None:
				continue
			self.logger.info(f"Syncing - \"{section}\"")

			for calendar in self.config[section]["calendars"].split(","):
				cldav_calendar = cldav.create_calendar(calendar)
				for event in cldav_calendar.get_events( 
					datetime.now() - timedelta(weeks=weeks_back), 
					datetime.now() + timedelta(weeks=weeks_forward)
				):
					if not event.is_busy():
						continue
					aggregation.add_event(
						event.get_start(),
						event.get_end(),
						"BUSY",
						"OPAQUE" if event.is_busy() else "TRANSPARENT"
					)

			self.logger.info(f"Finished Syncing - \"{section}\"")
