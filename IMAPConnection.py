#!/usr/bin/python
import imaplib
import ConfigParser
from pprint import pprint
import re

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
	def __init__(self, config_file):
		"""Create the connection using the provided config file"""
		self.folders = {}
		self.folders['/'] = IMAPFolder('/', None)

		# Read the config file
		config = ConfigParser.ConfigParser()
		config.read(config_file)
		self.hostname = config.get('server', 'hostname')
		self.port = config.getint('server', 'port')
		self.ssl = config.getboolean('server', 'ssl')
		self.username = config.get('account', 'username')
		self.password = config.get('account', 'password', True)
	
	def _ensure_connection(self):
		"""Ensures that a connection is made and raises an error if not"""
		if( not hasattr(self, 'connection') ):
			raise IMAPConnectionError("You need to connect first")

	def connect(self):
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

	def select_folder(self, folder_name):
		"""Selects the given folder causing all transactions to occur on that folder. Returns all messages in the given mailbox on success, raises an exception on failure"""
		self._ensure_connection()
			
		response, data = self.connection.select(folder_name)
		if( reponse != "OK" ):
			raise IMAPConnectionError("Bad response: " + response)
		if( reponse == "NO" ):
			raise IMAPConnectionError("Specified folder {0} does not exist".format(folder_name))

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
		

if __name__ == '__main__':
	
	conn = IMAPConnection('config.txt')
	conn.connect()
	folders = conn.get_folders()
	for k in folders.keys():
		print( k )
	
