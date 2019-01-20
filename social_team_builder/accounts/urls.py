from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"signin/$", views.SignInView.as_view(), name="signin"),
    url(r"signout/$", views.SignOutView.as_view(), name="signout"),
    url(r"signup/$", views.SignUpView.as_view(), name="signup"),
    url(r"profile/(?P<pk>\d+)/$", views.UserProfileView.as_view(),
        name='profile'),
    url(r"profile/edit/$", views.UserProfileEditView.as_view(),
        name='profile_edit'),
    url(r'profile/password/$', views.PasswordEditView.as_view(),
        name='password_edit'),
    url(r'applications/$', views.ApplicationView.as_view(),
        name='application'),
    url(r'applications/(?P<user_pk>\d+)/(?P<pos_pk>\d+)/(?P<decision>\w+)/$',
        views.DecisionView.as_view(), name='decision_update'),
    url(r'notifications/$', views.NotificationsView.as_view(), name='own_notifications'),
    url(r'validate/(?P<uid>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.ValidateView.as_view(), name='validate'),
]
