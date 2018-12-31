from django.conf import settings
from django.db import models


class Project(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='projects',
                             on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    description = models.TextField(default='')
    time_estimate = models.CharField(max_length=100)
    requirements = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.title}'


class Position(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(default='')
    project = models.ForeignKey(Project, related_name='positions')
    time = models.CharField(max_length=30)
    skill = models.ManyToManyField('accounts.Skill',
                                   related_name='skills')

    def __str__(self):
        return f'{self.name}'


# class Notification(models.Model):
#     # user = CharField()
#     # not_status = CharField()
#     # project_status = ForeignKey(Position)
#     # accepted_rejected = CharField() or BooleanField()
#     pass

