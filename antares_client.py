"""
Connect to ANTARES' Kafka cluster and read messages.
"""
from __future__ import print_function

import os
import sys
import datetime
import logging
import socket
import argparse
import zlib
import json

import confluent_kafka
from confluent_kafka.cimpl import KafkaError
import bson


# Kafka connection defaults.
ANTARES_KAFKA_HOST = 'pkc-epgnk.us-central1.gcp.confluent.cloud'
ANTARES_KAFKA_PORT = 9092
ANTARES_KAFKA_API_KEY = ''  # Set this value to your API Key
ANTARES_KAFKA_API_SECRET = ''  # Set this value to your API Secret


log = logging.Logger('antares_client')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel('INFO')


def main():
    # Load parameters
    args = load_args()

    # Process Alerts
    consumer = get_kafka_consumer(args)
    log.info('Connecting...')
    try:
        while True:
            msgs = consumer.consume(num_messages=10, timeout=1)
            for msg in msgs:
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        log.debug('End of stream {}-{}. Waiting...'
                                  .format(msg.topic(), msg.partition()))
                    else:
                        log.error(msg.error())
                    continue

                topic = msg.topic()
                alert = parse_antares_alert(msg.value())
                process_alert(alert)
                if args.output_dir:
                    file_path = save_alert(alert, args.output_dir, topic)
                    t = datetime.datetime.now().strftime('%H:%M:%S')
                    log.info('{} Saved alert {}'.format(t, file_path))
                else:
                    log.debug('Received alert on topic \'{}\''.format(topic))
    finally:
        consumer.close()


def process_alert(alert):
    """
    If you want to process Alerts as soon as they arrive, put your code here.
    """
    pass


def load_args():
    """
    Load command line arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('topic', type=str,
                        help='Name of Kafka topic to connect to.'
                             ' You may supply multiple topic names'
                             ' separated by commas, without spaces.')
    parser.add_argument('--host', type=str, default=ANTARES_KAFKA_HOST,
                        help='Hostname of Kafka cluster.')
    parser.add_argument('--port', type=int, default=ANTARES_KAFKA_PORT,
                        help='Port of Kafka cluster.')
    parser.add_argument('--api_key', type=str, default=ANTARES_KAFKA_API_KEY,
                        help='ANTARES Kafka API Key.')
    parser.add_argument('--api_secret', type=str, default=ANTARES_KAFKA_API_SECRET,
                        help='ANTARES Kafka API Secret.')
    parser.add_argument('-g', '--group', type=str, default=socket.gethostname(),
                        help='Globally unique name of consumer group.'
                             ' Defaults to your hostname.')
    parser.add_argument('-d', '--output_dir', type=str,
                        help='Directory to save Alerts in.')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    if args.verbose:
        log.setLevel('DEBUG')

    required = [('api_key', 'ANTARES_KAFKA_API_KEY'),
                ('api_secret', 'ANTARES_KAFKA_API_SECRET')]
    for arg, var in required:
        if not getattr(args, arg):
            log.error('You must provide --{}, or else set {} in {}.'
                      .format(arg, var, __file__))
            sys.exit(1)

    return args


def get_kafka_consumer(args):
    """
    Open a Kafka Consumer and subscribe to topic.
    """
    kafka_config = {
        'bootstrap.servers': '{}:{}'.format(args.host, args.port),
        'sasl.username': args.api_key,
        'sasl.password': args.api_secret,
        'group.id': args.group,

        'default.topic.config': {'auto.offset.reset': 'smallest'},
        'api.version.request': True,
        'broker.version.fallback': '0.10.0.0',
        'api.version.fallback.ms': 0,
        'sasl.mechanisms': 'PLAIN',
        'security.protocol': 'SASL_SSL',
    }
    consumer = confluent_kafka.Consumer(**kafka_config)
    topic = args.topic
    if ',' in topic:
        topics = topic.split(',')
    else:
        topics = [topic]
    consumer.subscribe(topics)
    return consumer


def parse_antares_alert(payload):
    """
    Convert an ANTARES Alert message to a Python object.

    ANTARES Alerts are outputted in GZIP-compressed BSON format.

    :param payload: byte array of message
    :return: dict
    """
    try:
        return bson.loads(zlib.decompress(payload))
    except Exception:
        log.error('Failed to parse message:')
        log.error(payload)
        raise


def save_alert(alert, directory, topic):
    """
    Save an Alert as a JSON file.

    Return path of the new file.
    """
    # Make output directory
    directory = os.path.join(directory, topic)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Write alert to file
    alert_id = alert['new_alert']['alert_id']
    file_name = '{}.json'.format(alert_id)
    file_path = os.path.join(directory, file_name)
    with open(file_path, 'w') as f:
        json.dump(alert, f, indent=4)

    return file_path


if __name__ == '__main__':
    main()
