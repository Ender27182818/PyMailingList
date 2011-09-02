from django.http import HttpResponse
from django.shortcuts import render_to_response
from PyMailingList.models import Message

def index(request):
	messages = Message.objects.all()
	return render_to_response('PyMailingList/index.html', {'messages':messages})

def show_message(request, message_id):
	message = Message.objects.get(pk=message_id)
	return render_to_response('PyMailingList/show_message.html', {'message':message})
