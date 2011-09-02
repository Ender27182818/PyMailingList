from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('PyMailingList.views',
	(r'^$', 'index'),
	(r'^/$', 'index'),
	(r'^message/(?P<message_id>\d+)/$', 'show_message'),
	url(r'^admin/', include(admin.site.urls)),
)
