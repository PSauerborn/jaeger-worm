"""module containing worker process that analysis worker data"""

import logging
import time
from datetime import datetime, timedelta

from config import WORKER_INTERVAL_MINUTES
from jaeger import get_traces, analyse_traces
from persistence import get_service_list, insert_service_analysis

LOGGER = logging.getLogger(__name__)


def analyse_jaeger_data():
    """Target function used to analyse jaeger data
    on interval"""
    # get list of services from postgres database
    services = get_service_list()
    if services is None:
        LOGGER.error('unable to retrieve services from postgres')
        return
    # iterate over services and extrace spans
    for service in services:
        service_name = service.get('service_name')
        LOGGER.info('analysing spans for service %s', service)
        # analyse traces for service and store in database
        results = analyse_traces(service_name, get_traces(service_name, '1h'))
        insert_service_analysis(service_name, results)

    return results

def get_sleep_time(start: datetime, delta) -> int:
    """Function used to determine sleep
    interval"""
    now, finished = datetime.utcnow(), start + delta
    if now < finished:
        return (finished - now).seconds
    return None

def timer(handler_func: object, interval_minutes: int, fail_on_error: bool = False):
    """Timer function used to execute command
    on time interval"""
    while True:
        LOGGER.info('executing handler function')
        start = datetime.utcnow()
        # execute handler function and evaluate sleep time
        try:
            handler_func()
        except Exception as err:
            LOGGER.exception('unable to execute target func')
            if fail_on_error:
                raise

        if (sleep_time := get_sleep_time(start, timedelta(minutes=interval_minutes))) is not None:
            LOGGER.info('sleeping for %s seconds', sleep_time)
            time.sleep(sleep_time)
        else:
            LOGGER.warning('function execution exceeded sleep time. executing again')


if __name__ == '__main__':

    timer(analyse_jaeger_data, WORKER_INTERVAL_MINUTES)