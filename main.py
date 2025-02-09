from project import create_app

app = create_app()
celery = app.celery_app


@app.get('/health')
async def health_check():
    return {'status': 'healthy'}
