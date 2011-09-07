import smtplib
import ConfigParser
import email
from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE

class SMTPConnectionError(Exception):
	"""Simple class for all SMTPConnection errors"""
	def __init__(self, value):
		self.parameter = value
	def __str__(self):
		return repr(self.parameter)

class SMTPConnection:
	"""Defines a connection to an IMAP server and allows some convenience functions"""
	def __init__(self, config_file, debug=False):
		"""Create the connection using the provided config file"""
		# Read the config file
		config = ConfigParser.ConfigParser()
		config.read(config_file)
		self.hostname = config.get('smtp_server', 'hostname')
		try:
			self.port = config.getint('smtp_server', 'port')
		except ConfigParser.NoOptionError:
			self.port = None
		self.ssl = config.getboolean('smtp_server', 'ssl')
		self.username = config.get('smtp_account', 'username')
		self.password = config.get('smtp_account', 'password', True)
		self.bot_name = config.get('bot', 'name')
		self.bot_address = config.get('bot', 'address')
	
	def _ensure_connection(self):
		"""Ensures that a connection is made and raises an error if not"""
		self.connect()

	def connect(self, debug=False):
		"""Connects to the server specified in the config file"""
		print( "Connecting SMTP server {0}:{3} with username {1} and SSL {2}".format(self.hostname, self.username, self.ssl, self.port) )
		if( self.ssl ):
			self.connection = smtplib.SMTP_SSL(self.hostname, self.port)
		else:
			self.connection = smtplib.SMTP(self.hostname, self.port)
		self.connection.login(self.username, self.password)
		print( "Connected." )
	
	def send_message( self, to, subject, body, debug=False ):
		"""Send a message with the given subject and body to the given recipient(s). Return true if it worked, false otherwise"""
		self._ensure_connection()
	
		if debug:
			print( "Sending message '{0}' to {1}".format( subject[:40], to ) )

		# If it's just a string, send it as a plain string
		if isinstance(body, str):
			if debug: print( "Sending as plain string" )
			msg = email.MIMEText.MIMEText(body, 'plain')
			msg['Subject'] = subject
			msg['From'] = self.bot_name
			msg['To'] = ', '.join(to)
			if debug: print( "  sendmail( {0}, {1}, {2} )".format( self.bot_address, to, msg.as_string() ) )
			self.connection.sendmail(self.bot_address, to, msg.as_string())
			self.connection.quit()
			return True
		# Try some different types
		else:
			# If it's a list of things, try that
			try:
				msg = MIMEMultipart()
				msg['Subject'] = subject
				msg['From'] = self.bot_name
				msg['To'] = self.bot_address
				for item in body:
					if isinstance(item, email.message.Message):
						msg.attach( item )
				if debug: print( "  sendmail( {0}, {1}, {2} )".format( self.bot_address, to, msg.as_string()[:30] ) )
				self.connection.sendmail(self.bot_address, to, msg.as_string())
				self.connection.quit()
				return True
			except TypeError:
				self.connection.quit()
				return False
		
