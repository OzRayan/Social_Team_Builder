"""social_team_builder URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import url, include, patterns
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings


urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^accounts/", include("accounts.urls", namespace="accounts")),
    url(r"^accounts/", include("django.contrib.auth.urls")),
    url(r'^notifications/', include('notify.urls', namespace='notifications')),
    url(r"^", include("projects.urls", namespace="projects")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Setting up urlpatterns for django-debug-toolbar(version==1.9.1)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += url(r'^__debug__/', include(debug_toolbar.urls)),

urlpatterns += staticfiles_urlpatterns()
