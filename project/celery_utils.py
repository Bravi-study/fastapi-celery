from celery import Celery
from celery import current_app as current_celery_app
from celery.result import AsyncResult, states

from project.config import settings


def create_celery() -> Celery:
    celery_app = current_celery_app
    celery_app.config_from_object(settings, namespace='CELERY')

    return celery_app


def get_task_info(task_id: str) -> dict[str, str]:
    """
    return task info according to the task_id
    """
    task = AsyncResult(task_id)
    state = task.state
    response = {'state': state}

    if state == states.FAILURE:
        response['error'] = str(task.result)

    return response
