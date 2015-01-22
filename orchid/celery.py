from __future__ import absolute_import

import os

from celery import Celery

from django.conf import settings

#import core.tasks

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orchid.settings')

app = Celery('orchid')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.conf.update(
    CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'add-every-30-seconds': {
        'task': 'core.tasks.update_cache',
        'schedule': timedelta(seconds=5),
        'args': ()
    },
}

app.conf.update(CELERYBEAT_SCHEDULE=CELERYBEAT_SCHEDULE)

CELERY_TIMEZONE = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))