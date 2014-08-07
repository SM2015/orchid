from __future__ import unicode_literals
from future.builtins import bytes, open
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, FormView
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic import DetailView
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from uuid import uuid4
from carteblanche.base import Noun
from carteblanche.mixins import NounView
#from core.verbs import NounView
import core.models as cm
import core.forms as cf
import core.tasks as ct
from django.db.models.signals import post_save
from actstream import action
import actstream.models as am
from django.contrib.auth import authenticate, login, logout
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.conf import settings
import decimal
import forms_builder.forms.models as fm
from forms_builder.forms.admin import FormAdmin
import json
from django.http import HttpResponse
from django.views.generic.edit import CreateView
import datetime

#do weird stuff to mAake user names nou usernames show up
def user_new_unicode(self):
    return self.get_full_name()
# Replace the __unicode__ method in the User class with out new implementation
User.__unicode__ = user_new_unicode 


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)

class SiteRootView(NounView):
    def get_noun(self, **kwargs):
        siteroot = cm.SiteRoot()
        return siteroot

class MessageView(SiteRootView, TemplateView):
    template_name = 'base/messages.html'
    message = 'Message goes here.'

    def get_context_data(self, **kwargs):

        # Call the base implementation first to get a context
        context = super(MessageView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['message'] = self.message
        return context


class LandingView(SiteRootView, TemplateView):
    template_name = 'base/bootstrap.html'


class BootstrapView(TemplateView):
    template_name = 'grid.html'


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return self.render_to_json_response(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'pk': self.noun.pk,
            }
            return self.render_to_json_response(data)
        else:
            return response

class UserCreateView(SiteRootView, FormView):
    model = User
    template_name = 'base/form.html'
    form_class = cf.RegistrationForm

    def form_valid(self, form):
        user = User.objects.create_user(uuid4().hex[:30], form.cleaned_data['email'], form.cleaned_data['password1'])
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.save()
        self.object = user
        locations = form.cleaned_data['locations']
        for l in locations:
            l.members.add(user)
            l.save()
        return super(UserCreateView, self).form_valid(form)

    def get_success_url(self):
        action.send(self.request.user, verb='created user', action_object=self.object, target=self.request.user)
        return reverse(viewname='make_new_user', current_app='core')

    def get_success_message(self, cleaned_data):
        first_name = cleaned_data['first_name']
        last_name = cleaned_data['last_name']
        locations = list(cleaned_data['locations'])
        location_names = ""
        for l in locations[:-1]:
            location_names+=l.title+", "
        location_names+=" and "+locations[-1].title+"."
        return first_name+" "+last_name+" now has an account. They are assigned to "+location_names+" Make another new user or return to the indicator."

class UserLoginView(SiteRootView, FormView):
    template_name = 'base/form.html'
    form_class = cf.LoginForm
    success_url = '/'

    def form_valid(self, form):
        user = form.user_cache
        login(self.request, user)
        form.instance = user
        if self.request.is_ajax():
            context = {
                'status':'success',
                'userid' : user.id,
                'sessionid': self.request.session.session_key
                }
            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)
        else:
            return super(UserLoginView, self).form_valid(form)

    def form_invalid(self, form):
        response = super(UserLoginView, self).form_invalid(form)
        if self.request.is_ajax():
            return self.render_to_json_response({"errors":form.errors, "status":"failure",})
        else:
            return response

    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)




class UserLogoutView(SiteRootView, TemplateView):
    template_name = 'bootstrap.html'

    def get(self, request, **kwargs):
        #if the user has no payment methods, redirect to the view where one can be created
        logout(self.request)
        return HttpResponseRedirect(reverse(viewname='location_list', current_app='core'))


class LocationCreateView(SiteRootView, CreateView):
    model = cm.Location
    template_name = 'base/form.html'
    fields = '__all__'
    form_class = cf.LocationForm

    def get(self, request, *args, **kwargs):
        supes = super(LocationCreateView, self).get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        if self.request.is_ajax():
            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)

        return supes

    def get_success_url(self):
        action.send(self.request.user, verb='created location', action_object=self.object)
        return reverse(viewname='location_detail', args=(self.object.id,), current_app='core')

