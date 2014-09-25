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
import forms_builder.forms.fields as ff
from django.core.cache import cache
import datetime, time
from dateutil.relativedelta import relativedelta
from collections import OrderedDict

ILLEGAL_FIELD_LABELS = ['User','Location','Score']

ALLOWED_FIELD_TYPES = [ff.TEXT, ff.TEXTAREA, ff.CHECKBOX]
FIELD_TYPE_NAMES = ["TEXT", "TEXTAREA", "CHECKBOX"]

DEFAULT_PASSING = 85.00

MONTH_CHOICES = (
    ('1', 'Jan'),
    ('2', 'Feb'),
    ('3', 'Mar'),
    ('4', 'Apr'),
    ('5', 'May'),
    ('6', 'Jun'),
    ('7', 'Jul'),
    ('8', 'Aug'),
    ('9', 'Sep'),
    ('10', 'Oct'),
    ('11', 'Nov'),
    ('12', 'Dec'),
)


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

class Image(Auditable, Noun):
    original_file = models.ImageField(upload_to=get_file_path, null=True, blank=True)
    internal_file = models.ImageField(upload_to='/', null=True, blank=True)

    def __unicode__(self):
        return "Image"
        url = self.get_file_url()
        if url == None:
            return "No File"
        else:
            return url

    def get_file_url(self):
        if self.original_file != None:
            return self.original_file.url
        else:
            return "pandas"

    def get_pandas(self):
        return "NOT PANDAS"

class Location(Auditable, Noun):
    title = models.TextField()
    position = GeopositionField()
    members = models.ManyToManyField(User, null=True, blank=True)
    images = models.ManyToManyField(Image, null=True, blank=True)
    indicators = models.ManyToManyField('Indicator', null=True, blank=True)
    verb_classes = [LocationDetailVerb, LocationUpdateVerb, LocationIndicatorListVerb, LocationImageCreateVerb]

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(viewname='location_detail', args=[self.id], current_app=APPNAME)

    def get_indicators(self):
        return self.indicators.all()

    def get_indicator_ids(self):
        return list(self.indicators.all().values_list('id', flat=True))

    def get_most_recent_image(self):
        try:
            return self.images.all().order_by('-created_at')[:1][0]
        except Exception as e:
            return None

    def get_series_key(self, indicator):
        return "series"+str(self.id)+"_"+str(indicator.id)

    def get_series(self, indicator):

        def convert_time_to_js(dt):
            return time.mktime(dt.timetuple())*1000

        key = self.get_series_key(indicator)
        value = cache.get(key)
        passing_percent = {}
        if value != None:
            print "Returning from cache"
            return value
        else:
            t = datetime.datetime.now()
            year_ago = t-relativedelta(months=12)
            #get all scores for this location/indicator from the last year
            scores = Score.objects.filter(indicator=indicator,location=self, datetime__gte=year_ago).order_by('datetime')
            #iterate over scores averaging them if there are more than one per month
            data = []
            for s in scores:
                #multiplied by 1000 because apparently js doesn't understand utc
                blob = [convert_time_to_js(s.datetime), s.score, s.passing]
                data.append(blob)
            i_series = {
                "name":indicator.title+" [GOAL: "+str(indicator.passing_percentage)+"%]",
                "data":data
            }
            #print "Saving to cache"
            #cache.set(key, i_series, None)

        return i_series

    def get_all_series(self):
        def percentage(part, whole, decimals=2):
            return 100 * float(part)/float(whole)
        t = datetime.datetime.now()
        year_ago = t-relativedelta(months=12)
        indicators = self.get_indicators()
        series = []
        for i in indicators:
            series.append(self.get_series(i))
            counts = OrderedDict()
            for s in series:
                #iterate over each blob
                for d in s["data"]:
                    print s
                    print d
                #if counts doesn't contain the timestamp key, add it
                    if not counts.has_key(d[0]):
                        #store 1 there if the score is passing
                        if d[2] == True:
                            counts[d[0]] = 1
                        #store 0 if it's failing
                        elif d[2] == False:
                            counts[d[0]] = 0
                    #otherwise update
                    else:
                        #add 1 if passing
                        if d[2] == True:
                            counts[d[0]]+=1
                    #do nothing if failing
            #iterate over counts, calculating counts[n]/indicators.count
            #raise Exception(counts)
        indicators_count = indicators.count()
        goals_met_data = [[k, percentage(v,indicators_count), percentage(v,indicators_count)>=DEFAULT_PASSING, DEFAULT_PASSING] for k, v in counts.iteritems()]
        goals_met_series = {
            "name":"PERCENT OF GOALS MET",
            "data":goals_met_data,
            "lineWidth":6,
            "dashStyle": 'longdash'
        }
        series.append(goals_met_series)
        return series

