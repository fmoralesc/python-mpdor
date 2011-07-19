import gobject

class SongData(gobject.GObject):
	# Grabs songdata from the output of MPDClient.currentsong()
	def __init__(self, currentsonginfo):
		gobject.GObject.__init__(self)
		self.title = self.__get_title(currentsonginfo)
		artist = self.__get_artist(currentsonginfo)
		if artist != None:
			self.artist = artist
		if currentsonginfo.has_key("album"):
			self.album = currentsonginfo["album"]
		if currentsonginfo.has_key("track"):
			self.track = currentsonginfo["track"]
		if currentsonginfo.has_key("date"):
			self.date = currentsonginfo["date"]
		if currentsonginfo.has_key("genre"):
			self.genre = currentsonginfo["genre"]

	# Returns song title
	def __get_title(self, songdata):
		if songdata.has_key("title"):
			if songdata.has_key("name"): # we can assume it's a radio or stream
				# we split the title from the info we have
				# for streams, "title" is usually of the form "artist - title"
				return songdata["title"].split(" - ")[1]
			else:
				return songdata["title"]
		return songdata["file"] # we return the file path

	# Returns song artist
	def __get_artist(self, songdata):
		if songdata.has_key("name"): # we can assume it's a radio or stream
			if songdata.has_key("title"): # we grab the artist info from the title
				return songdata["title"].split(" - ")[0]
		elif songdata.has_key("artist"):
			return songdata["artist"]
	
	def __repr__(self):
		return self.__dict__.__repr__()

# Playback mode
class MPDOptions(gobject.GObject):
	# Grabs options info from the output of MPDClient.status()
	def __init__(self, status):
		gobject.GObject.__init__(self)
		self.repeat = bool(int(status["repeat"]))
		self.random = bool(int(status["random"]))
		self.consume = bool(int(status["consume"]))
		self.single = bool(int(status["single"]))

	def __repr__(self):
		return self.__dict__.__repr__()
