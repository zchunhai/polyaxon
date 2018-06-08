import logging

from constants.jobs import JobLifeCycle
from db.getters.tensorboards import get_valid_tensorboard
from polyaxon.celery_api import app as celery_app
from polyaxon.settings import SchedulerCeleryTasks
from scheduler import tensorboard_scheduler

_logger = logging.getLogger(__name__)


@celery_app.task(name=SchedulerCeleryTasks.TENSORBOARDS_START, ignore_result=True)
def tensorboards_start(tensorboard_job_id):
    tensorboard = get_valid_tensorboard(tensorboard_job_id=tensorboard_job_id)
    if not tensorboard:
        _logger.warning('Tensorboard %s does not exist anymore.', tensorboard_job_id)
        return None

    if not JobLifeCycle.can_transition(status_from=tensorboard.last_status,
                                       status_to=JobLifeCycle.SCHEDULED):
        _logger.info('Tensorboard `%s` cannot transition from `%s` to `%s`.',
                     tensorboard.unique_name, tensorboard.last_status, JobLifeCycle.SCHEDULED)

    tensorboard_scheduler.start_tensorboard(tensorboard)


@celery_app.task(name=SchedulerCeleryTasks.TENSORBOARDS_STOP, ignore_result=True)
def tensorboards_stop(tensorboard_job_id):
    tensorboard = get_valid_tensorboard(tensorboard_job_id=tensorboard_job_id)
    if not tensorboard:
        return None
    tensorboard_scheduler.stop_tensorboard(tensorboard, update_status=True)
