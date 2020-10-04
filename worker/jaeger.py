"""module containing functions used to extract data from jaeger service"""

import logging
from typing import Any, List

import requests
from pydantic import ValidationError
import numpy as np
from hermes import increment_counter

from models import JaegerTrace, JaegerSpan, JaegerProcess
from config import JAEGER_QUERY_URL

LOGGER = logging.getLogger(__name__)


def get_process_id(service_name: str, processes: List[JaegerProcess]) -> str:
    """Helper function used to retrieve process ID from
    list of processes"""
    for process_id, process in processes.items():
        if process.service_name == service_name:
            return process_id

def get_trace_timestamp(trace: JaegerTrace) -> int:
    """Function used to retrieve request timestamp
    from trace"""
    timestamps = []
    for span in trace.spans:
        timestamps.append(span.start_time)
    return min(timestamps).timestamp()

def aggregate_trace(service_name: str, trace: JaegerSpan):
    """Function used to analyse jaeger span"""
    increment_counter('traces_analysed', labels={'service': service_name})
    LOGGER.debug('analysing trace %s with %d span(s)', trace.trace_id, len(trace.spans))
    # retrieve correct process ID to filter out irrelevant spans
    process_id = get_process_id(service_name, trace.processes)
    if process_id is None:
        LOGGER.error('unable to retreive process ID from spans')
        return
    # filter out relevant spans
    return [span.duration for span in trace.spans if span.process_id == process_id]

def analyse_traces(service_name: str, traces: list):
    """Function used to analyse a collection of traces"""
    latencies, trace_timestamps = [], []
    for trace in traces:
        trace_timestamps.append(get_trace_timestamp(trace))
        latencies += aggregate_trace(service_name, trace)

    # sort timestamps in order and cast lists to arrays
    trace_timestamps = sorted(trace_timestamps)
    latencies, trace_timestamp_diffs = np.array(latencies), np.diff(np.array(trace_timestamps))

    # evaluate metrics for both request latencies and request timestamps
    average_latency, median_latency = latencies.mean(), np.median(latencies)
    average_time_diff, median_time_diff = trace_timestamp_diffs.mean(), np.median(trace_timestamp_diffs)
    LOGGER.debug('analysed service \'%s\' with average latency %s and median latency %s', service_name, average_latency, median_latency)

    return {
        'average_latency': average_latency,
        'median_latency': median_latency,
        'median_request_time_diff': abs(median_time_diff),
        'average_request_time_diff': abs(average_time_diff),
        'request_count': len(traces)
    }

def get_traces(service_name: str, since: str = '1h') -> List[JaegerTrace]:
    """Function used to retrieve list of jaeger spans from
    jaeger query API"""
    url = JAEGER_QUERY_URL + '/api/traces?service={}&since={}'.format(service_name, since)
    try:
        LOGGER.debug('retrieving jaeger traces for service %s since %s', service_name, since)
        response = requests.get(url)
        response.raise_for_status()

        payload = response.json().get('data', None)
        if payload is None:
            LOGGER.error('received invalid response from jaeger query %s', payload)
        else:
            return [JaegerTrace(**trace) for trace in payload]
    except requests.HTTPError:
        LOGGER.exception('unable to retrieve jaeger traces from jaeger query')

