from django.contrib import messages
from django.contrib.auth import (get_user_model)
from django.contrib.auth.mixins import LoginRequiredMixin as LrM
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (CreateView, DetailView, DeleteView,
                                  ListView, TemplateView, UpdateView)

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
        context['position'] = models.Position.objects.filter(
            project__in=context['projects'])
        # print(dir(context['projects']))
        return context


class ProjectCreateView(LrM, PageTitleMixin, CreateView):
    model = models.Project
    form_class = forms.ProjectForm
    success_url = reverse_lazy("projects:project_list")
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
            self.request.POST,
            queryset=models.Position.objects.none())

        if form.is_valid() and position_formset.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()

            positions = position_formset.save(commit=False)
            for to_delete in position_formset.deleted_objects:
                to_delete.delete()

            for position in positions:
                name = position.name
                if name:
                    models.Position(
                        project=project,
                        name=name,
                        description=position.description).save()

            messages.success(request, 'Project created successfully!')

            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(request, 'Something went wrong')

        return HttpResponseRedirect(reverse('projects:create'))


class ProjectEditView(LrM, PageTitleMixin,
                      UpdateView):
    # model = models.Project
    form_class = forms.ProjectForm
    template_name = "projects/project_edit.html"
    context_object_name = "project"
    page_title = "Update project"

    def get(self, request, **kwargs):
        # pk = kwargs.get('pk')
        # noinspection PyUnresolvedReferences
        project = self.get_object()
        kwargs['project'] = project
        # project = self.get_object()
        # form = forms.ProjectForm(
        #     self.request.POST, request.FILES, instance=project)
        # print(project)
        # print(form.instance)
        return super().get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        # noinspection PyUnresolvedReferences
        context['position_formset'] = forms.PositionInlineFormset(
            queryset=models.Position.objects.filter(
                project=context['project']))

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        form = forms.ProjectForm(
            self.request.POST, request.FILES, instance=project)


        # noinspection PyUnresolvedReferences
        position_formset = forms.PositionInlineFormset(
            request.POST,
            queryset=models.Position.objects.filter(
                project=project))

        if form.is_valid() and position_formset.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()

            positions = position_formset.save(commit=False)
            for to_delete in position_formset.deleted_objects:
                to_delete.delete()

            for position in positions:
                name = position.name
                if name:
                    models.Position(
                        project=project,
                        name=name,
                        description=position.description).save()

            messages.success(request, 'Project updated successfully!')

            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(request, 'Something went wrong')

        # return HttpResponseRedirect(reverse('projects:edit'))
        return redirect(reverse('accounts:profile_edit',
                                {'form': form,
                                 'position_formset': position_formset}))

    # def get_page_title(self):
    #     obj = self.get_object()
    #     # print(obj.title)
    #     return f"Update {obj.title}"

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        project = get_object_or_404(models.Project, pk=pk)
        return project


class ProjectDetailView(DetailView):
    model = models.Project
    context_object_name = "project"
    template_name = "projects/project.html"
    # prefetch_related = ['positions', 'user']

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        # context['profile'] = context['project'].user
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
