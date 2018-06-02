import logging

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.functional import cached_property
from polyaxon_schemas.polyaxonfile.specification import BuildSpecification

from db.models.jobs import Job, JobStatus
from libs.spec_validation import validate_build_spec_config

logger = logging.getLogger('db.build_jobs')


class BuildJob(Job):
    """A model that represents the configuration for build job."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='+')
    project = models.ForeignKey(
        'db.Project',
        on_delete=models.CASCADE,
        related_name='build_jobs')
    config = JSONField(
        help_text='The compiled polyaxonfile for plugin job.',
        validators=[validate_build_spec_config])
    code_reference = models.ForeignKey(
        'db.CodeReference',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+')
    job_status = models.OneToOneField(
        'db.BuildJobStatus',
        related_name='+',
        blank=True,
        null=True,
        editable=True,
        on_delete=models.SET_NULL)

    class Meta:
        app_label = 'db'

    def __str__(self):
        return '{} build<{}, ref({})>'.format(self.project, self.image, self.code_reference)

    def save(self, *args, **kwargs):  # pylint:disable=arguments-differ
        if self.pk is None:
            last = BuildJob.objects.filter(project=self.project).last()
            self.sequence = 1
            if last:
                self.sequence = last.sequence + 1

        super(BuildJob, self).save(*args, **kwargs)

    @property
    def unique_name(self):
        return '{}.builds.{}'.format(self.project.unique_name, self.sequence)

    @cached_property
    def specification(self):
        return BuildSpecification.from_dict(self.config)

    @cached_property
    def image(self):
        return self.specification.build.image

    @cached_property
    def build_steps(self):
        return self.specification.build.build_steps

    @cached_property
    def env_vars(self):
        return self.specification.build.env_vars

    @cached_property
    def resources(self):
        return None

    @cached_property
    def node_selectors(self):
        return None

    @cached_property
    def env_vars(self):
        return self.specification.env_vars

    def set_status(self, status, message=None, details=None):  # pylint:disable=arguments-differ
        return self._set_status(status_model=BuildJobStatus,
                                logger=logger,
                                status=status,
                                message=message,
                                details=details)

    @staticmethod
    def create(user, project, config, code_reference):
        build_config = BuildSpecification.create_specification(config)
        try:
            job = BuildJob.objects.get(project=project,
                                       config=config,
                                       code_reference=code_reference)
        except BuildJob.DoesNotExist:
            job = BuildJob.objects.create(user=user,
                                          project=project,
                                          config=build_config,
                                          code_reference=code_reference)
        return job


class BuildJobStatus(JobStatus):
    """A model that represents build job status at certain time."""
    job = models.ForeignKey(
        'db.BuildJob',
        on_delete=models.CASCADE,
        related_name='statuses')

    class Meta(JobStatus.Meta):
        app_label = 'db'
        verbose_name_plural = 'Build Job Statuses'