from django import forms
from . import models


class ProjectForm(forms.ModelForm):
    """Project form
    :inherit: - forms.ModelForm class
    """
    description = forms.Textarea(attrs={"cols": 28, "rows": 6})

    class Meta:
        model = models.Project
        fields = [
            'title',
            'description',
            'time_estimate',
            'requirements']


class PositionForm(forms.ModelForm):
    """Position form
    :inherit: - forms.ModelForm
    """
    description = forms.Textarea(attrs={'cols': 28, 'rows': 6})

    class Media:
        css = {'all': ('css/order.css',)}
        js = ('js/jquery.fn.sortable.min.js',
              'js/order.js')

    class Meta:
        model = models.Position
        fields = ['name', 'description', 'time']


# PositionFormset for PositionInlineFormset
PositionFormset = forms.modelformset_factory(
    models.Position,
    form=PositionForm,
    extra=2,
)

PositionInlineFormset = forms.inlineformset_factory(
    models.Project,
    models.Position,
    form=PositionForm,
    fields=('name', 'description', 'time'),
    extra=2,
    formset=PositionFormset,
    min_num=0,
    max_num=5,
    can_delete=True
)
