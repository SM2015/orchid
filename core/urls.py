from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
import core.views as cv

urlpatterns = patterns('',
    url(r'^$', cv.LandingView.as_view(), name="landing"),
    ('^activity/', include('actstream.urls')),

    url(r'user/create/$', cv.UserCreateView.as_view(), name='user_ceate'),
    url(r'user/login/$', cv.UserLoginView.as_view(), name='user_login'),
    url(r'user/logout/$', cv.UserLogoutView.as_view(), name='user_logout'),

    url(r'location/create/$', cv.LocationCreateView.as_view(), name='location_create'),
    url(r'location/list/$', cv.LocationListView.as_view(), name='location_list'),

    url(r'indicator/create/$', cv.IndicatorCreateView.as_view(), name='indicator_create'),

    url(r'indicator/(?P<pk>\d+)/field/create/$', cv.FieldCreateView.as_view(), name='field_create'),
)


