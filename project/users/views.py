import logging
import random

import requests
from celery.result import AsyncResult, states
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .schemas import UserBody

logger = logging.getLogger(__name__)

users_router = APIRouter(prefix='/users')

templates = Jinja2Templates(directory='project/users/templates')

HTMX_STATUS_CHECK = """
    <div hx-ext="ws" id="message" ws-connect="/ws/task_status/{task_id}">
        <p id="status" hx-swap="outerHTML"></p>
    </div>
    <button type="submit" class="btn btn-primary" id="submit-btn" hx-swap-oob="true" disabled>
        Processing...
    </button>
"""


def api_call(email: str):
    # used for testing a failed api call
    if random.choice([0, 1]):
        raise Exception('random processing error')

    # used for simulating a call to a third-party api
    requests.post('https://httpbin.org/delay/5')


@users_router.get('/form/')
def form_example_get(request: Request):
    return templates.TemplateResponse('form.html', {'request': request})


@users_router.post('/form/')
# async def form_example_post(user_body: UserBody):
async def form_example_post(request: Request):
    import json

    from .tasks import sample_task

    user_body = await request.body()
    user_data = json.loads(user_body.decode())
    task = sample_task.delay(user_data['email'])

    return HTMLResponse(HTMX_STATUS_CHECK.format(task_id=task.task_id))


@users_router.get('/task_status/')
def task_status(task_id: str):
    task: AsyncResult = AsyncResult(task_id)
    state = task.state

    if state == states.FAILURE:
        error = str(task.result)
        response = {
            'state': state,
            'error': error,
        }
    else:
        response = {
            'state': state,
        }

    return JSONResponse(response)


@users_router.post('/webhook_test/')
def webhook_test():
    # if not random.choice([0, 1]):
    #     # mimic an error
    #     raise Exception()

    # blocking process
    response = requests.post('https://httpbin.org/delay/5')

    return response.json()


@users_router.post('/webhook_test_async/')
def webhook_test_async():
    from .tasks import task_process_notification

    task = task_process_notification.delay()
    print(task.id)
    return 'pong'


@users_router.get('/form_ws/')
def form_ws_example(request: Request):
    return templates.TemplateResponse('form_ws.html', {'request': request})


@users_router.get('/form_socketio/')
def form_socketio_example(request: Request):
    return templates.TemplateResponse('form_socketio.html', {'request': request})


@users_router.get('/form_htmx/')
def form_htmx_example(request: Request):
    return templates.TemplateResponse('form_htmx.html', {'request': request})
