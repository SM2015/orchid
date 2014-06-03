from forms_builder.forms.forms import FormForForm
from django.template.context import Context

def serialize_BuilderForm(builder_form):
    c = Context()
    z = FormForForm(builder_form, c)
    remote_form = RemoteForm(z)
    remote_form_dict = remote_form.as_dict()
    return remote_form_dict

def serialize_summary():
    output = {}
    for f in forms.models.Form.objects.all():
        serialized = serialize_BuilderForm(f.get_BuilderForm())
        output.__setitem__("a", serialized)
    return output