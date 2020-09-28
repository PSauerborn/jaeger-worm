"""Module containing persistence functions used to connect
to postgres server"""

import logging
import uuid

from datetime import timedelta, datetime
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

from config import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

LOGGER = logging.getLogger(__name__)

@contextmanager
def persistence():
    """Function used to create postgres persistence
    connection. Persistence connections are returned
    as conext managers"""
    connection = None
    try:
        LOGGER.debug('connecting to postgres at %s:%s', POSTGRES_HOST, POSTGRES_PORT)
        connection = psycopg2.connect(f'host={POSTGRES_HOST} port={POSTGRES_PORT} '
                               f'dbname={POSTGRES_DB} user={POSTGRES_USER} '
                               f'password={POSTGRES_PASSWORD}')
        yield connection
    except Exception:
        LOGGER.exception('unable to connect to postgres server')
        raise
    finally:
        if connection is not None:
            connection.close()

def database_function(func: object):
    """Wrapper used to insert database connection
    and cursor into function call arguments"""
    def wrapper(*args: tuple, **kwargs: dict):
        with persistence() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            return func(conn, cursor, *args, **kwargs)
    return wrapper

@database_function
def get_service_list(conn: object, cursor: object):
    """Persistence function used to retrieve
    list of service names from database"""
    results = cursor.execute('SELECT service_name FROM services')
    return cursor.fetchall()

@database_function
def insert_service_analysis(conn: object, cursor: object, service_name: str, results: dict):
    """Persistence function used to retrieve
    list of service names from database"""
    args = (
        service_name, results['average_latency'], results['median_latency'],
        results['average_request_time_diff'], results['median_request_time_diff'],
        results['request_count']
    )

    cursor.execute(
        'INSERT INTO analysis_results(service_name,average_latency,median_latency,average_request_time_diff,median_request_time_diff,request_count) '
        'VALUES(%s,%s,%s,%s,%s,%s)', args
    )
    conn.commit()


