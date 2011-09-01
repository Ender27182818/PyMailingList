import os
import sys

path = ['/home/eli/waug-mail' ]
for p in path:
	if p not in sys.path:
		sys.path.append(p)

def application( environ, start_response ):
	response_body = 'Welcome to PyMailingList.\nThe request method was {0}'.format( environ['REQUEST_METHOD'] )
	status = '200 OK'
	response_headers = [('Content-Type', 'text/plain'),
			('Content-Length', str(len(response_body)))]

	start_response(status, response_headers)
	return [response_body]
