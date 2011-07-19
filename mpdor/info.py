import gobject

class SongData(gobject.GObject):
	def __init__(self, artist=None, title=None, album=None, track=None, date=None, genre=None):
		gobject.GObject.__init__(self)
		self.artist = artist
		self.title = title
		self.album = album
		self.track = track
		self.date = date
		self.genre = genre

class MPDOptions(gobject.GObject):
	def __init__(self, repeat, random, consume, single):
		gobject.GObject.__init__(self)
		self.repeat = repeat
		self.random = random
		self.consume = consume
		self.single = single
	
	def __repr__(self):
		return "repeat: " + self.repeat.__repr__() +\
				"; random: " + self.random.__repr__()  +\
				"; consume: " + self.consume.__repr__() +\
				"; single: " + self.single.__repr__()
