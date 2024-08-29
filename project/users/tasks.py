import random
import time

import requests
from asgiref.sync import async_to_sync
from celery import Task, shared_task
from celery.signals import task_postrun
from celery.utils.log import get_task_logger

from project.users.views import api_call
from project.ws.views import (
    update_celery_task_status,
    update_celery_task_status_socketio,
)

logger = get_task_logger(__name__)


class BaseTaskWithRetry(Task):
    autoretry_for = (Exception, KeyError)
    retry_kwargs = {'max_retries': 5}
    retry_backoff = True


@shared_task
def divide(x: int, y: int) -> float:
    # from celery.contrib import rdb
    # rdb.set_trace()

    time.sleep(5)
    return x / y


@shared_task(retry_kwargs={'max_retries': 5})
def sample_task(email):
    api_call(email)


@shared_task(bind=True)
def task_process_notification(self):
    try:
        if not random.choice([0, 1]):
            # mimic random error
            raise Exception()

        # this would block the I/O
        requests.post('https://httpbin.org/delay/5')
    except Exception as e:
        logger.error('exception raised, it would be retry after 5 seconds')
        raise self.retry(exc=e, countdown=5)


# @task_postrun.connect
# def task_postrun_handler(task_id, **kwargs):
#     async_to_sync(update_celery_task_status)(task_id)
#     update_celery_task_status_socketio(task_id)


@shared_task(name='task_schedule_work')
def task_schedule_work():
    logger.info('task_schedule_work run')


@shared_task(name='default:dynamic_example_one')
def dynamic_example_one():
    logger.info('Example One')


@shared_task(name='low_priority:dynamic_example_two')
def dynamic_example_two():
    logger.info('Example Two')


@shared_task(name='high_priority:dynamic_example_three')
def dynamic_example_three():
    logger.info('Example Three')


@shared_task(bind=True, base=BaseTaskWithRetry, name='default:fail_take')
def fail_process_notification(self):
    time.sleep(3)
    try:
        raise Exception()
    except Exception as e:
        logger.error('exception raised, it would be retry after 5 seconds')
        raise self.retry(exc=e, countdown=5)
