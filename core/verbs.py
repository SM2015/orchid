import carteblanche.base as cb
from django.views.generic import DetailView
from django.shortcuts import render_to_response
from django.core.urlresolvers import resolve
from django.template import RequestContext
from django.core.urlresolvers import reverse
from functools import wraps
from django.utils.decorators import available_attrs
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

MESSAGES_TEMPLATE = 'base/messages.html'

class NounView(SuccessMessageMixin):
    success_message = "That worked!"

    def __init__(self, **kwargs):
        super(NounView, self).__init__(**kwargs)
        self.noun = None
        
    def get_view_required_verbs(self, view_name):
        verbs = []
        for v in self.noun.get_verbs():
            if v.required == True:
                if v.view_name == view_name:
                    verbs.append(v)
        return verbs

    def get_view_required_unavailable_verbs(self, view_name, user):
        verbs = []
        for v in self.get_view_required_verbs(view_name):
            if not v.is_available(user):
                verbs.append(v)
        return verbs

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        print "get_context_data"
        context = super(NounView, self).get_context_data(**kwargs)
        available_verbs = self.noun.get_available_verbs(self.request.user)
        context['available_verbs'] = available_verbs
        context['conditions'] = self.noun.conditions.get_available(self.request.user)
        context['noun'] = self.noun
        self.noun.conditions.cache = {}
        return context

    def dispatch(self, *args, **kwargs):
        self.noun = self.get_noun(**kwargs)
        #what verbs are required and available for viewing of this page
        #for each of those, get a forbidden message and direct the user to a messaging view
        view_name = resolve(self.request.path_info).url_name
        denied_messages = []
        for verb in self.get_view_required_unavailable_verbs(view_name, self.request.user):
            denied_messages.append(verb.denied_message)
        if len(denied_messages) > 0:
            for message in denied_messages:
                messages.add_message(self.request, messages.ERROR, message)
            return render_to_response(MESSAGES_TEMPLATE,{"available_verbs":self.noun.get_available_verbs(self.request.user)}, RequestContext(self.request))
        
        return super(NounView, self).dispatch(*args, **kwargs)

    def get_success_message(self, cleaned_data):
        view_name = resolve(self.request.path_info).url_name
        denied_messages = []
        for verb in self.get_view_required_unavailable_verbs(view_name, self.request.user):
            denied_messages.append(verb.success_message)

        return ''.join(denied_messages)

    class Meta:
        abstract = True

from django.core.urlresolvers import NoReverseMatch
class DjangoVerb(cb.Verb):
    view_name = None
    app = None
    visible = True

    def get_url(self):
        '''
        Default django get_url for urls that require no args.
        '''
        try:
            return reverse(viewname=self.view_name, args=[self.noun.id], current_app=self.app)
        except NoReverseMatch as e:
            return reverse(viewname=self.view_name, current_app=self.app)

def availability_login_required(is_available_func):
    @wraps(is_available_func, assigned=available_attrs(is_available_func))
    def decorator(self, user):
        print user
        if user.is_authenticated(): 
            print "is_authenticated = True"
            return is_available_func(self, user)
        else:
            print "is_authenticated = False"
            self.denied_message = "You must be logged in to "+self.display_name+"."
            return False
    return decorator

from carteblanche.base import Verb, Noun
APPNAME = 'core'

class CoreVerb(DjangoVerb):
    app = APPNAME
    condition_name = 'public'

class UnauthenticatedOnlyVerb(CoreVerb):
    condition_name = 'is_unauthenticated'
    required = True

    def is_available(self, user):
        #only available to non-logged in users
        if user.is_authenticated():
            return False
        return True

class AuthenticatedOnlyVerb(CoreVerb):
    condition_name = 'is_authenticated'
    required = True

    @availability_login_required
    def is_available(self, user):
        return True

class StaffVerb(CoreVerb):
    condition_name = 'is_staff'
    required = True

    @availability_login_required
    def is_available(self, user):
        return user.is_staff

class HistoryListVerb(CoreVerb):
    display_name = "View History"
    view_name='history_list'
    required = True
    denied_message = "Sorry, you can't view that history yet."
    
    def is_available(self, user):
        return self.noun.is_visible_to(user)

class LocationCreateVerb(AuthenticatedOnlyVerb):
    display_name = "Create New Location"
    view_name='location_create'

class IndicatorCreateVerb(AuthenticatedOnlyVerb):
    display_name = "Create New Indicator"
    view_name='indicator_create'

class IndicatorDetaileVerb(AuthenticatedOnlyVerb):
    display_name = "View Indicator"
    view_name='indicator_detail'

class FieldCreateVerb(AuthenticatedOnlyVerb):
    display_name = "Create New Field"
    view_name='field_create'

class LocationListVerb(CoreVerb):
    display_name = "View All Locations"
    view_name='location_list'

class SiteLoginVerb(UnauthenticatedOnlyVerb):
    display_name = "Login"
    #no view name ok because this is always allowed, fb handles the authentication

    def get_url(self):
        return reverse('user_login')

class SiteRoot(Noun):
    '''
    A hack that lets pages that have no actual noun have verbs and verb-based permissions. 
    '''
    verb_classes = [SiteLoginVerb, LocationListVerb, LocationCreateVerb, IndicatorCreateVerb]

    class Meta:
        abstract = True

    def __unicode__(self):
        return ''
