from django import forms
from . import models
# noinspection PyUnresolvedReferences
from accounts.models import Skill


class ProjectForm(forms.ModelForm):
    """Project form
    :inherit: - forms.ModelForm
    :field: - description - forms.TextArea
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
    :fields: - description - forms.TextArea
             -skill - forms.ModelMultipleChoiceField with
                      forms.CheckboxSelectMultiple() widget
    """
    description = forms.Textarea(attrs={'cols': 28, 'rows': 6})
    skills = Skill.objects.values_list('name', flat=True).distinct()
    skill = forms.ModelMultipleChoiceField(
        queryset=skills,
        widget=forms.CheckboxSelectMultiple(),
        required=False)
    # import pdb; pdb.set_trace()

    class Media:
        css = {'all': ('css/order.css',)}
        js = ('js/jquery.fn.sortable.min.js',
              'js/order.js')

    class Meta:
        model = models.Position
        fields = ['name', 'description', 'time', 'skill']


# PositionFormset for PositionInlineFormset
PositionFormset = forms.modelformset_factory(
    models.Position,
    form=PositionForm,
    extra=3,
)

# PositionInlineFormset
PositionInlineFormset = forms.inlineformset_factory(
    models.Project,
    models.Position,
    form=PositionForm,
    fields=('name', 'description', 'time', 'skill'),
    extra=3,
    formset=PositionFormset,
    min_num=0,
    max_num=5,
    can_delete=True
)
