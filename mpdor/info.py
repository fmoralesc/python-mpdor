import gobject

class SongData(gobject.GObject):
    # Grabs songdata from the output of MPDClient.currentsong()
    def __init__(self, currentsonginfo):
        gobject.GObject.__init__(self)
        self.title = self.__get_title(currentsonginfo)
        artist = self.__get_artist(currentsonginfo)
        if artist != None:
            self.artist = artist
        if currentsonginfo.has_key("Album"):
            self.album = currentsonginfo["Album"]
        if currentsonginfo.has_key("Track"):
            self.track = currentsonginfo["Track"]
        if currentsonginfo.has_key("Date"):
            self.date = currentsonginfo["Date"]
        if currentsonginfo.has_key("Genre"):
            self.genre = currentsonginfo["Genre"]

    # Returns song title
    def __get_title(self, songdata):
        if songdata.has_key("Title"):
            if songdata.has_key("Name"): # we can assume it's a radio or stream
                # we split the title from the info we have
                # for streams, "title" is usually of the form "artist - title"
                return songdata["Title"].split(" - ")[1]
            else:
                return songdata["Title"]
        return songdata["file"] # we return the file path

    # Returns song artist
    def __get_artist(self, songdata):
        if songdata.has_key("Name"): # we can assume it's a radio or stream
            if songdata.has_key("Title"): # we grab the artist info from the title
                return songdata["Title"].split(" - ")[0]
        elif songdata.has_key("Artist"):
            return songdata["Artist"]

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
        self.crossfade = int(status["xfade"])
        self.mixrampdb = float(status["mixrampdb"])
        self.mixrampdelay = float(status["mixrampdelay"])
        self.replay_gain_status = status["replay_gain_mode"]

    def __repr__(self):
        return self.__dict__.__repr__()
