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


# Still needs a lot of work ##########
class ProjectListView(PrefetchRelatedMixin, ListView):
    template_name = "projects/project_list.html"
    model = models.Project
    context_object_name = "projects"
    prefetch_related = ['positions']

    def get_context_data(self, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        # noinspection PyUnresolvedReferences
        context['positions'] = models.Position.objects.filter(
            project__in=context['projects'])
        context['filter'] = self.request.GET.get('position')
        return context

    def get_queryset(self):
        # noinspection PyUnresolvedReferences
        queryset = super().get_queryset()
        term = self.request.GET.get('q')

        if term:
            queryset = queryset.filter(Q(title__icontains=term) |
                                       Q(description__icontains=term))
        return queryset


class ProjectCreateView(LrM, PageTitleMixin, CreateView):
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
    # model = models.Project
    form_class = forms.ProjectForm
    template_name = "projects/project_edit.html"
    context_object_name = "project"
    success_url = reverse_lazy('projects:project_list')

    def get_page_title(self):
        return f"Update {self.object}"

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        project = get_object_or_404(models.Project, pk=pk)
        return project

    def get_context_data(self, **kwargs):
        context = super(ProjectEditView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        # noinspection PyUnresolvedReferences
        context['position_formset'] = forms.PositionInlineFormset(
            queryset=models.Position.objects.filter(
                project=context['project']))
        print(dir(context['position_formset']))
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


class ProjectDetailView(DetailView):
    model = models.Project
    context_object_name = "project"
    template_name = "projects/project.html"
    # prefetch_related = ['positions', 'user']

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        # noinspection PyUnresolvedReferences
        context['positions'] = models.Position.objects.filter(
            project=context['project'])
        return context


class ProjectDeleteView(LrM, DeleteView):
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
    pass