from forms_builder.forms.forms import FormForForm
from django.template.context import Context
from django_remote_forms.forms import RemoteForm

class Indicator(Auditable, Noun):
    title = models.TextField()
    form = models.ForeignKey(fm.Form, unique=True, null=True, blank=True)
    form_number = models.IntegerField(null=True, blank=True)
    passing_percentage = models.FloatField(default=85)
    maximum_monthly_records = models.IntegerField(default=20)
    verb_classes = [IndicatorListVerb, IndicatorDetailVerb, IndicatorUpdateVerb, FieldCreateVerb, FieldUpdateVerb]

    def __unicode__(self):
        return self.get_title()

    def get_absolute_url(self):
        return reverse(viewname='indicator_detail', args=[self.id], current_app=APPNAME)

    def get_builder_form_object(self):
        return self.form

    def get_form(self):
        c = Context()
        return FormForForm(self.get_builder_form_object(), c)

    def get_bool_field_ids(self):
        return self.get_builder_form_object().fields.filter(field_type=4).values_list('id', flat=True)

    def score_entry(self, entry):
        bool_field_ids = self.get_bool_field_ids()
        passing = []
        for f in entry.fields.all():
            if f.field_id in bool_field_ids:
                if f.value == u'True':
                    passing.append(f)
        return float(len(passing))/float(len(bool_field_ids))*100

    def get_serialized_builder_form(self):
        remote_form = RemoteForm(self.get_form())
        remote_form_dict = remote_form.as_dict()
        return remote_form_dict

    def get_serialized_fields(self):
        fields = []
        for f in self.form.fields.all().order_by("order"):
            if f.field_type in ALLOWED_FIELD_TYPES:
                blob = {
                    "id":f.id,
                    "field_type":FIELD_TYPE_NAMES[ALLOWED_FIELD_TYPES.index(f.field_type)],
                    "help_text":f.help_text,
                    "label":f.label,
                    "order":f.order,
                    "visible":f.visible
                }
                fields.append(blob)
        return fields

    def get_title(self):
        if self.form_number != None:
            return "#"+str(self.form_number)+" "+self.title
        else:
            return self.title

    def get_serialized(self):
        blob = {
            'id':self.id,
            'title':self.get_title(),
            'passing_percentage':self.passing_percentage,
            'maximum_monthly_records':self.maximum_monthly_records,
            'url':self.get_absolute_url(),
            'fields':self.get_serialized_fields()
        }

        return blob

    def get_column_headers(self):
        return ["Date"]+list(self.form.fields.all().order_by("order").values_list('label', flat=True))

    def get_filtered_entries(self, savedFilter, csv=False):
        # Store the index of each field against its ID for building each
        # entry row with columns in the correct order. Also store the IDs of
        # fields with a type of FileField or Date-like for special handling of
        # their values.
        user_field_id = self.form.fields.get(label="User").id
        print "user_field_id: "+str(user_field_id)
        input_user_values = []
        for u in savedFilter['input_user']:
            input_user_values.append(u.get_full_name())
        print "input_user_values: "+str(input_user_values)

        location_field_id = self.form.fields.get(label="Location").id
        print "location_field_id: "+str(location_field_id)
        location_values = list(savedFilter['locations'].values_list('title', flat=True))
        print "location_values: "+str(location_values)

        field_indexes = {}
        for field in self.form.fields.all().order_by("order"):
            field_indexes[field.id] = len(field_indexes)
        #get all field entries from the given form
        field_entries = fm.FieldEntry.objects.filter(entry__form=self.form
            ).order_by("-entry__id").select_related("entry")
        try:
            #if a date range is specified filter out any entries outside of the range
            if savedFilter.start_date and savedFilter.end_date:
                field_entries = field_entries.filter(
                    entry__entry_time__range=(savedFilter.start_date, savedFilter.end_date))
        except AttributeError as e:
            pass
        # Loop through each field value ordered by entry, building up each
        # entry as a row. Use the ``valid_row`` flag for marking a row as
        # invalid if it fails one of the filtering criteria specified.
        current_entry = None
        current_row = None
        valid_row = True
        num_columns = len(field_indexes)
        '''
        output = {}
        for field_entry in field_entries:
            #if output doesn't contain a blob for the formentry, create one with enough columns 
            #find the appropriate blob and 
        '''

        for field_entry in field_entries:
            #print field_entry.id
            #print "field_entry.field_id: "+str(field_entry.field_id)
            field_value = field_entry.value or "N/D"
            if field_value == "True":
                field_value = "Yes"
            elif field_value == "False":
                field_value = "No"
            #print field_value
            if field_entry.entry_id != current_entry:
                # New entry, write out the current row and start a new one.
                if valid_row and current_row is not None:
                    if not csv:
                        current_row.insert(0, current_entry)
                    yield current_row
                current_entry = field_entry.entry_id
                current_row = [""] * num_columns
                valid_row = True
                current_row = [field_entry.entry.entry_time]+current_row
            #print "field_entry.field_id: "+str(field_entry.field_id)
            if len(input_user_values) >0:
                if field_entry.field_id == user_field_id:
                    if not field_entry.value in input_user_values:
                        valid_row = False

            if field_entry.field_id == location_field_id:
                if not unicode(field_entry.value) in location_values:
                    valid_row = False

                
            # Only use values for fields that were selected.
            try:
                #shift over 1 to make room for the date column
                current_row[field_indexes[field_entry.field_id]+1] = field_value
                #print current_row
            except KeyError:
                print "KeyError current_row["+str(field_indexes)+"["+str(field_entry.id)+"]]"+fm.Field.objects.get(id=field_entry.field_id).label
                pass

        # Output the final row.
        if valid_row and current_row is not None:
            if not csv:
                current_row.insert(0, current_entry)
            yield current_row

class Score(models.Model):
    user = models.ForeignKey(User)
    indicator = models.ForeignKey(Indicator)
    location = models.ForeignKey(Location)
    score = models.FloatField(default=85)
    passing = models.BooleanField()
    entry_count = models.IntegerField()
    passing_entry_count = models.IntegerField()
    month = models.CharField(max_length=2, choices=MONTH_CHOICES)
    year = models.IntegerField()
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return str(self.score)+" : "+str(self.datetime)

    def get_status(self):
        raise Exception("hello")
        if passing == True:
            raise Exception("hello")
            return "passing"
        else:
            return "failing"

    def calculate_score(self):
        try:
            self.score = float(self.passing_entry_count)/self.entry_count*100
        except ZeroDivisionError as e:
            pass

    def merge(self, incoming_score):
        if incoming_score.indicator != self.indicator:
            raise Exception("Can't Merge Scores From Different Indicators")
        if incoming_score.indicator != self.indicator:
            raise Exception("Can't Merge Scores From Different Locations")
        self.entry_count += incoming_score.entry_count
        self.passing_entry_count += incoming_score.passing_entry_count
        self.calculate_score()
    





