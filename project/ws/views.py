import socketio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from socketio import AsyncNamespace

from project.celery_utils import get_task_info
from project.config import settings

from . import broadcast, ws_router


@ws_router.websocket('/ws/task_status/{task_id}')
async def ws_task_status(websocket: WebSocket):
    await websocket.accept()

    task_id = websocket.scope['path_params']['task_id']

    async with broadcast.subscribe(channel=task_id) as subscriber:
        async for event in subscriber:
            await websocket.send_text(event.message)


async def update_celery_task_status(task_id: str):
    """
    This function is called by Celery worker in task_postrun signal handler
    """
    data = get_task_info(task_id)
    state = data['state']
    print(f'SAVING STATE 2: {state}')
    await broadcast.connect()

    button = """
    <button type="submit" class="btn btn-primary" id="submit-btn" hx-swap-oob="true">
        Submit
    </button>
    """
    message = f'<p id="status">{state}</p>{button}'
    print(f'MESSAGE: {message}')
    await broadcast.publish(
        channel=task_id,
        message=message,  # RedisProtocol.publish expect str
    )
    await broadcast.disconnect()


class TaskStatusNameSpace(AsyncNamespace):
    async def on_join(self, sid, data):
        self.enter_room(sid=sid, room=data['task_id'])
        # just in case the task already finish
        await self.emit('status', get_task_info(data['task_id']), room=data['task_id'])

    async def on_connect(self, sid, data):
        print('CONNECTING')


def register_socketio_app(app: FastAPI) -> None:
    redis_manager = socketio.AsyncRedisManager(settings.WS_MESSAGE_QUEUE)
    # https://python-socketio.readthedocs.io/en/latest/server.html#uvicorn-daphne-and-other-asgi-servers
    # https://github.com/tiangolo/fastapi/issues/129#issuecomment-714636723
    sio = socketio.AsyncServer(
        cors_allowed_origins=['*'],
        async_mode='asgi',
        client_manager=redis_manager,
        logger=True,
        engineio_logger=True,
    )
    sio.register_namespace(TaskStatusNameSpace('/task_status'))
    asgi_app = socketio.ASGIApp(socketio_server=sio)

    app.mount('/ws', asgi_app)


def update_celery_task_status_socketio(task_id: str) -> None:
    """
    This function would be called in Celery worker
    https://python-socketio.readthedocs.io/en/latest/server.html#emitting-from-external-processes
    """
    # connect to the redis queue as an external process
    external_sio = socketio.RedisManager(settings.WS_MESSAGE_QUEUE, write_only=True)
    # emit an event
    external_sio.emit(
        'status',
        get_task_info(task_id),
        room=task_id,
        namespace='/task_status',
    )
