"""
Connect to ANTARES' Kafka cluster and read messages.
"""
from __future__ import print_function

import os
import sys
import logging
import socket
import argparse
import zlib
import json

import confluent_kafka
import bson


# Kafka connection defaults.
ANTARES_KAFKA_HOST = 'pkc-epgnk.us-central1.gcp.confluent.cloud'
ANTARES_KAFKA_PORT = 9092
ANTARES_KAFKA_API_KEY = None  # Set this value to your API Key
ANTARES_KAFKA_API_SECRET = None  # Set this value to your API Secret


log = logging.Logger('antares_client')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel('INFO')


def main():
    # Load parameters
    args = load_args()
    log.info('Starting up with config:')
    log.info(args.__dict__)

    # Process Alerts
    consumer = get_kafka_consumer(args)
    try:
        while True:
            msgs = consumer.consume(num_messages=10, timeout=1)
            for msg in msgs:
                if msg.error():
                    if '_PARTITION_EOF' in str(msg.error()):
                        log.info('End of stream. Waiting for messages...')
                    else:
                        log.error(msg.error())
                    continue

                topic = msg.topic()
                alert = parse_antares_alert(msg.value())
                log.debug('Received alert on topic "{}"'.format(topic))
                if args.output_dir:
                    save_alert(alert, args.output_dir, topic)
    finally:
        consumer.close()


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
    parser.add_argument('--group', type=str, default=socket.gethostname(),
                        help='Globally unique name of consumer group.'
                             ' Defaults to your hostname.')
    parser.add_argument('--output_dir', type=str,
                        help='Directory to save Alerts in.')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    if args.verbose:
        log.setLevel('DEBUG')

    required = [('api_key', '--api_key', 'ANTARES_KAFKA_API_KEY'),
                ('api_secret', '--api_secret', 'ANTARES_KAFKA_API_SECRET')]
    for arg, flag, var in required:
        if not getattr(args, arg):
            log.error('You must provide {} or set {} in {}.'
                      .format(flag, var, __file__))
            sys.exit(1)

    return args


def get_kafka_consumer(args):
    """
    Open a Kafka Consumer and subscribe to topic.
    """
    kafka_config = {
        'bootstrap.servers': '{}:{}'.format(args.host, args.port),
        'default.topic.config': {'auto.offset.reset': 'smallest'},
        'group.id': args.group,
        'sasl.mechanisms': 'PLAIN',
        'security.protocol': 'SASL_SSL',
        'sasl.username': args.api_key,
        'sasl.password': args.api_secret,
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
    """
    # Make output directory
    directory = os.path.join(directory, topic)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Write alert to file
    alert_id = alert['new_alert']['alert_id']
    file_name = '{}.json'.format(alert_id)
    file_path = os.path.join(directory, file_name)
    log.debug('Writing file {}'.format(file_path))
    with open(file_path, 'w') as f:
        json.dump(alert, f, indent=4)


if __name__ == '__main__':
    main()
