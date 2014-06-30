from django import forms
import core.models as cm
from django.contrib.auth.models import User
import django.forms.extras.widgets as widgets
import forms_builder.forms.models as fm

FIELD_TYPE_CHOICES = (
    (4, 'Yes / No'),
    (1, 'Short Text'),
    (2, 'Long Text'),
)

class BootstrapForm(forms.ModelForm):
    exclude = ['changed_by']
    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
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

class DropzoneForm(BootstrapForm):
    def __init__(self, *args, **kwargs):
        super(DropzoneForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if field.widget.attrs.has_key('class'):
                field.widget.attrs['class'] += ' form-control dropzone'
            else:
                field.widget.attrs.update({'class':'form-control dropzone'})


class RegistrationForm(BootstrapForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())
    # rest of the fields

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 != password2:
            self.add_error('password2', u"Didn't match first password..")
        return cleaned_data

    def save(self):
        return super(RegistrationForm, self).save()

    class Meta:
        model = User
        fields = ['email','first_name','last_name','password1','password1']

from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import ugettext as _

class LoginForm(BootstrapForm):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': _("Please enter a correct %(email)s and password. "
                           "Note that both fields may be case-sensitive."),
        'inactive': _("This account is inactive."),
    }

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            temp_user = User.objects.get(email=email)
            self.user_cache = authenticate(username=temp_user.username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError('WARNING')
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

class LocationForm(BootstrapForm):
    class Meta:
        model = cm.Location
        exclude = ['changed_by']

class IndicatorForm(BootstrapForm):
    title = forms.CharField(max_length=100)
    class Meta:
        model = cm.Indicator
        exclude = ['changed_by', 'form']

class FieldForm(BootstrapForm):
    field_type = forms.ChoiceField(choices = FIELD_TYPE_CHOICES,widget = forms.Select())
    
    class Meta:
        model = fm.Field
        exclude = ['slug', 'visible', 'placeholder_text', 'form', 'default','required','choices']