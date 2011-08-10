#!/usr/bin/python
import imaplib
import ConfigParser
from pprint import pprint

def open_connection(verbose=False):
	# Read the config file
	config = ConfigParser.ConfigParser()
	config.read('config.txt')
	hostname = config.get('server', 'hostname')
	port = config.getint('server', 'port')
	ssl = config.getboolean('server', 'ssl')
	username = config.get('account', 'username')
	password = config.get('account', 'password', True)

	print( "Connecting to {0}:{3} with username {1} and SSL {2}".format(hostname, username, ssl, port) )
	if( ssl ):
		connection = imaplib.IMAP4_SSL(hostname, port)
	else:
		connection = imaplib.IMAP4(hostname, port)
	connection.login(username, password)
	return connection
	

if __name__ == '__main__':
	connection = open_connection()
	try:
		typ, data = connection.list()
		print( "Response code:", typ )
		pprint( data )
	finally:
		connection.logout()
	
