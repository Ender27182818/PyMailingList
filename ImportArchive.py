#!/usr/bin/python
from IMAPConnection import IMAPConnection, IMAPConnectionError
from SMTPConnection import SMTPConnection, SMTPConnectionError
import pickle
import signal
import time
import sys
from optparse import OptionParser

VERSION = 0.1
SUBSCRIBERS_FILE = 'subscribers.pickle'
subscribers = []

def _parse_commandline():
	"""Parses the commandline parameters"""
	parser = OptionParser(usage="ImportArchive is a program for importing a mailing list archive into the DjangoSite", version=str(VERSION))
	parser.add_option( "--debug", dest="debug", default=False, action="store_true")
	(options, args) = parser.parse_args()
	return options

def handle_message( imap_conn, message_id, message ):
	"""Handle a message by putting it in the Django database""" 
	from_address = message['from'].lower()
	subject = message['subject'].lower()
	if '[android-users]' in message['subject']:
		subject = message['subject']
	else:
		subject = '[android-users] ' + message['subject']
	print( "Handling message from {0}: {1}...".format( from_address, subject[:50] ) )

	
if __name__ == '__main__':
	options = _parse_commandline()
	if options.debug:
		print("Debug enabled")
	
	imap_conn = IMAPConnection('config.txt')
	imap_conn.connect(debug=options.debug)
	message_count = imap_conn.select_folder("Archive")
	print( "Found {0} messages in the archive".format( message_count ) )
	try:
		message_ids = imap_conn.get_message_ids(debug=options.debug)
		if options.debug: print( "Got the following message ids: {0}".format(message_ids))
		for message_id in message_ids:
			if options.debug: print( "Getting message {0}".format( message_id ) )
			message = imap_conn.get_message(message_id)
			handle_message( imap_conn, message_id, message )
	except IMAPConnectionError, e:
		print("IMAPConnection error: " + repr(e))
		
			
	
