from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from carteblanche.base import Verb, Noun
#from carteblanche.django.mixins import DjangoVerb
from core.verbs import DjangoVerb, availability_login_required
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
import json
from django.contrib.contenttypes.models import ContentType
import actstream
from django.db.models import Q
import uuid
import os
from geoposition.fields import GeopositionField
from core.verbs import *
import forms_builder.forms.models as fm


def get_file_path(instance, filename):
    blocks = filename.split('.')
    ext = blocks[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    instance.name = blocks[0]
    return os.path.join('uploads/', filename)

@python_2_unicode_compatible
class Auditable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    changed_by = models.ForeignKey(User, null=True, blank=True, related_name="%(app_label)s_%(class)s_related")

    def __str__(self):
        return "auditable string goes here"

    @property
    def _history_user(self):
        return self.changed_by

    @_history_user.setter
    def _history_user_setter(self, value):
        self.changed_by = value

    def get_action_stream(self):
        stream = actstream.models.Action.objects.filter(self.get_action_stream_query()).order_by('-timestamp')
        return stream

    def get_action_stream_query(self):
        post_type = ContentType.objects.get_for_model(self)
        query = Q(target_object_id=self.id, target_content_type=post_type)
        return query

    def get_class_name(self):
        return self.__class__.__name__

    class Meta:
        abstract = True

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)

User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])

class Location(Auditable, Noun):
    title = models.CharField(max_length=300)
    position = GeopositionField()
    members = models.ManyToManyField(User)
    verb_classes = [IndicatorRecordCreateVerb]

    def __str__(self):
        return self.title

from forms_builder.forms.forms import FormForForm
from django.template.context import Context

class Indicator(Auditable, Noun):
    title = models.CharField(max_length=300)
    form = models.ForeignKey(fm.Form, unique=True, null=True, blank=True)
    passing_percentage = models.FloatField(default=85)
    verb_classes = [IndicatorDetaileVerb, FieldCreateVerb]

    def __str__(self):
        return self.title

    def get_builder_form_object(self):
        return self.form

    def get_form(self):
        c = Context()
        return FormForForm(self.get_builder_form_object(), c)

class Summary(Auditable, Noun):
    user = models.ForeignKey(User, unique=True)




