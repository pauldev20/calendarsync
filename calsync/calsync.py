from models.base import BaseCalDav, BaseCalendar, BaseObjectResource
from datetime import datetime, timedelta
from typing import Union, List
import configparser
import logging
import os

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
	
	def __get_aggregates_list(self, section: str, key: str) -> List[str]:
		return self.config[section][key].split(",") if key in self.config[section] else []
	
	def __get_aggregation_calendars(self) -> Union[List[BaseCalendar], None]:
		aggregates = []
		for section in self.config.sections():
			aggregate = self.__get_aggregates_list(section, "aggregate")
			visible = self.__get_aggregates_list(section, "visible")
			if len(aggregate) > 0 or len(visible) > 0:
				caldav = self.__get_cal_dav(section)
				aggregates.extend([
					caldav.create_calendar(cal) for cal in aggregate
				] + [
					caldav.create_calendar(cal, invisible_summary=False) for cal in visible
				])
		if len(aggregates) == 0:
			self.logger.error("Could not find aggregation calendar(s)")
			return None
		return aggregates

	def sync(self, weeks_back: int, weeks_forward: int) -> None:
		"""
		The `sync` function synchronizes calendars by retrieving events from specified
		calendars and adding them to aggregation calendars within a specified time
		range.
		
		:param weeks_back: The `weeks_back` parameter specifies the number of weeks in
		the past from the current date that should be included in the synchronization
		process. It determines the starting point for retrieving events from the
		calendars
		:type weeks_back: int
		:param weeks_forward: The parameter `weeks_forward` represents the number of
		weeks in the future from the current date that events will be synced
		:type weeks_forward: int
		"""
		if len(self.config.keys()) == 1:
			self.logger.error("No Or Invalid Config Found")
			return

		aggregations = self.__get_aggregation_calendars()
		if aggregations == None or len(aggregations) == 0:
			return
		
		new_agg_events: List[BaseObjectResource] = []
		for section in self.config.sections():
			cldav = self.__get_cal_dav(section)
			if cldav == None:
				continue

			# --------------------------- Get Aggregated Events -------------------------- #
			for calendar in self.config[section]["calendars"].split(","):
				self.logger.info(f"Loading Events - \"{section}\" - \"{calendar}\"")
				cldav_calendar = cldav.create_calendar(calendar,
					bool(self.config[section].get("travel", False))
				)
				for event in cldav_calendar.get_events( 
					datetime.now() - timedelta(weeks=weeks_back), 
					datetime.now() + timedelta(weeks=weeks_forward)
				):
					if not event.is_busy():
						continue
					new_agg_events.append(event)

			if len(self.config[section]["calendars"].split(",")) == 0:
				self.logger.error(f"No Configured Calendars Found - \"{section}\"")
			else:
				self.logger.info(f"Finished Loading Events - \"{section}\"")

		# --------------------------- Add Aggregated Events -------------------------- #
		self.logger.info(f"Syncing Calendar(s)")
		for agg_calendar in aggregations:
			agg_events = agg_calendar.get_events(
				datetime.now() - timedelta(weeks=weeks_back), 
				datetime.now() + timedelta(weeks=weeks_forward)
			)

			for evt in [event for event in agg_events if event not in new_agg_events]:
				agg_calendar.remove_events_in_range(evt.get_start(), evt.get_end())

			for evt in [event for event in new_agg_events if event not in agg_events]:
				agg_calendar.add_event(
					evt.get_start(),
					evt.get_end(),
					evt.get_name(),
					evt.is_busy()
				)
		self.logger.info(f"Finished Syncing Calendar(s)")
