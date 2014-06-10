from __future__ import unicode_literals
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
#from carteblanche.django.mixins import NounView
from core.verbs import NounView
import core.models as cm
import core.forms as cf
import core.tasks as ct
from django.db.models.signals import post_save
from actstream import action
from actstream.models import user_stream, action_object_stream, model_stream, actor_stream
from django.contrib.auth import authenticate, login, logout
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.conf import settings
import decimal
import forms_builder.forms.models as fm
import json
from django.http import HttpResponse
from django.views.generic.edit import CreateView

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
    template_name = 'overview/map.html'

    def get(self, request, **kwargs):
        return HttpResponseRedirect(reverse(viewname='location_list', current_app='core'))

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

class UserCreateView(SiteRootView, CreateView):
    model = User
    template_name = 'base/form.html'
    form_class = cf.RegistrationForm

    def form_valid(self, form):
        user = User.objects.create_user(uuid4().hex, form.cleaned_data['email'], form.cleaned_data['password1'])
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['first_name']
        user.save()
        user = authenticate(username=user.username, password=form.cleaned_data['password1'])
        login(self.request, user)
        form.instance = user
        return super(UserCreateView, self).form_valid(form)

    def get_success_url(self):
        action.send(self.request.user, verb='joined', action_object=self.object)
        return reverse(viewname='user_detail', args=(self.object.id,), current_app='core')

class UserLoginView(SiteRootView, FormView):
    template_name = 'base/form.html'
    form_class = cf.LoginForm
    success_url = '/'

    def form_valid(self, form):
        user = form.user_cache
        login(self.request, user)
        form.instance = user
        return super(UserLoginView, self).form_valid(form)

class UserLogoutView(SiteRootView, TemplateView):
    template_name = 'bootstrap.html'

    def get(self, request, **kwargs):
        #if the user has no payment methods, redirect to the view where one can be created
        logout(self.request)
        return HttpResponseRedirect(reverse(viewname='post_list', current_app='core'))


class LocationCreateView(SiteRootView, CreateView):
    model = cm.Location
    template_name = 'base/form.html'
    fields = '__all__'
    form_class = cf.LocationForm
    success_url = '/'

    def get(self, request, *args, **kwargs):
        supes = super(LocationCreateView, self).get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        if self.request.is_ajax():
            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)

        return supes

class LocationListView(SiteRootView, TemplateView):
    model = cm.Location    
    template_name = 'overview/map.html'

    def get_context_data(self, **kwargs):
        context = super(LocationListView, self).get_context_data(**kwargs)
        locations = []
        for l in cm.Location.objects.all():
            blob = {
                'id':l.id,
                'lattitude':l.position.latitude,
                'longitude':l.position.longitude,
                'title':l.title
            }
            locations.append(blob)
        context['locations'] = locations
        return context

    def get(self, request, *args, **kwargs):
        supes = super(LocationListView, self).get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        if self.request.is_ajax():
            data = json.dumps(context, default=decimal_default)
            out_kwargs = {'content_type':'application/json'}
            return HttpResponse(data, **out_kwargs)

        return supes

class IndicatorCreateView(SiteRootView, CreateView):
    model = cm.Indicator
    template_name = 'base/form.html'
    form_class = cf.IndicatorForm

    def form_valid(self, form):
        new_form = fm.Form.objects.create(title=form.cleaned_data['title'])
        location_field = fm.Field.objects.create(form=new_form, field_type=1, label="Location", visible=False)
        location_field = fm.Field.objects.create(form=new_form, field_type=1, label="User", visible=False)
        form.instance.form = new_form
        self.instance = form.instance
        #action.send(self.request.user, verb='created', action_object=self.object, target=self.object)
        return super(IndicatorCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse(viewname='field_create', args=(self.instance.id,), current_app='core')

class IndicatorView(NounView):
    def get_noun(self, **kwargs):
        return cm.Indicator.objects.get(id=self.kwargs['pk'])

class IndicatorDetailView(IndicatorView, FormView):
    model = fm.Field
    template_name = 'base/form_display.html'

    def get_form(self, form_class):
        return self.noun.get_form()

class FieldCreateView(IndicatorView, FormView):
    model = fm.Field
    template_name = 'base/form.html'

    def get_form(self, form_class):
        return cf.FieldForm(self.request.POST or None, self.request.FILES or None, initial=self.get_initial())

    def form_valid(self, form):
        form.instance.form = self.noun.form
        form.instance.save()
        self.instance = form.instance
        return super(FieldCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse(viewname='field_create', args=(self.noun.id,), current_app='core')

    def get_success_message(self, cleaned_data):
        return "Your field was created.  Make another new field or return to the indicator."

class IndicatorRecordCreateView_legacy(IndicatorView, FormView):
    model = fm.Form
    template_name = 'base/form.html'
    success_url = '/'

    def get_form(self, form_class):
        form = self.noun.get_form()
        return form

    def form_valid(self, form):
        raise Exception('raised')
        form.instance.form
        form.instance.save()
        self.instance = form.instance
        return super(FieldCreateView, self).form_valid(form)

    def get_success_message(self, cleaned_data):
        return "Your record was created."




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


class IndicatorRecordCreateView(IndicatorView, TemplateView):

    template_name = "base/form.html"

    def prep_form(self, form):
        form.fields.__delitem__('location')
        form.fields.__delitem__('user')
        return form

    def get_context_data(self, **kwargs):
        context = super(IndicatorRecordCreateView, self).get_context_data(**kwargs)
        published = Form.objects.published(for_user=self.request.user)
        indicator = get_object_or_404(cm.Indicator, id=kwargs["pk"])
        form = indicator.get_form()
        form = self.prep_form(form)
        context["form"] = form
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
            if score >= indicator.passing_percentage:
                messages.success(request,'Passing score of '+str(score))
            else:
                messages.error(request,'Not passing score of '+str(score))

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