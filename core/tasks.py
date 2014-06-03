from __future__ import absolute_import

from celery import shared_task
from actstream import action
import core.models as cm

@shared_task
def experimental(numbers):
    print "experiment occuring"
    raise experimental.retry(countdown=10)
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