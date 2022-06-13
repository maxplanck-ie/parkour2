from django.conf import settings
from django.conf.urls import url
from django.contrib.auth import views as auth_views

from common import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^get_navigation_tree/$', views.get_navigation_tree, name='get_navigation_tree'),

    url(r'^login/$', auth_views.login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
    url(r'^password_reset/$', auth_views.password_reset, {
        'post_reset_redirect': '/password_reset/done/',
        'subject_template_name': 'email/password_reset_subject.txt',
        'email_template_name': 'email/password_reset_email.html',
        'from_email': settings.SERVER_EMAIL
    }, name='password_reset'),
    url(r'^password_reset/done/$', auth_views.password_reset_done),
    url(r'^password_reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, {'post_reset_redirect' : '/accounts/password/done/'}),
]
