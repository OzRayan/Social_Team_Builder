from django.contrib import admin
from .models import User, UserApplication, Skill

admin.site.register(User)
admin.site.register(UserApplication)
admin.site.register(Skill)
