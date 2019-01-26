# NOTE: # noinspection - prefixed comments are for pycharm editor only
# for ignoring PEP 8 style highlights

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin as LrM
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import (CreateView, FormView, RedirectView,
                                  TemplateView, UpdateView, ListView)

from braces.views import PrefetchRelatedMixin as PrM
from notify.signals import notify
from PIL import Image

from . import forms
from . import models
from .mixins import PageTitleMixin as PtM
# noinspection PyUnresolvedReferences
from projects.models import Position, Project


class ValidateView(RedirectView):
    """Validate View - for user activation
    :url:
    ^accounts/validate/(?P<uid>[0-9A-Za-z_\-]+)/
    (?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$

    :inherit: - generic.RedirectView
    :methods: - get()
    :argument: - url"""
    url = reverse_lazy("accounts:profile_edit")

    def get(self, request, *args, **kwargs):
        """get method - use default_token_generator to verify user and token,
                    if pass user.is_active is set to True
        :param:: - request
                 - *args
                 - **kwargs"""
        pk = kwargs['uid']
        token = kwargs['token']
        try:
            # noinspection PyUnresolvedReferences
            user = models.User.objects.get(pk=pk)
        except(TypeError, ValueError, OverflowError, ObjectDoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            # In order to login() to work
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            user.save()
            login(request, user)
            messages.success(request, "Your account is now active. "
                                      "Complete your registration!")
        else:
            messages.warning(request, "Activation link is invalid.")
        return super().get(request, *args, **kwargs)


class SignInView(FormView):
    """Sign in view
    :url:
    ^accounts/signin/$

    :inherit: - generic.FormView
    :methods: - get_form()
              - form_valid()
    """
    form_class = AuthenticationForm
    success_url = reverse_lazy("projects:project_list")
    template_name = "accounts/signin.html"

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request, **self.get_form_kwargs())

    def form_valid(self, form):
        user, request = form.get_user(), self.request
        login(request, user)
        messages.success(request, 'Welcome {}'.format(user))
        return super().form_valid(form)


class SignOutView(LrM, RedirectView):
    """Sign out view
    :url:
    ^accounts/signout/$

    :inherit: - LrM (LoginRequiredMixin)
              - generic.RedirectView
    :methods: - get()"""
    url = reverse_lazy("projects:project_list")

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "You've been signed out. Come back soon!")
        return super().get(request, *args, **kwargs)


class SignUpView(CreateView):
    """Sign up view
    :url:
    ^accounts/signup/$

    :inherit: - generic.CreateView
    :methods: - form_valid()"""
    form_class = forms.UserCreateForm
    success_url = reverse_lazy("projects:project_list")
    template_name = "accounts/signup.html"
    context_object_name = "form"

    def form_valid(self, form):
        """form_valid method - sends a verification email for user activation
        using EmailMessage. Token is generated with default_token_generator"""
        if form.is_valid():
            user = form.save()
            email_to = form.cleaned_data.get('email')
            site = get_current_site(self.request)
            message = render_to_string('accounts/check_email.html', {
                'user': user,
                'domain': site.domain,
                'uid': user.pk,
                'token': default_token_generator.make_token(user), })
            email = EmailMessage('Activate your account.',
                                 message, to=[email_to])
            email.send()
            messages.info(self.request, "Check email for user activation!")
            return HttpResponseRedirect(self.success_url)


class UserProfileView(PrM, TemplateView):
    """User profile view
    :url:
    ^accounts/profile/(?P<pk>\d+)/$

    :inherit: - PrM (PrefetchRelatedMixin)
              - generic.TemplateView
    :methods: - get()
              - get_context_data()
    """
    template_name = "accounts/profile.html"
    context_object_name = "profile"
    prefetch_related = ['profile_skills', 'my_projects', 'projects', 'positions']

    def get(self, request, **kwargs):
        pk = kwargs.get('pk')
        profile = get_object_or_404(models.User, pk=pk)
        kwargs['profile'] = profile
        return super().get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skills'] = context['profile'].profile_skills.all()
        context['my_projects'] = context['profile'].my_projects.all()
        context['past_projects'] = context['profile'].projects.all()
        # import pdb; pdb.set_trace()
        return context


