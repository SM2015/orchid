from __future__ import absolute_import

from celery import shared_task
from actstream import action
import core.models as cm
import time

@shared_task
def experimental(numbers):
    print "experiment occuring"
    time.sleep(30)
    return True

@shared_task
def update_cache():
    print "updating cache"
    time.sleep(30)
    return True

import boto
import logging
logging.basicConfig()
from boto.elastictranscoder.exceptions import (
    InternalServiceException,
    LimitExceededException,
    ResourceInUseException,
)
from django.conf import settings