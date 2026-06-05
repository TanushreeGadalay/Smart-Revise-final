from celery import Celery

celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Optional: Autodiscover or explicitly include
celery.conf.update(
    include=["tasks"]
)