class LocationListView(SiteRootView, TemplateView):
    model = cm.Location    
    template_name = 'overview/map.html'

    def get_context_data(self, **kwargs):
        context = super(LocationListView, self).get_context_data(**kwargs)
        output = []
        if self.request.user.is_staff:
            locations = cm.Location.objects.all()
        else:
            locations = self.request.user.location_set.all()
        for l in locations:
            blob = {
                'id':l.id,
                'lattitude':l.position.latitude,
                'longitude':l.position.longitude,
                'title':l.title,
                'indicator_ids':l.get_indicator_ids()
            }
            output.append(blob)
        context['locations'] = output
        context['stream'] = am.Action.objects.all()[:40]
        return context

    def get(self, request, *args, **kwargs):
        supes = super(LocationListView, self).get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        if self.request.is_ajax():
            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)

        return supes

class LocationView(NounView):
    def get_noun(self, **kwargs):
        return cm.Location.objects.get(id=self.kwargs['pk'])

class LocationUpdateView(LocationView, UpdateView):
    model = cm.Location
    template_name = 'base/form.html'
    success_url = '/'
    form_class = cf.LocationForm

    def get_success_url(self):
        action.send(self.request.user, verb='updated location', action_object=self.get_noun())
        return reverse(viewname='location_detail', args=(self.noun.id,), current_app='core')

class LocationDetailView(LocationView, TemplateView):
    model = cm.Location    
    template_name = 'location/detail.html'

    def get_context_data(self, **kwargs):
        context = super(LocationDetailView, self).get_context_data(**kwargs)
        most_recent_image =self.noun.get_most_recent_image()
        if most_recent_image != None:
            context["most_recent_image_url"] = most_recent_image.get_file_url()
        context["stream"] = self.noun.get_action_stream()[:40]
        return context

class LocationIndicatorListlView(LocationView, TemplateView):
    model = cm.Location    
    template_name = 'location/indicators.html'

    def get_context_data(self, **kwargs):
        context = super(LocationIndicatorListlView, self).get_context_data(**kwargs)
        context['stream'] = self.noun.get_action_stream()[:40]
        context['indicators'] = self.noun.indicators.all().order_by('form_number')
        context['ILLEGAL_FIELD_LABELS'] = cm.ILLEGAL_FIELD_LABELS
        return context

    def get(self, request, *args, **kwargs):
        supes = super(LocationIndicatorListlView, self).get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        if self.request.is_ajax():
            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)
        return supes

try:
    import xlwt
    XLWT_INSTALLED = True
    XLWT_DATETIME_STYLE = xlwt.easyxf(num_format_str='MM/DD/YYYY HH:MM:SS')
except ImportError:
    XLWT_INSTALLED = False
