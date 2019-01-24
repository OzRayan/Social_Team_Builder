from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from PIL import Image

from . import models


class UserCreateForm(UserCreationForm):
    """User Create form
    :inherit: - forms.UserCreationForm class
    """
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Email address'
        self.fields['password2'].label = 'Enter password again!'
        self.fields['password2'].help_text = None


class UserProfileForm(forms.ModelForm):
    """User Profile form
    :inherit: - forms.ModelForm class
    :fields: - bio - forms.TextArea()
    """
    bio = forms.Textarea(attrs={"cols": 28, "rows": 8})

    class Meta:
        model = get_user_model()
        fields = ['username',
                  'first_name',
                  'last_name',
                  'email',
                  'bio',
                  'avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bio'].label = 'Short bio'


class AvatarForm(forms.ModelForm):
    """Avatar Form
    :inherit: - forms.ModelForm class"""
    class Meta:
        model = get_user_model()
        fields = ('avatar',)


class AvatarCropForm(forms.Form):
    """Avatar Crop Form
    :inherit: - forms.Form
    :fields: - left
             - top
             - right
             - bottom - all forms.IntegerField()
    :method: - clean()
    """
    left = forms.IntegerField()
    top = forms.IntegerField()
    right = forms.IntegerField()
    bottom = forms.IntegerField()

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        with Image.open(self.user.avatar.path) as avatar:
            width, height = avatar.size

            left = int(self.cleaned_data['left'])
            top = int(self.cleaned_data['top'])
            right = int(self.cleaned_data['right'])
            bottom = int(self.cleaned_data['bottom'])

            max_left = width - right
            max_top = height - bottom

            if left >= max_left or top >= max_top \
                    or left >= width or top >= height or right > (width+1) or bottom > (height+1) \
                    or left < 0 or top < 0 or right <= 0 or bottom <= 0:
                # messages.error(self.request, "Unable to crop!")
                raise forms.ValidationError("Unable to crop!")


class BaseForm(forms.ModelForm):
    """Base form - for SkillForm and ProjectForm(own_projects)
    :inherit: - form.ModelForm class"""

    class Media:
        css = {'all': ('css/order.css',)}
        js = ('js/jquery.fn.sortable.min.js',
              'js/order.js')


class SkillForm(BaseForm):
    """Skill form
    :inherit: - BaseForm class"""

    class Meta:
        model = models.Skill
        fields = ['name', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Skill'


class ProjectForm(BaseForm):
    """Project form - own project list with url field
    :inherit: - BaseForm class
    :fields: - url - forms.URLField()
    """
    url = forms.URLField()

    class Meta:
        model = models.MyProject
        fields = ['name', 'url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Project name'
        self.fields['url'].label = 'Project url'


# SkillFormset for SkillInlineFormset
SkillFormset = forms.modelformset_factory(
    models.Skill,
    form=SkillForm,
    extra=3,
    can_delete=True

)

SkillInlineFormSet = forms.inlineformset_factory(
    get_user_model(),
    models.Skill,
    form=SkillForm,
    fields=('name',),
    extra=3,
    formset=SkillFormset,
    min_num=0,
    max_num=20,
    can_delete=True
)

# ProjectFormset for ProjectInlineFormset
ProjectFormset = forms.modelformset_factory(
    models.MyProject,
    form=ProjectForm,
    extra=1,
)

ProjectInlineFormset = forms.inlineformset_factory(
    get_user_model(),
    models.MyProject,
    form=ProjectForm,
    fields=('name', 'url'),
    extra=1,
    formset=ProjectFormset,
    min_num=0,
    max_num=15,
    can_delete=True
)
