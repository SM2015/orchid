from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
import core.views as cv
from django.views.decorators.cache import cache_page

urlpatterns = patterns('',
    url(r'^$', cv.LandingView.as_view(), name="landing"),
    ('^activity/', include('actstream.urls')),

    url(r'user/create/$', cv.UserCreateView.as_view(), name='make_new_user'),
    url(r'user/login/$', cv.UserLoginView.as_view(), name='user_login'),
    url(r'user/logout/$', cv.UserLogoutView.as_view(), name='user_logout'),

    url(r'progress/(?P<tag>\w+)$', cv.ProgressListView.as_view(), name='progress_list'),

    url(r'scores/list/$', cv.ScoresDetailView.as_view(), name='scores_list'),
    url(r'scores/month/(?P<month>\d+)/year/(?P<year>\d+)/list/$', cv.ScoresDetailView.as_view(), name='scores_date_list'),

    url(r'location/create/$', cv.LocationCreateView.as_view(), name='location_create'),
    url(r'location/(?P<pk>\d+)/detail/$', cv.LocationDetailView.as_view(), name='location_detail'),
    url(r'location/(?P<pk>\d+)/update/$', cv.LocationUpdateView.as_view(), name='location_update'),
    url(r'location/list/$', cv.LocationListView.as_view(), name='location_list'),
    url(r'location/(?P<location_pk>\d+)/score/upload/$', cv.LocationScoreUploadView.as_view(), name='location_score_upload'),
    url(r'location/(?P<pk>\d+)/visualize/$', cv.LocationVisualize.as_view(), name='location_visualize'),
    url(r'location/(?P<location_pk>\d+)/indicator/(?P<pk>\d+)/record/create/$', cv.IndicatorRecordCreateView.as_view(), name='indicator_record_create'),
    url(r'location/(?P<location_pk>\d+)/indicator/(?P<pk>\d+)/record/upload/$', cv.IndicatorRecordUploadView.as_view(), name='indicator_record_upload'),
    url(r'location/(?P<location_pk>\d+)/indicator/(?P<pk>\d+)/visualize/$', cv.LocationIndicatorVisualize.as_view(), name='location_indicator_visualize'),
    url(r'location/(?P<pk>\d+)/image/create/$', cv.LocationImageCreateView.as_view(), name='location_image_create'),
    url(r'location/(?P<pk>\d+)/indicator/list/$', cv.LocationIndicatorListlView.as_view(), name='location_indicator_list'),
    url(r'entries/filter/$', cv.EntriesFilterView.as_view(), name='entries_filter'),

    url(r'indicator/(?P<pk>\d+)/detail/$', cv.IndicatorDetailView.as_view(), name='indicator_detail'),
    url(r'indicator/(?P<pk>\d+)/update/$', cv.IndicatorUpdateView.as_view(), name='indicator_update'),
    url(r'indicator/create/$', cv.IndicatorCreateView.as_view(), name='indicator_create'),
    url(r'indicator/list/$', cv.IndicatorListView.as_view(), name='indicator_list'),

    url(r'indicator/(?P<pk>\d+)/field/create/$', cv.FieldCreateView.as_view(), name='field_create'),
    url(r'indicator/(?P<indicator_pk>\d+)/field/(?P<pk>\d+)/update/$', cv.FieldUpdateView.as_view(), name='field_update'),


)


