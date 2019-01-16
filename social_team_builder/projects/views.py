from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin as LrM
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q

from django.http import HttpResponseRedirect, HttpResponse, Http404

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (CreateView, DetailView, DeleteView,
                                  ListView, TemplateView, UpdateView)
from notify.signals import notify
from braces.views import SelectRelatedMixin, PrefetchRelatedMixin

from . import forms
from . import models
from .mixin import PageTitleMixin
# noinspection PyUnresolvedReferences
from accounts.models import UserApplication


class ProjectListView(ListView):
    """Projects list view
    :url:
    ^$

    :inherit: - PageTitleMixin (custom mixin)
              - generic.ListView
    :methods: - get_context_data()
              - get_queryset()
    """
    template_name = "projects/project_list.html"
    model = models.Project
    context_object_name = "projects"
    # prefetch_related = ['positions']

    def get_context_data(self, **kwargs):
        positions = models.Position.objects.exclude(
            apply__status=True)
        context = super(ProjectListView, self).get_context_data(**kwargs)
        # noinspection PyUnresolvedReferences
        context['positions_list'] = positions.values('name').distinct()
        context['positions'] = positions
        # print(dir(context['positions'].distinct()))
        context['selected'] = self.request.GET.get('filter')
        return context

    def get_queryset(self):
        # noinspection PyUnresolvedReferences
        queryset = super().get_queryset()
        term = self.request.GET.get('q')
        if term:
            queryset = queryset.filter(Q(title__icontains=term) |
                                       Q(description__icontains=term))
        selected_filter = self.request.GET.get('filter')
        if selected_filter:
            queryset = queryset.filter(Q(positions__name=selected_filter))
        return queryset


class ProjectCreateView(LrM, PageTitleMixin, CreateView):
    """Project list view
    :url:
    project/new/$

    :inherit: - (LrM) loginRequiredMixin
              - PageTitleMixin (custom mixin)
              - generic.CreateView
    :methods: - get_context_data()
              - post()
    """
    model = models.Project
    form_class = forms.ProjectForm
    template_name = "projects/project_new.html"
    page_title = "Create project"

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
            messages.error(request, 'Something went wrong')

        return HttpResponseRedirect(reverse('projects:create'))


class ProjectEditView(LrM, PageTitleMixin,
                      UpdateView):
    """Project Edit view
    :url:
    project/(?P<pk>\d+)/edit/$

    :inherit: - (LrM) loginRequiredMixin
              - PageTitleMixin (custom mixin)
              - generic.UpdateView
    :methods: - get_page_title()
              - get_object()
              - get_context_data()
              - post()
    """
    # model = models.Project
    form_class = forms.ProjectForm
    template_name = "projects/project_edit.html"
    context_object_name = "project"

    def get_page_title(self):
        return f"Update {self.object}"

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
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
            project = form.save(commit=False)
            # project.user = request.user
            project.save()

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

        # return HttpResponseRedirect(reverse('projects:edit'))
        return HttpResponseRedirect(reverse('accounts:profile_edit'))


class ProjectDetailView(PrefetchRelatedMixin, DetailView):
    """Project Detail view
    :url:
    project/(?P<pk>\d+)/$

    :inherit: - generic.DetailView
    :methods: - get_context_data()
    """
    model = models.Project
    context_object_name = "project"
    template_name = "projects/project.html"
    prefetch_related = ['positions', 'user', 'positions__apply']

    def get_context_data(self, **kwargs):
        user = self.request.user
        print(dir(user))
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        # noinspection PyUnresolvedReferences
        context['positions'] = models.Position.objects.filter(
            project=context['project']).exclude(apply__status=True)
        # noinspection PyUnresolvedReferences
        if user.is_authenticated():
            context['applied'] = models.Position.objects.filter(
                project=context['project'],
                apply__applicant=user)
        else:
            context['applied'] = models.Position.objects.filter(
                project=context['project']
            )
        # print(dir(context['applied'].values))
        return context


class ProjectDeleteView(LrM, DeleteView):
    """Project delete view
    :url:
    project/(?P<pk>\d+)/delete/$

    :inherit: - (LrM) loginRequiredMixin
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


class ApplyView(LrM, PageTitleMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        user = request.user
        project_pk = kwargs.get('pr_pk')
        position_pk = kwargs.get('ps_pk')
        # noinspection PyUnresolvedReferences
        project = models.Project.objects.get(pk=project_pk)
        # noinspection PyUnresolvedReferences
        position = models.Position.objects.get(pk=position_pk)
        obj, _ = UserApplication.objects.get_or_create(
            applicant=user,
            project=project,
            position=position,
            defaults={'applicant': user, 'project': project, 'position': position})
        obj.save()
        return HttpResponseRedirect(reverse_lazy('projects:project_list'))


