from django.conf.urls import url


from . import views

urlpatterns = [
    url(r'^$', views.ProjectListView.as_view(), name='project_list'),
    # url(r'search/$', views.SearchView.as_view(), name='search'),
    url(r'project/new/$', views.ProjectCreateView.as_view(), name='create'),
    url(r'project/(?P<pk>\d+)/$', views.ProjectDetailView.as_view(), name='detail'),
    url(r'project/(?P<pk>\d+)/delete/$', views.ProjectDeleteView.as_view(), name='delete'),
    url(r'project/(?P<pk>\d+)/edit/$', views.ProjectEditView.as_view(), name='edit'),
]
