from django.db import models

# Create your models here.
class Message(models.Model):
	sent_date = models.DateTimeField('date sent')
	sender = models.CharField(max_length=100, help_text="The email address of the sender of the email. ie joe_smith@nowhere.com")
	sender_name = models.CharField(max_length=100, blank=True, help_text="The name of the sender. ie Joe Smith")
	subject = models.CharField(max_length=300, blank=True, help_text="The message subject")
	content = models.TextField()
