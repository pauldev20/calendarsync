from typing import List, Literal
from datetime import datetime
import caldav

# ---------------------------------------------------------------------------- #
#                              BaseObjectResource                              #
# ---------------------------------------------------------------------------- #
class BaseObjectResource(caldav.CalendarObjectResource):
	def __init__(self, event: caldav.CalendarObjectResource) -> None:
		self.__dict__.update(event.__dict__)

	def is_busy(self) -> bool:
		if hasattr(self.instance.vevent, "transp") == False:
			return True
		return self.instance.vevent.transp.value == "OPAQUE"
	
	def get_name(self) -> str:
		return self.instance.vevent.summary.value
	
	def get_start(self) -> datetime:
		return self.instance.vevent.dtstart.value

	def get_end(self) -> datetime:
		return self.instance.vevent.dtend.value
	
	def __str__(self) -> str:
		return f"{self.get_name()} ({self.is_busy()}) - [{self.get_start()} - {self.get_end()}]"

# ---------------------------------------------------------------------------- #
#                                 BaseCalendar                                 #
# ---------------------------------------------------------------------------- #
class BaseCalendar:
	def __init__(self, calendar: caldav.Calendar) -> None:
		self.calendar = calendar

	def __expandLocal(self, events: List[caldav.CalendarObjectResource], start: datetime, end: datetime) -> List[caldav.CalendarObjectResource]:
		events_ = events.copy()
		for event in events_:
			event.expand_rrule(start=start, end=end)
		return [evt for splitevent in events_ for evt in splitevent.split_expanded()]
	
	def get_events(self, start: datetime, end: datetime) -> List[BaseObjectResource]:
		return [
			BaseObjectResource(event) for event in self.__expandLocal(self.calendar.search(start=start, end=end, event=True), start, end)
		]
	
	def clear(self) -> None:
		for event in self.calendar.search(event=True):
			event.delete()
	
	def add_event(self, dtstart: datetime, dtend: datetime, summary: str, transp: Literal["OPAQUE", "TRANSPARENT"] = "OPAQUE") -> caldav.CalendarObjectResource:
		return self.calendar.save_event(
			summary=summary,
			dtstart=dtstart,
			dtend=dtend,
			transp=transp
		)

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
		if self.client == None:
			raise NotImplementedError("This method is not implemented, please use a subclass")
		else:
			self.client.principal()

	def get_calendar_names(self) -> List[str]:
		if self.client == None:
			self.connect()
		return [cal.name for cal in self.client.principal().calendars()]

	def create_calendar(self, calendar_name: str) -> BaseCalendar:
		if self.client == None:
			self.connect()
		if calendar_name in self.get_calendar_names():
			return BaseCalendar(self.client.principal().calendar(name=calendar_name))
		return BaseCalendar(self.client.principal().make_calendar(calendar_name))
