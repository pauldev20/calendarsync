from models.base import BaseCalDav
import caldav

# ---------------------------------------------------------------------------- #
#                                 iCloudCalDav                                 #
# ---------------------------------------------------------------------------- #
class iCloudCalDav(BaseCalDav):
	def connect(self):
		self.client = caldav.DAVClient(
			url="https://caldav.icloud.com",
			username=self.username,
			password=self.password
		)
		super().connect()
