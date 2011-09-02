#!/usr/bin/python
from IMAPConnection import IMAPConnection, IMAPConnectionError
from SMTPConnection import SMTPConnection, SMTPConnectionError
from django.core.management import setup_environ
import pickle
import datetime
import signal
import time
import sys
import os
import re
from optparse import OptionParser

VERSION = 0.1
SUBSCRIBERS_FILE = 'subscribers.pickle'
subscribers = []

parent_path = os.path.abspath('..')
if parent_path not in sys.path:
	sys.path.append( parent_path )
import settings
setup_environ(settings)
from PyMailingList.models import Message
print( "Showing {0} messages in Django store".format( len(Message.objects.all() ) ) )

def _parse_commandline():
	"""Parses the commandline parameters"""
	parser = OptionParser(usage="ImportArchive is a program for importing a mailing list archive into the DjangoSite", version=str(VERSION))
	parser.add_option( "--debug", dest="debug", default=False, action="store_true")
	(options, args) = parser.parse_args()
	return options

def get_message_content(message):
	"""Given an email message, get the base content we want to store or None if it has no valid content"""
	if not message.is_multipart():
		if 'image' in message.get_content_type():
			return None
		else:
			return message.get_payload()
	
	for p in message.get_payload():
		content = get_message_content(p)
		if content is not None and p.get_content_type() is "text/plain":
			return content
		
def _split_from(f):
	"""Given a from line like 'Eli Ribble <eribble@somewhere.com>' return a tuple of 'Eli Ribble' and 'eribble@somewhere.com'"""
	m = re.search(r'(?P<sender_name>[\w ]+) <(?P<sender_address>[\w@\.]+)', f)
	if m is None:
		raise Exception("Couldn't match {0} with existing regex".format(f))
	d = m.groupdict()
	return (d['sender_name'], d['sender_address'])
	
def handle_message( imap_conn, message_id, message ):
	"""Handle a message by putting it in the Django database""" 
	f = message['from']
	sender_name, sender_email = _split_from(f)
	subject = message['subject']
	if '[android-users]' not in subject:
		subject = '[android-users] ' + subject
	content = message.get_payload()
	d = message['Date']
	# Remove the timezone specifier since we don't have a good way to handle it yet
	d = d[:d.rfind(' ')]
	sent_date = datetime.datetime.strptime( d, '%a, %d %b %Y %H:%M:%S')
	# Get the message content
	content = get_message_content(message)
	if content is None:
		content = "No valid content found"
			
		
	print( "Handling message from {0}: {1}...".format( sender_name, subject[:50] ) )
	new_message = Message( pk=message_id,sent_date=sent_date, sender=sender_email, sender_name=sender_name, content=content)
	new_message.save()

	
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
		
			
	
