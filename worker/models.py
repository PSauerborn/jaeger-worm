"""module containing data models used by module"""

import logging
import json
import uuid
from typing import Any, List, Dict
from datetime import datetime

from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)


class SpanTag(BaseModel):
    """Data class containing fields for a jaeger span"""
    key: str
    value_type: str
    value: Any

    class Config:
        fields = {
            'value_type': 'type'
        }

class JaegerProcess(BaseModel):
    """Data class containing fields for a jaeger process"""
    service_name: str
    tags: List[SpanTag]

    class Config:
        fields = {
            'service_name': 'serviceName'
        }

class JaegerSpan(BaseModel):
    """Data class containing fields to encapsulate a
    jaeger span"""
    trace_id: str
    span_id: str
    flags: int
    operation_name: str
    references: List
    start_time: datetime
    duration: int
    tags: List[SpanTag]
    logs: List
    process_id: str
    warnings: Any

    class Config:
        fields = {
            'operation_name': 'operationName',
            'start_time': 'startTime',
            'trace_id': 'traceID',
            'span_id': 'spanID',
            'process_id': 'processID'
        }

class JaegerTrace(BaseModel):
    """Data class containing fields needed for a
    complete jaeger trace"""
    trace_id: str
    spans: List[JaegerSpan]
    processes: Dict[str, JaegerProcess]
    warnings: Any

    class Config:
        fields = {
            'trace_id': 'traceID'
        }


if __name__ == '__main__':

    with open('./trace.json', 'r') as f:
        payload = json.load(f)

    trace = JaegerTrace(**payload)

    print(trace)