class UserProfileEditView(LrM, PtM, UpdateView):
    """User profile edit view
    :url:
    ^accounts/profile/edit/$

    :inherit: - LrM (mixins.LoginRequiredMixin)
              - PtM (PageTitleMixin)
              - generic.UpdateView
    :methods: - get_page_title()
              - get_object()
              - get_context_data()
              - post()
    """
    model = get_user_model()
    form_class = forms.UserProfileForm
    template_name = "accounts/profile_edit.html"
    context_object_name = "profile"

    def get_page_title(self):
        return 'Update {}'.format(self.object)

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        # noinspection PyUnresolvedReferences
        context['skill_formset'] = forms.SkillInlineFormSet(
            queryset=models.Skill.objects.filter(
                user=context['profile']),
            prefix="skill")
        # noinspection PyUnresolvedReferences
        context['project_formset'] = forms.ProjectInlineFormset(
            queryset=models.MyProject.objects.filter(
                user=context['profile']),
            prefix="project")
        return context

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        form = forms.UserProfileForm(
            request.POST, request.FILES, instance=user)
        # noinspection PyUnresolvedReferences
        skill_formset = forms.SkillInlineFormSet(
            request.POST,
            queryset=models.Skill.objects.filter(
                user=user),
            prefix="skill")
        # noinspection PyUnresolvedReferences
        project_formset = forms.ProjectInlineFormset(
            request.POST,
            queryset=models.MyProject.objects.filter(
                user=user),
            prefix="project")

        if (form.is_valid()
                and skill_formset.is_valid()
                and project_formset.is_valid()):
            profile_form = form.save(commit=False)
            profile_form.user = user
            profile_form.save()

            skills = skill_formset.save(commit=False)
            projects = project_formset.save(commit=False)

            # Skill formset
            for to_delete in skill_formset.deleted_objects:
                to_delete.delete()
            for skill in skills:
                name = skill.name
                if name:
                    models.Skill(user=user, name=name).save()

            # Project formset
            for to_delete in project_formset.deleted_objects:
                to_delete.delete()
            for project in projects:
                if not project.id:
                    # noinspection PyUnresolvedReferences
                    models.MyProject.objects.create(
                        user=user,
                        name=project.name,
                        url=project.url)
                else:
                    project.save()
            messages.success(request, "Profile updated successfully!")
            return HttpResponseRedirect(reverse_lazy("accounts:profile",
                                                     kwargs={'pk': request.user.id}))

        return HttpResponseRedirect(reverse('accounts:profile_edit',
                                            {'skill_formset': skill_formset,
                                             'project_formset': project_formset}))


class ApplicationView(LrM, PrM, ListView):
    """Application view
    :url:
    ^accounts/applications/$

    :inherit: - LrM (mixins.LoginRequiredMixin)
              - PrM (PrefetchRelatedMixin)
              - generic.ListView
    :methods: - choice() - staticmethod
              - get_context_data()
              - get_queryset()
    """
    template_name = "accounts/applications.html"
    model = models.UserApplication
    context_object_name = 'applications'
    prefetch_related = ['applicant__projects', ]

    @staticmethod
    def choice(arg):
        if arg == "New application":
            arg = None
        if arg == "Accepted":
            arg = True
        if arg == "Rejected":
            arg = False
        return arg

    def get_context_data(self, **kwargs):
        context = super(ApplicationView, self).get_context_data(**kwargs)
        context['applications'] = context['applications'].filter(
            project__user=self.request.user)
        # import pdb; pdb.set_trace()

        context['app_list'] = ['New application', 'Accepted', 'Rejected']
        # noinspection PyUnresolvedReferences
        context['projects'] = self.request.user.projects.all()
        # noinspection PyUnresolvedReferences
        context['skills_list'] = Position.objects.filter(
            project__in=context['projects']).values('name').distinct()

        context['pro_selected'] = self.request.GET.get('pro_filter')
        context['skill_selected'] = self.request.GET.get('skill_filter')
        context['app_selected'] = self.request.GET.get('app_filter')
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        app_term = self.request.GET.get('app_filter')
        pro_term = self.request.GET.get('pro_filter')
        skill_term = self.request.GET.get('skill_filter')
        if app_term:
            queryset = queryset.filter(status=self.choice(app_term))

        if pro_term:
            queryset = queryset.filter(project__title=pro_term)

        if skill_term:
            queryset = queryset.filter(position__name=skill_term)

        return queryset


