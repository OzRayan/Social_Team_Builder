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
    """User Manager class for creating user and superuser
    :inherit: - models.BaseUserManager
    :methods: - create_user()
              - create_superuser()"""
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
    """User model
    :inherit: - models.AbstractBaseUser
              - models.PermissionsMixin
    :fields: - base fields: - username, email, date_joined, is_active, is_staff
             - project related fields: - first_name, last_name, bio, avatar
    :methods: - full_name() as a property
              - __str__()
              - get_absolute_url()
              - get_short_name()
    """
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    bio = models.TextField(default='')
    avatar = models.ImageField(upload_to='./user_avatar', blank=True)

    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # objects which use the UserManager class
    objects = UserManager()

    USERNAME_FIELD = "email"
    # Required field for login
    REQUIRED_FIELDS = ['username']

    @property
    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def get_absolute_url(self):
        return reverse("accounts:profile",
                       {'username': self.username})

    def __str__(self):
        return self.username

    def get_short_name(self):
        return self.username

    def get_full_name(self):
        return self.full_name


class Skill(models.Model):
    """Skill model
    :inherit: - models.Model
    :fields: - user, name
    :methods: - __str__()
    """
    user = models.ForeignKey(User, default='', related_name="profile_skills")
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class MyProject(models.Model):
    """Own project model
    :inherit: - models.Model
    :fields: - user, name, url
    :methods: - __str__()
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='my_projects',
                             on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    url = models.URLField()

    def __str__(self):
        return self.name


class UserApplication(models.Model):
    """User Application model
    :inherit: - models.Model
    :fields: - applicant, position, project, status
    """
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.CASCADE,
                                  related_name='application')
    position = models.ForeignKey('projects.Position', related_name='apply')
    project = models.ForeignKey('projects.Project')
    status = models.NullBooleanField(default=None)
