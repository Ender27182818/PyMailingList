import imaplib
import ConfigParser
from pprint import pprint
import re
import email

class IMAPConnectionError(Exception):
	"""Simple class for all IMAPConnection errors"""
	def __init__(self, value):
		self.parameter = value
	def __str__(self):
		return repr(self.parameter)

class IMAPFolder:
	# The regex used for parsing the data returned from an IMAP server
	list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')

	"""Defines a folder in an IMAP account"""
	def __init__(self, folder_name, parent):
		self.children = []
		self.folder_name = folder_name
		if parent is None:
			self.path = '/'
		else:
			self.bind_parent(parent)
			
	
	def bind_parent(self, parent):
		self.parent = parent
		# Fix up my path
		if( parent.path == '/' ):
			self.path = '/' + self.folder_name
		else:
			self.path = parent.path + '/' + self.folder_name

		# Add me to my parents children, if I'm not already
		for c in parent.children:
			if c is self:
				return
		parent.children.append(self)

	@staticmethod
	def parse_list_line(line):
		"""Parses the given 'list' data line into its constituent parts"""
		flags, delimiter, folder_name = IMAPFolder.list_response_pattern.match(line).groups()
		folder_name = folder_name.strip('"')
		return flags, delimiter, folder_name
		
class IMAPConnection:
	"""Defines a connection to an IMAP server and allows some convenience functions"""
	def __init__(self, config_file, debug=False):
		"""Create the connection using the provided config file"""
		self.folders = {}
		self.folders['/'] = IMAPFolder('/', None)
		self.selected_folder_name = '/'

		# Read the config file
		config = ConfigParser.ConfigParser()
		config.read(config_file)
		self.hostname = config.get('imap_server', 'hostname')
		self.port = config.getint('imap_server', 'port')
		self.ssl = config.getboolean('imap_server', 'ssl')
		self.username = config.get('imap_account', 'username')
		self.password = config.get('imap_account', 'password', True)
		self.bot_name = config.get('bot', 'name')
		self.bot_address = config.get('bot', 'address')
	
	def _ensure_connection(self):
		"""Ensures that a connection is made and raises an error if not"""
		if( not hasattr(self, 'connection') ):
			raise IMAPConnectionError("You need to connect first")

	def connect(self, debug=False):
		"""Connects to the server specified in the config file"""
		print( "Connecting to {0}:{3} with username {1} and SSL {2}".format(self.hostname, self.username, self.ssl, self.port) )
		if( self.ssl ):
			self.connection = imaplib.IMAP4_SSL(self.hostname, self.port)
		else:
			self.connection = imaplib.IMAP4(self.hostname, self.port)
		self.connection.login(self.username, self.password)
		print( "Connected." )
	

	def get_folders(self, parent_folder_path='/'):
		"""Returns a list of the folders"""
		self._ensure_connection()
		
		if( parent_folder_path is '/'):
			response, data = self.connection.list()
		else:
			response, data = self.connection.list(directory=parent_folder)

		if( response != "OK" ):
			raise IMAPConnectionError("Bad response: " + response)
		
		# Parse the returned data
		parent_folder = self.get_folder(parent_folder_path)
		for line in data:
			flags, delimiter, folder_name = IMAPFolder.parse_list_line(line)
			folder = self.get_folder( folder_name, create=True, parent=parent_folder )
			folder.flags = flags
			folder.delimiter = delimiter
		return self.folders

	def select_folder(self, folder_name, readonly=True):
		"""Selects the given folder causing all transactions to occur on that folder. Returns all messages in the given mailbox on success, raises an exception on failure"""
		self._ensure_connection()
			
		response, data = self.connection.select(folder_name, readonly=readonly)
		if( response != "OK" ):
			raise IMAPConnectionError("Bad response: " + response)
		if( response == "NO" ):
			raise IMAPConnectionError("Specified folder {0} does not exist".format(folder_name))
		if not isinstance(data, list):
			raise IMAPConnectionError("Unrecognized data response: " + repr(data))
		self.selected_folder = folder_name
		return int(data[0])

	def get_folder(self, folder_name, create=False, parent=None):
		"""Returns the folder with the given name, if it exists, or None if it does not, unless create is specified, in which case it creates the folder and returns the created one"""
		if( folder_name in self.folders.keys() ):
			return self.folders[folder_name]
		if( create ):
			new_folder = IMAPFolder(folder_name, parent=parent)
			self.folders[new_folder.path] = new_folder
			return new_folder
		else:
			return None

	message_status_line_pattern = re.compile(r'(?P<name>.*?) \(MESSAGES (?P<message_count>.*)\)')
	def _parse_status_message_status_line( self, line ):
		"""Parses a line from a status request looking for message count and returns the mailbox name and the message count"""
		folder_name, message_count = self.message_status_line_pattern.match(line).groups()
		return folder_name, int(message_count)
		
		
		
	def get_message_ids(self, debug=False):
		"""Returns the list of message IDs of the messages in the given folder"""
		self._ensure_connection()

		# Make sure there are messages in the inbox
		response, statusline = self.connection.status( self.selected_folder, "(MESSAGES)" )
		if response != "OK":
			raise IMAPConnectionError("Bad response on status: " + response)
		if debug:
			print( "get_message_ids: Status request returned: {0} {1}".format( response, statusline ) )
		folder_name, message_count = self._parse_status_message_status_line( statusline[0] )
		if debug:
			print( "Parsed out folder name '{0}' and message count '{1}'".format(folder_name, message_count) )
		if message_count == 0:
			return []

		response, msg_ids = self.connection.search(None, 'ALL')
		if( response != "OK" ):
			raise IMAPConnectionError("Bad response: " + response)

		if not isinstance(msg_ids, list):
			raise IMAPConnectionError("Unrecognized message ID string: " + repr(msg_ids))
		
		msg_ids = msg_ids[0].split(' ')
		return msg_ids

	def get_message(self, message_id, debug=False):
		"""Returns the header of the given message ID"""
		self._ensure_connection()

		if debug:
			print( "Getting message with id '{0}'".format(message_id) )

		response, msg_data = self.connection.fetch(message_id, '(RFC822)')
		if( response != "OK" ):
			raise IMAPConnectionError("Bad response: " + response)
		# The data that comes back is funny - it's a list of two items, the second being a string
		# with the messages' flags. The first item in the list is a tuple with data about the message
		# body as a string and the body itself
		if not isinstance(msg_data, list) or len(msg_data) != 2:
			raise IMAPConnectionError("Unrecognized message: " + repr(msg_data))
		flags = msg_data[1]
		if not isinstance(msg_data[0], tuple) or len(msg_data[0]) != 2:
			raise IMAPConnectionError("Unrecognized message data: " + repr(msg_data[0]))
		body_data = msg_data[0][0]
		body = msg_data[0][1]

		# Turn the message body into an actual email instance
		message = email.message_from_string(body)
		return message

	def copy_message( self, message_id, dest_folder_name, debug=False ):
		"""Copy the message with the given ID to the given folder from the selected folder"""
		if debug:
			print( "Copying message {0} to {1}".format( message_id, dest_folder_name ) )
		self._ensure_connection()
	
		response = self.connection.copy(message_id, dest_folder_name)
		if response[0] != 'OK':
			raise IMAPConnectionError("Unable to copy message: " + repr(response) )
	
	def delete_message( self, message_id, debug=False ):
		"""Delete the given message from the given folder"""
		self._ensure_connection()

		if debug: print( "Deleting message {0}".format( message_id ) )

		response, info = self.connection.store(message_id, '+FLAGS', r'(\Deleted)')
		if response != 'OK':
			raise IMAPConnectionError("Failed to delete message: {0}\n{1}".format(response, info))

		response, info = self.connection.expunge()
		if response != 'OK':
			raise IMAPConnectionError("Failed to expunge messages: {0}\n{1}".format(response, info))
		
	def move_message( self, message_id, dest_folder_name, debug=False ):
		"""Move the message with the given ID to the given folder"""
		if debug:
			print( "Moving message {0} to {1}".format( message_id, dest_folder_name ))
		self.copy_message( message_id, dest_folder_name, debug=debug )
		self.delete_message( message_id, debug=debug )

