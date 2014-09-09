from django import forms
import core.models as cm
from django.contrib.auth.models import User
import django.forms.extras.widgets as widgets
import forms_builder.forms.models as fm

#do weird stuff to mAake user names nou usernames show up
def user_new_unicode(self):
    return self.get_full_name()
# Replace the __unicode__ method in the User class with out new implementation
User.__unicode__ = user_new_unicode 
FIELD_TYPE_CHOICES = (
    (4, 'Yes / No'),
    (1, 'Short Text'),
    (2, 'Long Text'),
)

class BootstrapForm(forms.Form):
    exclude = ['changed_by']
    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if field.widget.attrs.has_key('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs.update({'class':'form-control'})

class ModelBootstrapForm(forms.ModelForm):
    exclude = ['changed_by']
    def __init__(self, *args, **kwargs):
        super(ModelBootstrapForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if field.widget.attrs.has_key('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs.update({'class':'form-control'})

class BooleanForm(forms.Form):
    decision = forms.BooleanField(required=True, label="Confirm", help_text="I swear, I'm ready to do this.")

    def clean(self):
        cleaned_data = super(BooleanForm, self).clean()
        decision = cleaned_data.get("decision")

        if decision==None:
            self._errors["decision"] = self.error_class(["You have to check the box if you want to publish."])
            # These fields are no longer valid. Remove them from the
            # cleaned data.


        # Always return the cleaned data, whether you have changed it or
        # not.
        return cleaned_data

class DropzoneForm(ModelBootstrapForm):
    def __init__(self, *args, **kwargs):
        super(DropzoneForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if field.widget.attrs.has_key('class'):
                field.widget.attrs['class'] += ' form-control dropzone'
            else:
                field.widget.attrs.update({'class':'form-control dropzone'})


class RegistrationForm(ModelBootstrapForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    locations = forms.ModelMultipleChoiceField(queryset=cm.Location.objects.all(), required=False, widget=forms.SelectMultiple(attrs={'class':'chosen-select'}))
    # rest of the fields

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        email = cleaned_data.get("email")
        if User.objects.filter(email=email).count()>0:
            self._errors['email'] = self.error_class(["There's already a user with that email address."])
            del cleaned_data['email']

        password1 = cleaned_data.get("password1").lower()
        password2 = cleaned_data.get("password2").lower()

        if password1 != password2:
            self._errors['password2'] = self.error_class(["Didn't match first password."])
            del cleaned_data['password2']

        return cleaned_data

    def save(self):
        return super(RegistrationForm, self).save()

    class Meta:
        model = User
        fields = ['email','first_name','last_name','password1','password1']

from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist

class LoginForm(ModelBootstrapForm):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': _("Please enter a correct %(email)s and password. "
                           "Note that both fields may be case-sensitive."),
        'inactive': _("This account is inactive."),
    }


    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password').lower()
        print "email: "+email
        print "password: "+password

        if email and password:
            try:
                temp_user = User.objects.get(email=email)
            except ObjectDoesNotExist as e:
                self._errors['email'] = self.error_class(['No user exists with that email.'])
                del cleaned_data['email']
                return self.cleaned_data

            self.user_cache = authenticate(username=temp_user.username,
                                           password=password)
            if self.user_cache is None:
                self._errors['password'] = self.error_class(['Incorrect password.'])
                del cleaned_data['password']
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache

    class Meta:
     model = User
     fields = ['email','password']

class LocationForm(ModelBootstrapForm):
    members = forms.ModelMultipleChoiceField(queryset=cm.User.objects.all().order_by('first_name'), required=False, widget=forms.SelectMultiple(attrs={'class':'chosen-select'}))
    indicators = forms.ModelMultipleChoiceField(queryset=cm.Indicator.objects.all().order_by('form_number','title'), required=False, widget=forms.SelectMultiple(attrs={'class':'chosen-select'}))
    class Meta:
        model = cm.Location
        exclude = ['changed_by','images']

class IndicatorForm(ModelBootstrapForm):
    title = forms.CharField(max_length=100)
    class Meta:
        model = cm.Indicator
        exclude = ['changed_by', 'form']


class FieldForm(ModelBootstrapForm):
    field_type = forms.ChoiceField(choices = FIELD_TYPE_CHOICES,widget = forms.Select())

    def clean(self):
        cleaned_data = super(FieldForm, self).clean()
        label = cleaned_data.get("label")
        order = cleaned_data.get("order")

        if label in cm.ILLEGAL_FIELD_LABELS:
            self._errors["label"] = self.error_class(["You aren't allowed to name a field "+label+"."])

        if order !=None:
            if order < 1:
                self._errors["order"] = self.error_class(["You aren't allowed to have an order less than 0."])


        # Always return the cleaned data, whether you have changed it or
        # not.
        return cleaned_data
    class Meta:
        model = fm.Field
        exclude = ['slug', 'required', 'placeholder_text', 'form', 'default','choices']

class ImageForm(ModelBootstrapForm):
    class Meta:
        model = cm.Image
        fields = ['original_file']

class JSONUploadForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(JSONUploadForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if field.widget.attrs.has_key('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs.update({'class':'form-control'})

    json = forms.CharField(widget=forms.Textarea)

class SavedFilterForm(BootstrapForm):
    indicator = forms.ModelChoiceField(queryset=cm.Indicator.objects.all(), required=True)
    locations = forms.ModelMultipleChoiceField(queryset=cm.Location.objects.all(), required=False, widget=forms.SelectMultiple(attrs={'class':'chosen-select'}))
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class':'datepicker'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class':'datepicker'}))
    input_user = forms.ModelMultipleChoiceField(queryset=cm.User.objects.all(), required=False, widget=forms.SelectMultiple(attrs={'class':'chosen-select'}))
    export = forms.BooleanField(required=False, help_text="Export this data as an excel spreadsheet.")