from io import BytesIO, StringIO
from forms_builder.forms.utils import now, slugify
class EntriesFilterView(SiteRootView, FormView):
    model = cm.Location    
    template_name = 'base/form.html'
    form_class = cf.SavedFilterForm

    def form_valid(self, form):
        indicator = form.cleaned_data['indicator']
        entries = indicator.get_filtered_entries(form.cleaned_data)
        context = {
            "columns":indicator.get_column_headers(),
            "entries":entries,
            "available_verbs": self.noun.get_available_verbs(self.request.user),
            "filter":form.cleaned_data
            }
        return render_to_response('indicator/entries.html',
                          context,
                          context_instance=RequestContext(self.request))

    def form_valid(self, form):
        indicator = form.cleaned_data['indicator']
        columns = indicator.get_column_headers()
        if form.cleaned_data['export']==True:
            response = HttpResponse(mimetype="application/vnd.ms-excel")
            fname = "%s-%s.xls" % ("QI Data Export", slugify(now().ctime()))
            attachment = "attachment; filename=%s" % fname
            response["Content-Disposition"] = attachment
            queue = BytesIO()
            workbook = xlwt.Workbook(encoding='utf8')
            sheet = workbook.add_sheet(indicator.title[:31])
            for c, col in enumerate(columns):
                sheet.write(0, c, col)
            for r, row in enumerate(indicator.get_filtered_entries(form.cleaned_data,csv=True)):
                for c, item in enumerate(row):
                    if isinstance(item, datetime.datetime):
                        item = item.replace(tzinfo=None)
                        sheet.write(r + 2, c, item, XLWT_DATETIME_STYLE)
                    else:
                        sheet.write(r + 2, c, item)
            workbook.save(queue)
            data = queue.getvalue()
            response.write(data)
            return response
        else:
            context = {
            "columns":columns,
            "entries":indicator.get_filtered_entries(form.cleaned_data,csv=False),
            "available_verbs": self.noun.get_available_verbs(self.request.user),
            "filter":form.cleaned_data
            }
            return render_to_response('indicator/entries.html',
                              context,
                              context_instance=RequestContext(self.request))


from dateutil.relativedelta import relativedelta

class ScoresDetailView(SiteRootView, TemplateView):   
    template_name = 'overview/scores.html'

    def get_context_data(self, **kwargs):
        context = super(ScoresDetailView, self).get_context_data(**kwargs)
        NOT_ASSIGNED_STRING = "N/A"
        try:
            month = int(self.kwargs['month'])
            year = int(self.kwargs['year'])
        except Exception as e:
            d = datetime.datetime.now()
            month = d.month
            year = d.year
        queryset = cm.Indicator.objects.all().order_by("form_number")
        columns = list(queryset.values_list('title', flat=True))
        indicator_ids = list(queryset.values_list('id', flat=True))
        #get all scores for this month
        rows = {}
        for l in cm.Location.objects.all():
            rows[l.id] = [l.title]+([NOT_ASSIGNED_STRING]*len(columns))
        #add space to the begininbg of columns for the location names
        columns = ["Location"]+columns
        for s in cm.Score.objects.filter(month=str(month), year=year):               
            #add the score object to the table if it exists
            indicator_index = indicator_ids.index(s.indicator.id)+1
            if rows[s.location.id][indicator_index] == NOT_ASSIGNED_STRING:
                rows[s.location.id][indicator_index] = s
            else:
                rows[s.location.id][indicator_index].merge(s)

        this_month = datetime.date(year, month, 1)

        #raise Exception(rows)
        context['this_month'] = this_month
        context['last_month'] = this_month-relativedelta(months=1)
        context['next_month'] = this_month+relativedelta(months=1)
        context['columns'] = columns
        context['entries'] = rows.values()
        return context

class LocationImageCreateView(LocationView, CreateView):
    model = cm.Image
    template_name = 'base/form.html'
    fields = ['original_file']

    def get_form(self, form_class):
        return cf.ImageForm(self.request.POST or None, self.request.FILES or None, initial=self.get_initial())

    def form_valid(self, form):
        return super(LocationImageCreateView, self).form_valid(form)

    def get_success_url(self):
        self.noun.images.add(self.object)
        action.send(self.request.user, verb='uploaded image', action_object=self.object, target=self.noun)
        return reverse(viewname='location_detail', args=(self.noun.id,), current_app='core')

class IndicatorCreateView(SiteRootView, CreateView):
    model = cm.Indicator
    template_name = 'base/form.html'
    form_class = cf.IndicatorForm

    def form_valid(self, form):
        new_form = fm.Form.objects.create(title=form.cleaned_data['title'][0:50])
        location_field = fm.Field.objects.create(form=new_form, field_type=1, label="Location", visible=False, order=-2)
        location_field = fm.Field.objects.create(form=new_form, field_type=1, label="User", visible=False,order=-1)
        location_field = fm.Field.objects.create(form=new_form, field_type=13, label="Score", visible=False, order=0)
        form.instance.form = new_form
        self.instance = form.instance
        #action.send(self.request.user, verb='created', action_object=self.object, target=self.object)
        return super(IndicatorCreateView, self).form_valid(form)

    def get_success_url(self):
        action.send(self.request.user, verb='created indicator', action_object=self.instance)
        return reverse(viewname='field_create', args=(self.instance.id,), current_app='core')


