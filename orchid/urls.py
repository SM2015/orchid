from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
import forms_builder.forms.urls # add this import
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'orchid.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    (r'', include('core.urls')),
    url(r'^forms/', include(forms_builder.forms.urls)),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)