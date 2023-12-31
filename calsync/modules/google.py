from models.base import BaseCalDav
import caldav

# ---------------------------------------------------------------------------- #
#                                 GoogleCalDav                                 #
# ---------------------------------------------------------------------------- #
class GoogleCalDav(BaseCalDav):
	def connect(self):
		self.client = caldav.DAVClient(
			url=f"https://www.google.com/calendar/dav/{self.username}/user",
			username=self.username,
			password=self.password
		)
		super().connect()
