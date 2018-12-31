from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, username=None, password=None):
        if not email:
            raise ValueError('Users must have an email address!')
        if not username:
            username = email.split('@')[:1]

        user = self.model(
            username=username,
            email=self.normalize_email(email)
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(
            username,
            email,
            password
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    bio = models.TextField(default='')
    avatar = models.ImageField(upload_to='./user_avatar', blank=True)

    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_absolute_url(self):
        return reverse("accounts:profile",
                       {'username': self.username})

    def __str__(self):
        return self.username

    def get_short_name(self):
        return self.username

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'


class Skill(models.Model):
    user = models.ForeignKey(User, related_name="profile_skills")
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class MyProject(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='my_projects',
                             on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    url = models.URLField()

    def __str__(self):
        return self.name


class UserApplication(models.Model):
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.CASCADE,
                                  related_name='application')
    position = models.ForeignKey('projects.Position', related_name='applications')
    project = models.ForeignKey('projects.Project')
    status = models.NullBooleanField(default=None)