class IndicatorView(NounView):
    def get_noun(self, **kwargs):
        return cm.Indicator.objects.get(id=self.kwargs['pk'])

class IndicatorUpdateView(IndicatorView, UpdateView):
    model = cm.Indicator
    template_name = 'base/form.html'
    success_url = '/'
    form_class = cf.IndicatorForm

    def get_success_url(self):
        action.send(self.request.user, verb='updated indicator', action_object=self.get_noun())
        return reverse(viewname='indicator_detail', args=(self.noun.id,), current_app='core')

class IndicatorDetailView(IndicatorView, TemplateView):
    model = cm.Indicator
    template_name = 'indicator/list.html'

    def get_context_data(self, **kwargs):
        context = super(IndicatorDetailView, self).get_context_data(**kwargs)
        context['ILLEGAL_FIELD_LABELS'] = cm.ILLEGAL_FIELD_LABELS
        context['stream'] = self.noun.get_action_stream()[:40]
        context['ILLEGAL_FIELD_LABELS'] = cm.ILLEGAL_FIELD_LABELS
        return context

    def get_context_data(self, **kwargs):
        context = super(IndicatorDetailView, self).get_context_data(**kwargs)
        indicators = []
        indicators.append(self.noun.get_serialized())
        context['indicators'] = indicators
        context['ILLEGAL_FIELD_LABELS'] = cm.ILLEGAL_FIELD_LABELS

        return context

    def get(self, request, *args, **kwargs):
        supes = super(IndicatorDetailView, self).get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        if self.request.is_ajax():
            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)

        return supes

class IndicatorListView(SiteRootView, TemplateView):
    model = cm.Indicator    
    template_name = 'indicator/list.html'

    def get_context_data(self, **kwargs):
        context = super(IndicatorListView, self).get_context_data(**kwargs)
        indicators = []
        for l in cm.Indicator.objects.all().order_by('form_number'):
            blob = l.get_serialized()
            indicators.append(blob)
        context['indicators'] = indicators
        context['ILLEGAL_FIELD_LABELS'] = cm.ILLEGAL_FIELD_LABELS
        return context

    def get(self, request, *args, **kwargs):
        supes = super(IndicatorListView, self).get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        if self.request.is_ajax():
            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)

        return supes

class FieldCreateView(IndicatorView, FormView):
    model = fm.Field
    template_name = 'base/form.html'

    def get_form(self, form_class):
        return cf.FieldForm(self.request.POST or None, self.request.FILES or None, initial=self.get_initial())

    def form_valid(self, form):
        form.instance.form = self.noun.form
        form.instance.required = False
        self.object = form.instance.save()
        self.instance = form.instance
        return super(FieldCreateView, self).form_valid(form)

    def get_success_url(self):
        action.send(self.request.user, verb='created field', action_object=self.instance, target=self.noun)
        return reverse(viewname='field_create', args=(self.noun.id,), current_app='core')

    def get_success_message(self, cleaned_data):
        return "Your field was created.  Make another new field or return to the indicator."

class FieldUpdateView(IndicatorView, UpdateView):
    model = fm.Field
    template_name = 'base/form.html'
    success_url = '/'

    def get_noun(self, **kwargs):
        form = self.get_object().form
        return cm.Indicator.objects.get(form=form)

    def get_object(self):
        output = get_object_or_404(fm.Field, id=self.kwargs["pk"])
        return output

    def get_form(self, form_class):
        return cf.FieldForm(self.request.POST or None, self.request.FILES or None, initial=self.get_initial(), instance=self.get_object())

    def get_success_url(self):
        action.send(self.request.user, verb='updated field', action_object=self.get_object(), target=self.noun)
        return reverse(viewname='indicator_detail', args=(self.noun.id,), current_app='core')