class DecisionView(LrM, TemplateView):
    """Application view
    :url:
    ^accounts/applications/(?P<user_pk>\d+)/(?P<pos_pk>\d+)/(?P<decision>\w+)/$

    :inherit: - LrM (LoginRequiredMixin)
              - generic.TemplateView
    :methods: - application_update() - staticmethod
              - get()
    """
    @staticmethod
    def application_update(user, position, arg):
        # noinspection PyUnresolvedReferences
        models.UserApplication.objects.filter(
            applicant=user, position=position
        ).update(status=arg)

    def get(self, request, *args, **kwargs):
        user_pk = self.kwargs.get('user_pk')
        position_pk = self.kwargs.get('pos_pk')
        decision = self.kwargs.get('decision')
        user = models.User.objects.get(pk=user_pk)
        position = Position.objects.filter(pk=position_pk).first()
        message = ''
        if user and position:
            if decision == "accept":
                self.application_update(user, position, True)
                message = "accepted"
            if decision == "reject":
                self.application_update(user, position, False)
                message = "rejected"

            notify.send(user, recipient=user, actor=user,
                        verb='Your application for {} it was {}'.format(position.name, message),
                        decription="")
            return HttpResponseRedirect(reverse("accounts:application"))


class NotificationsView(LrM, TemplateView):
    """Notifications view
    :url:
    ^accounts/notifications/$

    :inherit: - LrM (LoginRequiredMixin)
              - generic.TemplateView
    :methods: - get_context_data()
              - get()
    """
    template_name = 'accounts/notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unreads'] = self.request.user.notifications.unread()
        return context

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AvatarView(LrM, UpdateView):
    """Avatar view - new avatar upload
    :url:
    ^accounts/profile/avatar/$

    :inherit: - LrM (LoginRequiredMixin)
              - generic.UpdateView
    :methods: - get_object()
              - get_context_data()
              - post()
    """
    form_class = forms.AvatarForm
    template_name = "accounts/avatar_edit.html"
    model = get_user_model()

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        form = forms.AvatarForm(
            request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('accounts:avatar_edit'))
        return HttpResponseRedirect(reverse('accounts:avatar_edit',
                                            {'form': form}))


class AvatarEditView(LrM, TemplateView):
    """Avatar edit view - rotate right-left, flip up-side
    :url:
    ^accounts/profile/avatar/edit/(?P<action>\w+)/$

    :inherit: - LrM (LoginRequiredMixin)
              - generic.TemplateView
    :methods: - edit() - staticmethod
              - get()
    """
    template_name = "accounts/avatar_edit.html"

    @staticmethod
    def edit(path, arg):
        with Image.open(path) as image:
            image = image.transpose(arg)
            image.save(path)

    def get(self, request, *args, **kwargs):
        action = self.kwargs.get('action')
        if action == 'left':
            self.edit(request.user.avatar.path, Image.ROTATE_90)
        if action == 'right':
            self.edit(request.user.avatar.path, Image.ROTATE_270)
        if action == 'up':
            self.edit(request.user.avatar.path, Image.FLIP_TOP_BOTTOM)
        if action == 'side':
            self.edit(request.user.avatar.path, Image.FLIP_LEFT_RIGHT)
        return HttpResponseRedirect(reverse('accounts:avatar_edit'))


class CropView(LrM, FormView):
    """Crop view - cropping
    :url:
    ^accounts/profile/avatar/crop/$

    :inherit: - LrM (LoginRequiredMixin)
              - generic.FormView
    :methods: - get_context_data()
              - post()
    """
    success_url = reverse_lazy("accounts:avatar_edit")
    template_name = "accounts/avatar_edit.html"
    form_class = forms.AvatarCropForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        with Image.open(self.request.user.avatar.path) as image:
            width, height = image.size
            size = str(width), str(height)
        context['size'] = size
        return context

    def post(self, request, *args, **kwargs):
        with Image.open(request.user.avatar.path) as image:
            width, height = image.size
            size = str(width), str(height)
            print('##### SIZE ####')
            print(size)
            print('###############')
            form = forms.AvatarCropForm(data=request.POST, request=request)

            if form.is_valid():
                new = (int(form.cleaned_data['left']),
                       int(form.cleaned_data['top']),
                       int(form.cleaned_data['right']),
                       int(form.cleaned_data['bottom']))
                image = image.crop(new)
                image.save(request.user.avatar.path)
                # import pdb; pdb.set_trace()
                return HttpResponseRedirect(reverse("accounts:avatar_edit"))
            return HttpResponseRedirect(reverse_lazy('accounts/avatar_edit.html',
                                        {'form': form}))
