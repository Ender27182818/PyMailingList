#!/usr/bin/python
from IMAPConnection import IMAPConnection

if __name__ == '__main__':
	conn = IMAPConnection('config.txt')
	conn.connect()
	folders = conn.get_folders()
	for k in folders.keys():
		print( k )
	