import json

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.utils.http import urlquote
from django.views.generic.base import TemplateView
from email_extras.utils import send_mail_template

from forms_builder.forms.forms import FormForForm
from forms_builder.forms.models import Form

from forms_builder.forms.signals import form_invalid, form_valid
from forms_builder.forms.utils import split_choices

from django.contrib import messages


class IndicatorRecordCreateView(LocationView, TemplateView):

    template_name = "base/form.html"

    def get_noun(self, **kwargs):
        return cm.Location.objects.get(id=self.kwargs['location_pk'])

    def prep_form(self, form):
        #form.fields.__delitem__('location')
        #form.fields.__delitem__('user')
        return form

    def get_context_data(self, **kwargs):
        context = super(IndicatorRecordCreateView, self).get_context_data(**kwargs)
        published = Form.objects.published(for_user=self.request.user)
        indicator = get_object_or_404(cm.Indicator, id=kwargs["pk"])
        form = indicator.get_form()
        form = self.prep_form(form)
        context["form"] = form
        context["indicator"] = indicator
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        indicator = get_object_or_404(cm.Indicator, id=kwargs["pk"])
        builder_form_object = indicator.get_builder_form_object()
        form = FormForForm(builder_form_object, RequestContext(request),
                                    request.POST or None,
                                    request.FILES or None)
        if not form.is_valid():
            form_invalid.send(sender=request, form=form_for_form)
        else:
            # Attachments read must occur before model save,
            # or seek() will fail on large uploads.
            attachments = []
            for f in form.files.values():
                f.seek(0)
                attachments.append((f.name, f.read()))
            indicator = get_object_or_404(cm.Indicator, id=kwargs["pk"])
            location = get_object_or_404(cm.Location, id=kwargs["location_pk"])
            form.cleaned_data["user"] = request.user.get_full_name()
            form.cleaned_data["location"] = location.__str__()
            entry = form.save()
            form_valid.send(sender=request, form=form, entry=entry)
            form = self.prep_form(form)
            score = indicator.score_entry(entry)
            context = self.get_context_data(**kwargs)
            if score >= indicator.passing_percentage:
                messages.success(request,'Passing score of '+str(score))
                action.send(self.request.user, verb='entered passing record', action_object=context.get("indicator"), target=self.noun)
            else:
                messages.error(request,'Not passing score of '+str(score))
                action.send(self.request.user, verb='entered failing record', action_object=context.get("indicator"), target=self.noun)
            return HttpResponseRedirect(reverse(viewname='indicator_record_create', args=(kwargs['location_pk'], kwargs['pk'],), current_app='core'))

        context = {"builder_form_object": builder_form_object, "form": form}
        return self.render_to_response(context)

    def render_to_response(self, context, **kwargs):
        if self.request.is_ajax():
            json_context = json.dumps({
                "errors": context["form_for_form"].errors,
                "form": context["form_for_form"].as_p(),
                "message": context["form"].response,
            })
            return HttpResponse(json_context, content_type="application/json")
        return super(IndicatorRecordCreateView, self).render_to_response(context, **kwargs)

form_detail = IndicatorRecordCreateView.as_view()

from forms_builder.forms.utils import now, split_choices

