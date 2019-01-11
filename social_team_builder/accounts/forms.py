import re
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

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
    :inherit: - forms.ModelForm class"""

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
    :inherit: - BaseForm class"""

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
    extra=1,
    can_delete=True

)

SkillInlineFormSet = forms.inlineformset_factory(
    get_user_model(),
    models.Skill,
    form=SkillForm,
    fields=('name',),
    extra=1,
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


class PasswordForm(forms.Form):
    """Password Form
    :Inherit: - forms.Form
    :fields: - old - password --> CharField widget PasswordInput
             - new - password --> CharField widget PasswordInput
             - check_new - password --> CharField widget PasswordInput
    """
    old = forms.CharField(widget=forms.PasswordInput())
    new = forms.CharField(widget=forms.PasswordInput())
    check_new = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, request=None, *args, **kwargs):
        """Prepares user data for password validation"""
        self.request = request
        super().__init__(*args, **kwargs)

    def error(self, error_message):
        """Validation error for failing checks"""
        messages.error(self.request, error_message)
        raise forms.ValidationError(error_message)

    def clean(self):
        """Password validation"""
        cleaned_data = super().clean()
        old_pass = cleaned_data.get('old', '')
        new_pass = cleaned_data.get('new', '')
        check_pass = cleaned_data.get('check_new', '')
        profile = self.request.user

        # validator(new_pass, check_pass, profile, old=old_pass, create=True)

        if not old_pass:
            self.error('First give the old password!')
        if not new_pass:
            self.error('Before confirming the new password, add one first!')
        if not check_pass:
            self.error('Confirm the new password')

        if len(new_pass) < 14:
            self.error('Minim length 14 characters!')
        if old_pass == new_pass:
            self.error('New password can\'t match with the old password!')
        if new_pass != check_pass:
            self.error('Passwords doesn\'t match!')

        # Checks if user profile name are present in password
        if profile.first_name.lower() in new_pass.lower() or \
                profile.last_name.lower() in new_pass.lower():
            self.error('Password can\'t contain your first or last name!')

        # Regex use to check alphabet, numeric, upper, lower and special chars in password.
        if not re.findall('[A-Z]', new_pass):
            self.error('Password must contain at least one upper letter!')
        if not re.findall('[a-z]', new_pass):
            self.error('Password must contain at least one lower letter!')
        if not re.findall('\d', new_pass):
            self.error('Password must contain at least one number!')
        if not re.findall('\W[^_]', new_pass):
            self.error('Password must contain at least one special character (ex: .\!@#$%^&*?_~-)')

        return cleaned_data
