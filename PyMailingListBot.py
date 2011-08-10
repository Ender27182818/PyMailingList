#!/usr/bin/python
from IMAPConnection import IMAPConnection

if __name__ == '__main__':
	conn = IMAPConnection('config.txt')
	conn.connect()
	message_count = conn.select_folder("INBOX")
	message_ids = conn.get_message_ids()
	for message_id in message_ids:
		message = conn.get_message(message_id)
		if( message['subject'].lower() == 'subscribe' ):
			print("Found subscription request from " + message['from'])
	
