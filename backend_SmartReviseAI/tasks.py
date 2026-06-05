from celery_app import celery
from ml.logic import generate_content

@celery.task
def generate_revision(topic):
    return generate_content(topic)
