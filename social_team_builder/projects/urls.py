from django.conf.urls import url


from . import views

app_name = 'social_team_builder'

urlpatterns = [
    url(r'^$', views.ProjectListView.as_view(), name='project_list'),
    url(r'project/new/$', views.ProjectCreateView.as_view(), name='create'),
    url(r'project/(?P<pk>\d+)/$', views.ProjectDetailView.as_view(), name='detail'),
    url(r'project/(?P<pk>\d+)/delete/$', views.ProjectDeleteView.as_view(), name='delete'),
    url(r'project/(?P<pk>\d+)/edit/$', views.ProjectEditView.as_view(), name='edit'),
    url(r'project/(?P<pr_pk>\d+)/apply/position/(?P<ps_pk>\d+)/$', views.ApplyView.as_view(), name='apply'),
]
