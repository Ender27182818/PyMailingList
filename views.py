from django.http import HttpResponse
from django.shortcuts import render_to_response
from PyMailingList.models import Message

def index(request):
	return render_to_response('PyMailingList/index.html', {})