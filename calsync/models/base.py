from datetime import datetime, timedelta
from typing import List
import isodate
import caldav

# ---------------------------------------------------------------------------- #
#                              BaseObjectResource                              #
# ---------------------------------------------------------------------------- #
class BaseObjectResource(caldav.CalendarObjectResource):
	def __init__(self, event: caldav.CalendarObjectResource, addTravelTimes: bool = False) -> None:
		self.__dict__.update(event.__dict__)
		self.__addTravelTimes = addTravelTimes

	def is_busy(self) -> bool:
		"""
		The function checks if the event is busy or not.
		:return: a boolean value, True if the event is busy else False.
		"""
		if hasattr(self.instance.vevent, "transp") == False:
			return True
		return self.instance.vevent.transp.value == "OPAQUE"
	
	def get_name(self) -> str:
		"""
		The function `get_name` returns the value of the `summary` attribute of the event.
		:return: a string value, which is the summary value of the vevent instance.
		"""
		return self.instance.vevent.summary.value
	
	def set_name(self, name: str) -> None:
		"""
		The function `set_name` sets the value of the `summary` attribute of the event.
		:param name: The `name` parameter is a string that represents the name of the
		event.
		:type name: str
		"""
		self.instance.vevent.summary.value = name
	
	def get_start(self) -> datetime:
		"""
		The function returns the start datetime of an event.
		:return: The method is returning the value of the `dtstart` attribute of the
		event.
		"""
		if self.__addTravelTimes:
			return self.instance.vevent.dtstart.value - self.get_travel_time()
		return self.instance.vevent.dtstart.value

	def get_end(self) -> datetime:
		"""
		The function returns the end datetime of an event.
		:return: The method is returning the value of the `dtend` attribute of the
		event.
		"""
		return self.instance.vevent.dtend.value
	
	def get_travel_time(self) -> timedelta:
		"""
		The function returns the travel time of an event.
		:return: The method is returning the travel time of the event.
		"""
		if hasattr(self.instance.vevent, "x_apple_travel_duration") == False:
			return timedelta(days=0, seconds=0)
		return isodate.parse_duration(self.instance.vevent.x_apple_travel_duration.value)

	def __str__(self) -> str:
		return f"{self.get_name()} ({self.is_busy()}) - [{self.get_start()} - {self.get_end()}]"

	def __eq__(self, other):
		return self.get_name() == other.get_name() and self.get_start() == other.get_start() and self.get_end() == other.get_end()

# ---------------------------------------------------------------------------- #
#                                 BaseCalendar                                 #
# ---------------------------------------------------------------------------- #
class BaseCalendar:
	def __init__(self, calendar: caldav.Calendar, addTravelTimes: bool = False) -> None:
		self.addTravelTimes = addTravelTimes
		self.calendar = calendar

	def __expandLocal(self, events: List[caldav.CalendarObjectResource], start: datetime, end: datetime) -> List[caldav.CalendarObjectResource]:
		events_ = events.copy()
		for event in events_:
			event.expand_rrule(start=start, end=end)
		return [evt for splitevent in events_ for evt in splitevent.split_expanded()]
	
	def get_events(self, start: datetime, end: datetime) -> List[BaseObjectResource]:
		"""
		The function `get_events` returns a list of `BaseObjectResource` objects by
		searching for events within a specified time range.
		
		:param start: The start parameter is a datetime object that represents the
		start date and time of the range for which you want to retrieve events
		:type start: datetime
		:param end: The "end" parameter is a datetime object that represents the end
		time or date of the range for which you want to retrieve events
		:type end: datetime
		:return: a list of BaseObjectResource objects.
		"""
		return [
			BaseObjectResource(event, self.addTravelTimes) for event in self.__expandLocal(
				self.calendar.search(start=start, end=end, event=True), start, end
			)
		]
	
	def clear(self) -> None:
		"""
		The function clears all events from a calendar.
		"""
		for event in self.calendar.search(event=True):
			event.delete()
	
	def add_event(self, dtstart: datetime, dtend: datetime, summary: str, busy: bool = True) -> caldav.CalendarObjectResource:
		"""
		The function adds an event to a calendar with the specified start and end
		times, summary, and busy status.
		
		:param dtstart: The dtstart parameter represents the start date and time of the
		event. It should be a datetime object that specifies the year, month, day,
		hour, minute, and second of the event's start time
		:type dtstart: datetime
		:param dtend: The `dtend` parameter represents the end date and time of the
		event.
		:type dtend: datetime
		:param summary: The summary parameter is a string that represents the title or
		description of the event. It is typically a brief and concise summary of what
		the event is about
		:type summary: str
		:param busy: The "busy" parameter is a boolean value that indicates whether the
		event is marked as busy or not.
		:type busy: bool (optional)
		:return: a `caldav.CalendarObjectResource` object.
		"""
		return self.calendar.save_event(
			summary=summary,
			dtstart=dtstart,
			dtend=dtend,
			transp="OPAQUE" if busy else "TRANSPARENT"
		)
	
	def remove_events_in_range(self, start: datetime, end: datetime) -> None:
		"""
		The function removes all events within a specified time range.
		
		:param start: The start parameter is a datetime object that represents the
		start date and time of the range for which you want to remove events
		:type start: datetime
		:param end: The "end" parameter is a datetime object that represents the end
		time or date of the range for which you want to remove events
		:type end: datetime
		"""
		for event in self.calendar.search(start=start, end=end, event=True):
			event.delete()

# ---------------------------------------------------------------------------- #
#                                  BaseCalDav                                  #
# ---------------------------------------------------------------------------- #
class BaseCalDav:
	def __init__(self, username: str, password: str):
		self.username = username
		self.password = password
		self.client: caldav.DAVClient = None
		self.connect()

	def connect(self):
		"""
		The function checks if the client is None and raises an error if it is,
		otherwise it calls the principal method of the client.
		"""
		if self.client == None:
			raise NotImplementedError("This method is not implemented, please use a subclass")
		else:
			self.client.principal()

	def get_calendar_names(self) -> List[str]:
		"""
		The function returns a list of calendar names by connecting to a client and
		accessing the calendars.
		:return: A list of calendar names.
		"""
		if self.client == None:
			self.connect()
		return [cal.name for cal in self.client.principal().calendars()]

	def create_calendar(self, calendar_name: str, add_travel_times: bool = False) -> BaseCalendar:
		"""
		The function creates a calendar with the given name if it doesn't already
		exist, and returns a BaseCalendar object.
		
		:param calendar_name: The parameter `calendar_name` is a string that represents
		the name of the calendar that you want to create
		:type calendar_name: str
		:return: an instance of the BaseCalendar class.
		"""
		if self.client == None:
			self.connect()
		if calendar_name in self.get_calendar_names():
			return BaseCalendar(self.client.principal().calendar(name=calendar_name), add_travel_times)
		return BaseCalendar(self.client.principal().make_calendar(calendar_name), add_travel_times)
