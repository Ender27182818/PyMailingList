#!/usr/bin/python
from IMAPConnection import IMAPConnection

if __name__ == '__main__':
	conn = IMAPConnection('config.txt')
	conn.connect()
	message_count = conn.select_folder("INBOX")
	print("Found {0} messages in INBOX".format(message_count))
	message_ids = conn.get_message_ids()
	print(message_ids)
	
