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

def signal_handler(signal, frame):
	print( "Exiting..." )
	flush_subscribers()
	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def flush_subscribers():
	"""Flushes the subscribers list to the pickle file"""
	f = open(SUBSCRIBERS_FILE, 'w')
	pickle.dump( subscribers, f )
	f.close()
	
def add_subscriber(address):
	"""Adds the given address to the subscribers file"""
	if address not in subscribers:
		subscribers.append(address)
		flush_subscribers()
	
def remove_subscriber(address):
	"""Adds the given address to the subscribers file"""
	if address in subscribers:
		subscribers.remove(address)
		flush_subscribers()
	
def _parse_commandline():
	"""Parses the commandline parameters"""
	parser = OptionParser(usage="PyMailingListBot is a program for having a mailing list on an IMAP/SMTP server combination", version=str(VERSION))
	parser.add_option( "--debug", dest="debug", default=False, action="store_true")
	(options, args) = parser.parse_args()
	return options

def handle_subscribe_request( imap_conn, smtp_conn, message_id, from_address ):
	"""Handles when a subscribe request message is received"""
	print("Found subscription request from " + from_address)
	add_subscriber(from_address)
	worked = smtp_conn.send_message( from_address, 'Subscription Request', "You have been subscribed. Thank you. You may unsubscribe any time by replying to this message with the subject 'unsubscribe'" )
	if not worked:
		print("Failed to properly handle subscription request")
		sys.exit(0)
	imap_conn.move_message( message_id, "Subscriptions" )
	
def handle_unsubscribe_request( imap_conn, smtp_conn, message_id, from_address ):
	print("Found unsubscribe request from " + from_address)
	remove_subscriber(from_address)
	worked = smtp_conn.send_message( from_address, 'Unsubscription Request', "You have been un-subscribed. Thank you. If you ever wish to re-subscribe you may do so by sending a message to this mailing list with the subject 'subscribe'" )
	if not worked:
		print("Failed to properly handle un-subscription request")
		sys.exit(0)
	imap_conn.move_message( message_id, "Subscriptions" )

def handle_message( imap_conn, smtp_conn, message_id, message ):
	# Handle sending a message out
	if '[android-users]' in message['subject']:
		subject = message['subject']
	else:
		subject = '[android-users] ' + message['subject']
	worked = smtp_conn.send_message( 'android-users-group@wavelink.com', subject, message.get_payload(), bcc=subscribers )
	if not worked:
		print("Failed to properly forward message")
		sys.exit(0)
	imap_conn.move_message( message_id, "Archive" )
	print( "Handled forwarding message '{0}' from {1} to the list".format( subject, message['from'] ) )
	
if __name__ == '__main__':
	options = _parse_commandline()
	if options.debug:
		print("Debug enabled")
	# Read in the existing subscribers
	try:
		subs_file = open(SUBSCRIBERS_FILE)
		subscribers = pickle.load(subs_file)
		subs_file.close()
		print("Read in the following subscribers:")
		for s in subscribers:
			print("  " + s)
	except IOError, e:
		print("New subscribers file")
	imap_conn = IMAPConnection('config.txt')
	imap_conn.connect(debug=options.debug)
	smtp_conn = SMTPConnection('config.txt')
	smtp_conn.connect(debug=options.debug)
	message_count = imap_conn.select_folder("INBOX")
	while( True ):
		try:
			message_ids = imap_conn.get_message_ids(debug=options.debug)
			if len(message_ids) > 0:
				message_id = message_ids[0]
				message = imap_conn.get_message(message_id)
				from_address = message['from'].lower()
				subject = message['subject'].lower()
				if( subject == 'subscribe' ):
					handle_subscribe_request( imap_conn, smtp_conn, message_id, from_address )
				elif subject == 'unsubscribe':
					handle_unsubscribe_request( imap_conn, smtp_conn, message_id, from_address )
				else:
					handle_message( imap_conn, smtp_conn, message_id, message )
			else:
				time.sleep(60)
	
		except IMAPConnectionError, e:
			print("IMAPConnection error: " + repr(e))
		except SMTPConnectionError, e:
			print("SMTPConnection error: " + repr(e))
		
			
	
