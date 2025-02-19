import os
import pathlib
from functools import cache

from kombu import Queue


def route_task(name: str, args, kwargs, options, task=None, **kw) -> dict[str, str]:
    if ':' in name:
        queue, _ = name.split(':')
    else:
        queue = 'default'

    return {'queue': queue}


class BaseConfig:
    BASE_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent

    DATABASE_URL: str = os.environ.get(
        'DATABASE_URL', f'sqlite:///{BASE_DIR}/db.sqlite3'
    )
    ASYNC_DATABASE_URL: str = os.environ.get(
        'ASYNC_DATABASE_URL',
        'postgresql+asyncpg://fastapi_celery:fastapi_celery@db/fastapi_celery',
    )
    DATABASE_CONNECT_DICT: dict = {}

    WS_MESSAGE_QUEUE: str = os.environ.get(
        'WS_MESSAGE_QUEUE', 'redis://127.0.0.1:6379/0'
    )
    CELERY_BROKER_URL: str = os.environ.get(
        'CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0'
    )
    CELERY_RESULT_BACKEND: str = os.environ.get(
        'CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/0'
    )
    CELERY_BEAT_SCHEDULE: dict[str, dict] = {
        # 'task-schedule-work': {
        #     'task': 'task_schedule_work',
        #     'schedule': 5.0,  # five seconds
        # },
    }
    CELERY_TASK_DEFAULT_QUEUE: str = 'default'
    CELERY_TASK_CREATE_MISSING_QUEUES: bool = False
    CELERY_TASK_QUEUES: list[Queue] = [
        # need to define default queue here or exception would be raised
        Queue('default'),
        Queue('high_priority'),
        Queue('low_priority'),
    ]
    # CELERY_TASK_ROUTES = {
    #     'project.users.tasks.*': {
    #         'queue': 'high_priority',
    #     },
    # }
    CELERY_TASK_ROUTES = (route_task,)


class DevelopmentConfig(BaseConfig):
    pass


class ProductionConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    pass


@cache
def get_settings() -> BaseConfig:
    config_cls_dict = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
    }
    config_name = os.environ.get('FASTAPI_CONFIG', 'development')
    config_cls = config_cls_dict[config_name]

    return config_cls()


settings = get_settings()
