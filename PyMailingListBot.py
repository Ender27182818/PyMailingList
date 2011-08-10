#!/usr/bin/python
from IMAPConnection import IMAPConnection
from SMTPConnection import SMTPConnection

if __name__ == '__main__':
	imap_conn = IMAPConnection('config.txt')
	imap_conn.connect()
	smtp_conn = SMTPConnection('config.txt')
	smtp_conn.connect()
	message_count = imap_conn.select_folder("INBOX")
	message_ids = imap_conn.get_message_ids()
	for message_id in message_ids:
		message = imap_conn.get_message(message_id)
		if( message['subject'].lower() == 'subscribe' ):
			print("Found subscription request from " + message['from'])
			smtp_conn.send_message( message['from'], 'Subscription Request', "You have been subscribed. Thank you" )
		
			
	
