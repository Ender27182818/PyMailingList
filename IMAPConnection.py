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
	def __init__(self, line, parent='/'):
		"""Parses the given data line into this object"""
		self.parent = parent
		self.flags, self.delimiter, self.mailbox_name = IMAPFolder.list_response_pattern.match(line).groups()
		self.mailbox_name = self.mailbox_name.strip('"')
		self.path = parent + self.mailbox_name
		
class IMAPConnection:
	"""Defines a connection to an IMAP server and allows some convenience functions"""
	def __init__(self, config_file):
		"""Create the connection using the provided config file"""
		# Read the config file
		config = ConfigParser.ConfigParser()
		config.read(config_file)
		self.hostname = config.get('server', 'hostname')
		self.port = config.getint('server', 'port')
		self.ssl = config.getboolean('server', 'ssl')
		self.username = config.get('account', 'username')
		self.password = config.get('account', 'password', True)

	def connect(self):
		"""Connects to the server specified in the config file"""
		print( "Connecting to {0}:{3} with username {1} and SSL {2}".format(self.hostname, self.username, self.ssl, self.port) )
		if( self.ssl ):
			self.connection = imaplib.IMAP4_SSL(self.hostname, self.port)
		else:
			self.connection = imaplib.IMAP4(self.hostname, self.port)
		self.connection.login(self.username, self.password)
		print( "Connected." )
	
	def get_folders(self, parent_folder='/'):
		"""Returns a list of the folders"""
		if( hasattr(self, 'folders') ):
			return self.folders
		if( not hasattr(self, 'connection') ):
			raise IMAPConnectionError("You need to connect first")
		
		if( parent_folder is '/'):
			response, data = self.connection.list()
		else:
			response, data = self.connection.list(directory=parent_folder)

		if( response != "OK" ):
			raise IMAPConnectionError("Bad response: " + response)
		
		# Parse the returned data
		self.folders = {}
		for line in data:
			new_folder = IMAPFolder( line, parent=parent_folder )
			self.folders[new_folder.path] = new_folder
		return self.folders
			
		

if __name__ == '__main__':
	
	conn = IMAPConnection('config.txt')
	conn.connect()
	folders = conn.get_folders()
	for k in folders.keys():
		print( k )
	
