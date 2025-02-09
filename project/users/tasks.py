import time

from celery import Task, shared_task
from celery.utils.log import get_task_logger

from project.database import db_context

# Removed the top-level import of api_call from views to fix circular dependency

logger = get_task_logger(__name__)


class BaseTaskWithRetry(Task):
    autoretry_for = (Exception, KeyError)
    retry_kwargs = {'max_retries': 5}
    retry_backoff = True


@shared_task
def divide(x: int, y: int) -> float:
    time.sleep(5)
    return x / y


@shared_task(retry_kwargs={'max_retries': 5})
def sample_task(email):
    # Lazy import to break the circular dependency
    from project.users.views import api_call

    api_call(email)


@shared_task(base=BaseTaskWithRetry)
def task_process_notification():
    time.sleep(3)
    print('hello')
    raise Exception()


@shared_task(name='low_priority:task_schedule_work')
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


@shared_task
def task_send_welcome_email(user_pk):
    from project.users.models import User

    with db_context() as session:
        user = session.get(User, user_pk)
        logger.info(f'send email to {user.email} {user.id}')


@shared_task()
def task_test_logger():
    logger.info('test')
