import gobject
import socket

HELLO_PREFIX = "OK MPD "
ERROR_PREFIX = "ACK "
SUCCESS = "OK"
NEXT = "list_OK"

class MPDError(Exception): pass
class ConnectionError(MPDError): pass
class ProtocolError(MPDError): pass
class CommandError(MPDError): pass
class CommandListError(MPDError): pass
class PendingCommandError(MPDError): pass
class IteratingError(MPDError): pass

class _NotConnected(object):
	def __getattr__(self, attr):
		return self._dummy

	def _dummy(*args):
		raise ConnectionError("Not connected")

class MPDProtocolClient(gobject.GObject):
	def __init__(self):
		gobject.GObject.__init__(self)
		self._reset()

	def _write_line(self, line):
		self._wfile.write("%s\n" % line)
		self._wfile.flush()
		self._last_command = line.split()[0]

	def _read_line(self):
		line = self._rfile.readline()
		if not line.endswith("\n"):
			raise ConnectionError("Connection lost while reading line")
		line = line.rstrip("\n")
		if line.startswith(ERROR_PREFIX):
			error = line[len(ERROR_PREFIX):].strip()
			raise CommandError(error)
		if self._command_list is not None:
			if line == NEXT:
				return
			if line == SUCCESS:
				raise ProtocolError("Got unexpected '%s'" % SUCCESS)
		elif line == SUCCESS:
			return
		return line

	def _get_response(self):
		raw_lines = []
		line = self._read_line()
		while line != None:
			raw_lines.append(line)
			line = self._read_line()

		if len(raw_lines) == 0:
			return # we have OK
		else:
			if NEXT in raw_lines:
				# TODO: extend the parser to handle this
				pass
			else:
				# those are lists
				if self._last_command in ("commands", "notcommands", "list",
						"listplaylist", "tagtypes", "urlhandlers"):
					return [":".join(com.split(":")[1:]).strip() for com in raw_lines]

				#  those are dictionaries or single values
				elif self._last_command in ("status", "currentsong", "stats",
						"replay_gain_status", "playlist", "addid", "idle", "update"):
					response_data = {}
					for line in raw_lines:
						line_data = [d.strip() for d in line.split(":")]
						if self._last_command == "playlist":
							response_data[int(line_data[0])] = line_data[2]
						elif self._last_command in ("addid", "update"):
							return int(line_data[1])
						elif self._last_command == "idle":
							self._pending = False
							return line_data[1]
						else:
							response_data[line_data[0]] = line_data[1]
					return response_data

				# those are lists of dictionaries
				elif self._last_command in ("playlistid", "playlistfind",
						"playlistsearch", "playlistinfo", "plchanges", "plchangesposid",
						"listplaylistinfo",	"search", "find", "listplaylists", "outputs"):
					items = []
					seen_attrs = []
					tmp_dict = {}
					for line in raw_lines:
						line_data = [d.strip() for d in line.split(":")]
						_attr, value = line_data[0], line_data[1]
						# TODO: check if there are duplicates
						if _attr in seen_attrs:
							items.append(tmp_dict)
							tmp_dict = {}
							seen_attrs = []
							seen_attrs.append(_attr)
							tmp_dict[_attr] = value
						elif line == raw_lines[-1]:
							tmp_dict[_attr] = value
							items.append(tmp_dict)
							tmp_dict = {}
							seen_attrs = []
							seen_attrs.append(_attr)
						else:
							seen_attrs.append(_attr)
							tmp_dict[_attr] = value
					return items
		return raw_lines

	def _execute(self, *args):
		line = " ".join([args[0], " ".join(['"'+str(i)+'"' for i in args[1]])]).strip()
		if not self._pending:
			self._write_line(line)
			if self._command_list is not None:
				self._command_list.append(line)
			else:
				return self._get_response()
		else:
			raise PendingCommandError("Can't execute commands while other"
			"commands are pending")

	def _create_executor(self, command):
		return lambda *args: self._execute(command, args)

	def _get_commands(self):
		# idle and password must be treated differently, so we filter them out
		available_commands = [com for com in self._execute("commands", ()) if com not in ("idle", "password")]
		for command in available_commands:
			self.__dict__[command] = self._create_executor(command)

	def _hello(self):
		line = self._rfile.readline()
		if not line.endswith("\n"):
			raise ConnectionError("Connection lost while reading MPD hello")
		line = line.rstrip("\n")
		if not line.startswith(HELLO_PREFIX):
			raise ProtocolError("Got invalid MPD hello: '%s'" % line)
		self.mpd_version = line[len(HELLO_PREFIX):].strip()
		self._get_commands()

	def _reset(self):
		self.mpd_version = None
		self._pending = False
		self._command_list = None
		self._last_command = None
		self._sock = None
		self._rfile = _NotConnected()
		self._wfile = _NotConnected()

	def _connect_unix(self, path):
		if not hasattr(socket, "AF_UNIX"):
			raise ConnectionError("Unix domain sockets not support"
			"on this platform")
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sock.connect(path)
		return sock

	def _connect_tcp(self, host, port):
		try:
			flags = socket.AI_ADDRCONFIG
		except AttributeError:
			flags = 0
		err = None
		for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC,
				socket.SOCK_STREAM, socket.IPPROTO_TCP,
				flags):
			af, socktype, proto, canonname, sa = res
			sock = None
			try:
				sock = socket.socket(af, socktype, proto)
				sock.connect(sa)
				return sock
			except socket.error:
				if sock is not None:
					sock.close()
		if err is not None:
			raise err
		else:
			raise ConnectionError("getaddrinfo returns an empty list")

	def connect_to_server(self, host, port):
		if self._sock is not None:
			raise ConnectionError("Already connected")
		if host.startswith("/"):
			self._sock = self._connect_unix(host)
		else:
			self._sock = self._connect_tcp(host, port)
		self._rfile = self._sock.makefile("rb")
		self._wfile = self._sock.makefile("wb")
		try:
			self._hello()
		except:
			self.disconnect_from_server()
			raise

	def disconnect_from_server(self):
		self._rfile.close()
		self._wfile.close()
		self._sock.close()
		self._reset()
		# we delete all of the instance's protocol methods
		for com in [com for com in self.__dict__ if callable(self.__dict__[com])]:
			del self.__dict__[com]

	def fileno(self):
		if self._sock is None:
			raise ConnectionError("Not connected")
		return self._sock.fileno()

	def command_list_ok_begin(self):
		if self._command_list is not None:
			raise CommandListError("Already in command list")
		self._write_line("command_list_ok_begin")
		self._command_list = []

	def command_list_end(self):
		if self._command_list is None:
			raise CommandListError("Not in command list")
		self._write_line("command_list_end")
		self._command_list = None
		return self._get_response()

	def idle(self, *subsystem):
		if self._pending == False:
			self._pending = True
			line = "idle " + " ".join(subsystem)
			self._write_line(line.strip())

	def noidle(self, *args):
		if self._pending == True:
			self._pending = False
			self._execute("noidle", args)

	def password(self, password):
		if self._pending == False:
			self._execute("password", password)
			self._get_commands() # available commands might have changed
