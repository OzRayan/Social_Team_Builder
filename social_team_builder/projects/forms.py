from django import forms
from . import models

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class ProjectForm(forms.ModelForm):
    description = forms.Textarea(attrs={"cols": 28, "rows": 6})

    class Meta:
        model = models.Project
        fields = [
            'title',
            'description',
            'time_estimate',
            'requirements']


class BaseForm(forms.ModelForm):
    class Media:
        css = {'all': ('css/order.css',)}
        js = ('js/jquery.fn.sortable.min.js',
              'js/order.js')


class PositionForm(BaseForm):
    description = forms.Textarea(attrs={'cols': 28,'rows': 6})

    class Meta:
        model = models.Position
        fields = ['name', 'description']


PositionFormset = forms.modelformset_factory(
    models.Position,
    form=PositionForm,
    extra=1,
)

PositionInlineFormset = forms.inlineformset_factory(
    models.Project,
    models.Position,
    form=PositionForm,
    fields=('name', 'description'),
    extra=1,
    min_num=0,
    max_num=5
)
