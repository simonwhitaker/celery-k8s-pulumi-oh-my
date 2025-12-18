import pulumi

from resources import celery_broker_url

pulumi.export("celery_broker_url", celery_broker_url)