class IndicatorRecordUploadView(LocationView, FormView):
    template_name = 'base/form.html'
    form_class = cf.JSONUploadForm
    success_url = '/'

    def get_noun(self, **kwargs):
        return cm.Location.objects.get(id=self.kwargs['location_pk'])

    def form_valid(self, form):
        try:
            json_string = form.cleaned_data['json']
            data = json.loads(json_string, parse_float=decimal.Decimal)
            
            #create field entries for incoming data.  Don't save them until we're done
            fieldEntries = []
            for f in data.get("values"):
                field_id = f.get("field_id")
                new_value = f.get("value")
                if new_value == True:
                    new_value = u"True"
                elif new_value == False:
                    new_value = u"False"
                new_fieldEntry = fm.FieldEntry(value=new_value, field_id=field_id)
                fieldEntries.append(new_fieldEntry)
            if fieldEntries.__len__() > 0:
                #if there are entries, create a new record
                form_id = fm.Field.objects.get(id=field_id).form_id
                new_record = fm.FormEntry(entry_time=now(), form_id=form_id)
                new_record.save()
                for f in fieldEntries:
                    #connect the entries to the record
                    f.entry_id = new_record.id
                    f.save()
                #create entries for location and user data
                score = float(data.get("score"))
                builder_form = fm.Form.objects.get(id=form_id)
                new_locationEntry = fm.FieldEntry(value=self.get_noun().__str__(), field_id=builder_form.fields.get(label="Location").id, entry_id=new_record.id)
                new_locationEntry.save()
                new_userEntry = fm.FieldEntry(value=self.request.user.get_full_name(), field_id=builder_form.fields.get(label="User").id, entry_id=new_record.id)
                new_userEntry.save()
                new_scoreEntry = fm.FieldEntry(value=score, field_id=builder_form.fields.get(label="Score").id, entry_id=new_record.id)
                new_scoreEntry.save()

                #take the score from the json and create an action
                indicator = cm.Indicator.objects.get(form__id=form_id)
                if score >= indicator.passing_percentage:
                    messages.success(self.request,'Passing score of '+str(score))
                    action.send(self.request.user, verb='PASS '+str(score), action_object=indicator, target=self.noun)
                else:
                    messages.error(self.request,'Not passing score of '+str(score))
                    action.send(self.request.user, verb='FAIL '+str(score), action_object=indicator, target=self.noun)
            context = {
                "status":"success",
                "record_id":new_record.id
            }
        except Exception as e:
            context = {
                "status":"failure",
                "error":e
            }
        if self.request.is_ajax():

            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)
        else:
            return super(IndicatorRecordUploadView, self).form_valid(form)


    def get(self, request, *args, **kwargs):
        supes = super(IndicatorRecordUploadView, self).get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        if self.request.is_ajax():
            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)

        return supes

'''
incoming json looks like:
{
    "title":"blah blah blah",
    "scores":[
        {
            "percentage":100.00,
            "indicator_id":0,
            "location_id":0,
            "passing":true,
            "total_record_count":0,
            "passing_record_count":0
        }
    ]
}
'''

class LocationScoreUploadView(LocationView, FormView):
    template_name = 'base/form.html'
    form_class = cf.JSONUploadForm
    success_url = '/'

    def get_noun(self, **kwargs):
        return cm.Location.objects.get(id=self.kwargs['location_pk'])

    def form_valid(self, form):
        json_string = form.cleaned_data['json']
        try:
            data = json.loads(json_string, parse_float=decimal.Decimal)
            new_scores = []
            for s in data.get("scores"):
                print type(s)
                #check to make sure the location matches
                if int(s.get("location_id")) != self.noun.id:
                    raise Exception("wrong score for this location")
                indicator_id = s.get("indicator_id")
                indicator = cm.Indicator.objects.get(id=indicator_id)
                #create but don't save untill all are created
                new_score = cm.Score(indicator=indicator, passing=s.get("passing"), entry_count=s.get("total_record_count"), passing_entry_count=s.get("passing_record_count"), month=str(s.get("month")), year=s.get("year"),score=s.get("percentage"),location=self.noun, user=self.request.user)
                new_scores.append(new_score)
            #if nothing blew up, lets save these
            for s in new_scores:
                s.save()
            context = {
                "status":"success",
                "score_id":0
            }
        except Exception as e:
            context = {
                "status":"failure",
                "error":e
            }
        if self.request.is_ajax():

            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)
        else:
            return super(LocationScoreUploadView, self).form_valid(form)


    def get(self, request, *args, **kwargs):
        supes = super(LocationScoreUploadView, self).get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        if self.request.is_ajax():
            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)

        return supes
