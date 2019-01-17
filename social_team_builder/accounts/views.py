from django.contrib import messages
from django.contrib.auth import (get_user_model, login, logout,
                                 update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin as LrM
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.generic import (CreateView, FormView, RedirectView,
                                  TemplateView, UpdateView, ListView)

from braces.views import SelectRelatedMixin, PrefetchRelatedMixin

from . import forms
from . import models
from .mixins import PageTitleMixin
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
            messages.info(request, "Your account is now active. "
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
        messages.success(request, f'Welcome {user}')
        return super().form_valid(form)


class SignOutView(LrM, RedirectView):
    """Sign out view
    :url:
    ^accounts/signout/$

    :inherit: - (LrM) mixins.LoginRequiredMixin
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
            messages.success(self.request, "Check email for user activation!")
            return redirect(self.success_url)


class UserProfileView(PageTitleMixin,
                      PrefetchRelatedMixin,
                      TemplateView):
    """User profile view
    :url:
    ^accounts/profile/(?P<pk>\d+)/$

    :inherit: - PageTitleMixin (custom mixin)
              - generic.TemplateView
    :methods: - get_page_title()
              - get_context_data()
    """
    template_name = "accounts/profile.html"
    model = get_user_model()
    context_object_name = "profile"
    prefetch_related = ['my_projects', 'profile_skills']
    #
    # def get_object(self, queryset=None):
    #     return self.request.user

    def get(self, request, **kwargs):
        pk = kwargs.get('pk')
        profile = models.User.objects.get(pk=pk)
        kwargs['profile'] = profile
        return super().get(request, **kwargs)
    #
    #
    # def get_page_title(self):
    #     # obj = self.get_object()
    #     return f"{self.get_object()}'s Profile"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skills'] = context['profile'].profile_skills.all()
        context['my_projects'] = context['profile'].my_projects.all()
        return context


class UserProfileEditView(LrM, PageTitleMixin, UpdateView):
    """User profile edit view
    :url:
    ^accounts/profile/edit/$

    :inherit: - (LrM) LoginRequiredMixin
              - PageTitleMixin (custom mixin)
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
        return f'Update {self.object}'

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
            self.request.POST, request.FILES, instance=user)
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
            # print(dir(skill_formset))

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

        return redirect(reverse('accounts:profile_edit',
                                {'form': form,
                                 'skill_formset': skill_formset,
                                 'project_formset': project_formset}))


# This view still needs work!!!
# #############################
class PasswordEditView(LrM, PageTitleMixin, UpdateView):
    # model = get_user_model()
    form_class = forms.PasswordForm
    # success_url = reverse_lazy("accounts:profile")
    template_name = "accounts/password_edit.html"
    page_title = "Update Password"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        form = forms.PasswordForm(data=request.POST, request=request)
        if form.is_valid():
            if user.check_password(form.cleaned_data.get('old')):
                user.set_password(form.cleaned_data.get('new'))
                user.save()
                update_session_auth_hash(self.request, user)
                return HttpResponseRedirect(reverse_lazy('acounts:profile'))
        return HttpResponseRedirect(reverse("accounts:password_edit"))


# @login_required
# # def password_edit_view(request):
# #     """password_edit_view prepare user data for form, check password auth
# #     :decorator: - login_required
# #     :input: - request
# #     :returns: - HttpResponseRedirect profile detail
# #               - render template(accounts/password_edit.html) with form
# #     """
# #     user = request.user
# #     form = forms.PasswordForm(request=request)
# #     if request.method == "POST":
# #         form = forms.PasswordForm(data=request.POST, request=request)
# #         if form.is_valid():
# #             if user.check_password(form.cleaned_data.get('old')):
# #                 user.set_password(form.cleaned_data.get('new'))
# #                 user.save()
# #                 update_session_auth_hash(request, user)
# #                 messages.success(request, "Password saved!")
# #                 return HttpResponseRedirect('accounts/profile/')
# #
# #             else:
# #                 messages.error(request, "Old password incorrect.")
# #
# #     return render(request, 'accounts/password_edit.html', {'form': form})


class ApplicationView(LrM, PrefetchRelatedMixin, ListView):
    template_name = "accounts/applications.html"
    model = models.UserApplication
    context_object_name = 'applications'
    prefetch_related = ['projects', ]

    def get_context_data(self, **kwargs):
        context = super(ApplicationView, self).get_context_data(**kwargs)
        pk = self.request.user.id
        context['applications_list'] = self.get_queryset().values('status')
        # noinspection PyUnresolvedReferences
        context['projects'] = Project.objects.filter(user_id=pk)
        # noinspection PyUnresolvedReferences
        context['skills_list'] = Position.objects.exclude(
            apply__status=True).values('name').distinct()
        context['pro_selected'] = self.request.GET.get('pro_filter')
        context['skill_selected'] = self.request.GET.get('skill_filter')
        context['app_selected'] = self.request.GET.get('app_filter')
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        app_term = self.request.GET.get('app_filter')
        pro_term = self.request.GET.get('pro_filter')
        skill_term = self.request.GET.get('skill_filter')
        user = models.User.objects.all().exclude(pk=self.request.user.id)
        print(user)


