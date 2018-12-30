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
                                  TemplateView, UpdateView, DetailView)

from braces.views import SelectRelatedMixin, PrefetchRelatedMixin

from . import forms
from . import models
from .mixins import PageTitleMixin


class ValidateView(RedirectView):
    url = reverse_lazy("accounts:profile_edit")

    def get(self, request, *args, **kwargs):
        pk = kwargs['uid']
        token = kwargs['token']
        try:
            # noinspection PyUnresolvedReferences
            user = models.User.objects.get(pk=pk)
        except(TypeError, ValueError, OverflowError, ObjectDoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            user.save()
            login(request, user)
            messages.info(request, "Your account is now active. "
                                   "Complete your registration!")
        else:
            messages.warning(request, "Activation link is invalid.")
        return super().get(request, *args, **kwargs)


class SignInView(FormView):
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
    url = reverse_lazy("projects:project_list")

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "You've been signed out. Come back soon!")
        return super().get(request, *args, **kwargs)


class SignUpView(CreateView):
    form_class = forms.UserCreateForm
    success_url = reverse_lazy("projects:project_list")
    template_name = "accounts/signup.html"
    context_object_name = "form"

    def form_valid(self, form):
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


class UserProfileView(LrM, PageTitleMixin,
                      PrefetchRelatedMixin,
                      TemplateView):
    template_name = "accounts/profile.html"
    model = get_user_model()
    context_object_name = "profile"
    prefetch_related = ['my_projects', 'profile_skill']

    def get(self, request, **kwargs):
        pk = kwargs.get('pk')
        profile = get_object_or_404(models.User, pk=pk)
        kwargs['profile'] = profile
        return super().get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skills'] = context['profile'].skills.all()
        context['my_projects'] = context['profile'].my_projects.all()
        return context

    def get_object(self, queryset=None):
        return self.request.user

    def get_page_title(self):
        obj = self.get_object()
        return f"{obj}'s Profile"


class UserProfileEditView(LrM, PageTitleMixin, UpdateView):
    model = get_user_model()
    form_class = forms.UserProfileForm
    template_name = "accounts/profile_edit.html"
    context_object_name = "profile"

    def get(self, request, **kwargs):
        profile = self.request.user
        kwargs['profile'] = profile
        return super().get(request, **kwargs)

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

    def get_page_title(self):
        obj = self.get_object()
        return f'Update {obj.username}'

    def get_object(self, queryset=None):
        return self.request.user


# This view still needs work!!!
# #############################
class PasswordEditView(LrM, PageTitleMixin, UpdateView):
    # model = get_user_model()
    form_class = forms.PasswordForm
    success_url = reverse_lazy("accounts:profile")
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
        form = forms.PasswordForm(data=request.POST, request=user)
        if form.is_valid():
            if user.check_password(form.cleaned_data.get('old')):
                user.set_password(form.cleaned_data.get('new'))
                user.save()
                update_session_auth_hash(self.request, user)
        return super().form_valid(form)


@login_required
def password_edit_view(request):
    """password_edit_view prepare user data for form, check password auth
    :decorator: - login_required
    :input: - request
    :returns: - HttpResponseRedirect profile detail
              - render template(accounts/password_edit.html) with form
    """
    user = request.user
    form = forms.PasswordForm(request=request)
    if request.method == "POST":
        form = forms.PasswordForm(data=request.POST, request=request)
        if form.is_valid():
            if user.check_password(form.cleaned_data.get('old')):
                user.set_password(form.cleaned_data.get('new'))
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password saved!")
                return HttpResponseRedirect('/accounts/profile/')

            else:
                messages.error(request, "Old password incorrect.")

    return render(request, 'accounts/password_edit.html', {'form': form})


class ApplicationView(LrM, PrefetchRelatedMixin, TemplateView):
    template_name = "accounts/applications.html"

    def get_context_data(self, **kwargs):
        context = super(ApplicationView, self).get_context_data(**kwargs)
        # noinspection PyUnresolvedReferences
        context['skills'] = models.Skill.objects.all()
        return context
