# NOTE: # noinspection - prefixed comments are for pycharm editor only
# for ignoring PEP 8 style highlights

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin as LrM
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import (CreateView, DetailView, DeleteView,
                                  ListView, TemplateView, UpdateView)
# from notify.signals import notify
from braces.views import PrefetchRelatedMixin as PrM

from . import forms
from . import models
from .mixin import PageTitleMixin as PtM
# noinspection PyUnresolvedReferences
from accounts.models import UserApplication


class ProjectListView(PrM, ListView):
    """Projects list view
    :url:
    ^$

    :inherit: - PrefetchRelatedMixin
              - generic.ListView
    :methods: - get_context_data()
              - get_queryset()
    """
    template_name = "projects/project_list.html"
    model = models.Project
    context_object_name = "projects"
    prefetch_related = ['positions', ]

    def get_context_data(self, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        # noinspection PyUnresolvedReferences
        positions = models.Position.objects.exclude(apply__status=True)
        context['positions_list'] = positions.values('name').distinct()
        context['selected'] = self.request.GET.get('filter')
        return context

    def get_queryset(self):
        user_skills = None
        # noinspection PyUnresolvedReferences
        queryset = super().get_queryset()
        user = self.request.user
        # import pdb; pdb.set_trace()

        if str(user) != 'AnonymousUser':
            user_skills = user.profile_skills.all().values('name')
            user_skills = [skill['name'] for skill in user_skills.values()]
        for_you = self.request.GET.get('for_you')
        term = self.request.GET.get('q')
        selected_filter = self.request.GET.get('filter')
        if for_you:
            queryset = queryset.filter(Q(
                positions__skill__name__in=user_skills)).exclude(
                user=self.request.user).distinct()
        if term:
            queryset = queryset.filter(Q(title__icontains=term) |
                                       Q(description__icontains=term))
        if selected_filter:
            queryset = queryset.filter(Q(positions__name=selected_filter))
        return queryset


class ProjectCreateView(LrM, CreateView):
    """Project list view
    :url:
    ^project/new/$

    :inherit: - LrM (loginRequiredMixin)
              - generic.CreateView
    :methods: - get_context_data()
              - post()
    """
    model = models.Project
    form_class = forms.ProjectForm
    template_name = "projects/project_new.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectCreateView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        # noinspection PyUnresolvedReferences
        context['position_formset'] = forms.PositionInlineFormset(
            queryset=models.Position.objects.none())
        return context

    def post(self, request, *args, **kwargs):
        form = forms.ProjectForm(request.POST)
        # noinspection PyUnresolvedReferences
        position_formset = forms.PositionInlineFormset(
            request.POST,
            queryset=models.Position.objects.none())

        if form.is_valid() and position_formset.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()

            positions = position_formset.save(commit=False)
            for to_delete in position_formset.deleted_objects:
                to_delete.delete()

            for position in positions:
                position.project = project
                position.save()
            position_formset.save_m2m()
            messages.success(request, 'Project created successfully!')

            return HttpResponseRedirect(reverse_lazy("projects:detail",
                                                     kwargs={'pk': project.id}))
        else:
            messages.error(request, position_formset.errors)
            # print("ERRORS: ", position_formset.errors)
        return HttpResponseRedirect(reverse('projects:create'))


class ProjectEditView(LrM, PtM, UpdateView):
    """Project Edit view
    :url:
    project/(?P<pk>\d+)/edit/$

    :inherit: - LrM (mixins.loginRequiredMixin)
              - PtM (PageTitleMixin)
              - generic.UpdateView
    :methods: - get_page_title()
              - get_object()
              - get_context_data()
              - post()
    """
    form_class = forms.ProjectForm
    template_name = "projects/project_edit.html"
    context_object_name = "project"

    def get_page_title(self):
        return "Update {}".format(self.object)

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        # noinspection PyUnresolvedReferences
        project = models.Project.objects.filter(pk=pk).first()
        return project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        # noinspection PyUnresolvedReferences
        context['position_formset'] = forms.PositionInlineFormset(
            queryset=models.Position.objects.filter(
                project=context['project']))
        return context

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        form = forms.ProjectForm(
            request.POST, request.FILES, instance=project)

        # noinspection PyUnresolvedReferences
        position_formset = forms.PositionInlineFormset(
            request.POST,
            queryset=models.Position.objects.filter(
                project=project))

        if form.is_valid() and position_formset.is_valid():
            project = form.save()
            positions = position_formset.save(commit=False)
            for to_delete in position_formset.deleted_objects:
                to_delete.delete()
            for position in positions:
                position.project = project
                position.save()
            position_formset.save_m2m()
            messages.success(request, 'Project updated successfully!')

            return HttpResponseRedirect(reverse_lazy("projects:detail",
                                                     kwargs={'pk': project.id}))
        else:
            messages.error(request, 'Something went wrong')

        return HttpResponseRedirect(reverse_lazy('projects:edit'))


class ProjectDetailView(PrM, DetailView):
    """Project Detail view
    :url:
    project/(?P<pk>\d+)/$

    :inherit: - PrM (PrefetchRelatedMixin)
              - generic.DetailView
    :methods: - get_context_data()
    """
    model = models.Project
    context_object_name = "project"
    template_name = "projects/project.html"
    prefetch_related = ['positions', 'user', 'positions__apply']

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        # noinspection PyUnresolvedReferences
        positions = models.Position.objects.all()
        context['positions'] = positions.filter(
            project=context['project']).exclude(apply__status=True)
        if str(user) != "AnonymousUser":
            # noinspection PyUnresolvedReferences
            context['applied'] = positions.filter(
                project=context['project'],
                apply__applicant=user)
        else:
            # noinspection PyUnresolvedReferences
            context['applied'] = positions.filter(
                project=context['project']
            )
        # print(dir(context['applied'].values))
        return context


class ProjectDeleteView(LrM, DeleteView):
    """Project delete view
    :url:
    project/(?P<pk>\d+)/delete/$

    :inherit: - LrM (loginRequiredMixin)
              - generic.DeleteView
    :methods: - get_object()
    """
    model = models.Project
    form_class = forms.ProjectForm
    template_name = "projects/project_delete.html"
    context_object_name = "project"
    success_url = reverse_lazy("projects:project_list")

    def get_object(self, queryset=None):
        project = super().get_object()
        if project.user != self.request.user:
            raise Http404('You are not allowed to delete!')
        return project


class ApplyView(LrM, TemplateView):
    """Apply view
    :url:
    project/(?P<pr_pk>\d+)/apply/position/(?P<ps_pk>\d+)/$

    :inherit: - LrM (loginRequiredMixin)
              - generic.DeleteView
    :methods: - get_object()
    """
    def get(self, request, *args, **kwargs):
        user = request.user
        project_pk = kwargs.get('pr_pk')
        position_pk = kwargs.get('ps_pk')
        # noinspection PyUnresolvedReferences
        project = get_object_or_404(models.Project, pk=project_pk)
        # noinspection PyUnresolvedReferences
        position = get_object_or_404(models.Position, pk=position_pk)
        obj, _ = UserApplication.objects.get_or_create(
            applicant=user,
            project=project,
            position=position,
            defaults={'applicant': user, 'project': project, 'position': position})
        obj.save()
        return HttpResponseRedirect(reverse_lazy('projects:detail',
                                                 kwargs={'pk': project.id}))
