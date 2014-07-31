from django.conf import settings
from django.contrib import admin
import core.models as cm

admin.site.register(cm.Location)
admin.site.register(cm.Indicator)
admin.site.register(cm.Image)
admin.site.register(cm.Score)