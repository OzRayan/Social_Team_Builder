from django.conf import settings
from django.db import models


class Project(models.Model):
    """Project model
    :inherit: - models.Model
    :fields: - user, title, description, time_estimate, requirements
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='projects',
                             on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    description = models.TextField(default='')
    time_estimate = models.CharField(max_length=100)
    requirements = models.CharField(max_length=255)

    def __str__(self):
        return '{}'.format(self.title)


class Position(models.Model):
    """Position model
    :inherit: - models.Model
    :fields: - name, description, project, time, skill
    """
    name = models.CharField(max_length=50)
    description = models.TextField(default='')
    project = models.ForeignKey(Project,
                                related_name='positions',
                                on_delete=models.CASCADE)
    time = models.CharField(max_length=30)
    skill = models.ManyToManyField('accounts.Skill',
                                   default='',
                                   related_name='skills')

    def __str__(self):
        return '{}'.format(self.name)

