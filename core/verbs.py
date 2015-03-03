from carteblanche.mixins import DjangoVerb, availability_login_required
from carteblanche.base import Verb, Noun, Conditions
from django.core.urlresolvers import reverse

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

class SiteUserCreateVerb(StaffVerb):
    display_name = "Create User"
    view_name ='make_new_user'

class SiteLoginVerb(UnauthenticatedOnlyVerb):
    display_name = "Login"
    #no view name ok because this is always allowed, fb handles the authentication

    def get_url(self):
        return reverse('user_login')

class HistoryListVerb(CoreVerb):
    display_name = "View History"
    view_name='history_list'
    required = True
    denied_message = "Sorry, you can't view that history yet."

    def is_available(self, user):
        return self.noun.is_visible_to(user)

class LocationCreateVerb(StaffVerb):
    display_name = "Create New Location"
    view_name='location_create'

class LocationUpdateVerb(StaffVerb):
    display_name = "Update Location"
    view_name='location_update'

class LocationImageCreateVerb(AuthenticatedOnlyVerb):
    display_name = "Add Image To This Location"
    view_name='location_image_create'

class LocationVisualizeVerb(AuthenticatedOnlyVerb):
    display_name = "Visualize This Location"
    view_name='location_visualize'


class ScoreListVerb(AuthenticatedOnlyVerb):
    display_name = "View All Location Goals"
    view_name='scores_list'

class IndicatorCreateVerb(StaffVerb):
    display_name = "Create New Indicator"
    view_name='indicator_create'

class IndicatorDetailVerb(AuthenticatedOnlyVerb):
    display_name = "View Indicator"
    view_name='indicator_detail'

class IndicatorUpdateVerb(StaffVerb):
    display_name = "Update Indicator"
    view_name='indicator_update'

class IndicatorListVerb(AuthenticatedOnlyVerb):
    display_name = "View All Indicators"
    view_name='indicator_list'

class IndicatorRecordCreateVerb(AuthenticatedOnlyVerb):
    display_name = "Enter Data"
    view_name='indicator_record_create'

class FieldCreateVerb(StaffVerb):
    display_name = "Create New Field"
    view_name='field_create'

class FieldUpdateVerb(StaffVerb):
    display_name = "Create New Field"
    view_name='field_update'
    visible = False

    def get_url(self):
        return None

class LocationDetailVerb(AuthenticatedOnlyVerb):
    display_name = "View Location"
    view_name='location_detail'

class LocationPhotoListVerb(AuthenticatedOnlyVerb):
    display_name = "View Photos"
    view_name='location_photo_list'

class EntriesFilterVerb(AuthenticatedOnlyVerb):
    display_name = "Filter and Export Data"
    view_name='entries_filter'

class LocationListVerb(AuthenticatedOnlyVerb):
    display_name = "View All Locations"
    view_name='location_list'

class LocationIndicatorListVerb(AuthenticatedOnlyVerb):
    display_name = "View This Location's Indicators"
    view_name='location_indicator_list'

class LocationListStreamVerb(AuthenticatedOnlyVerb):
    display_name = "All Locations History"
    view_name='location_stream_list'

class LocationListVisualizeVerb(AuthenticatedOnlyVerb):
    display_name = "Visualize All Locations"
    view_name='location_list_visualize'

class UserListVerb(StaffVerb):
    display_name = "View All Users"
    view_name='user_list'



class SiteRoot(Noun):
    '''
    A hack that lets pages that have no actual noun have verbs and verb-based permissions. 
    '''
    verb_classes = [SiteLoginVerb, LocationListStreamVerb, LocationListVerb, LocationListVisualizeVerb, ScoreListVerb, IndicatorListVerb, EntriesFilterVerb, LocationCreateVerb, IndicatorCreateVerb, SiteUserCreateVerb, UserListVerb]

    class Meta:
        abstract = True

    def __unicode__(self):
        return ''

class UserDetailVerb(AuthenticatedOnlyVerb):
    display_name = "View User"
    view_name='user_detail'

class UserUpdateVerb(StaffVerb):
    display_name = "Update User"
    view_name='user_update'

class UserDeactivateVerb(StaffVerb):
    display_name = "Deactivate User"
    view_name='user_deactivate'

class ResetPasswordVerb(StaffVerb):
    display_name = "Reset Password"
    view_name='user_password_reset'

class CoreUser(Noun):
    '''
    A hack that lets pages that use the  have verbs and verb-based permissions. 
    '''
    verb_classes = [UserListVerb, UserDetailVerb, UserUpdateVerb, ResetPasswordVerb, UserDeactivateVerb]
    id = -1

    def __init__(self, user):
        self.id = user.id
        self.conditions = Conditions(self)

    class Meta:
        abstract = True

    def __unicode__(self):
        return ''