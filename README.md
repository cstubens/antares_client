# antares_client
A light-weight client for receiving alerts from [ANTARES](http://antares.noao.edu).

ANTARES is an Alert Broker developed by the [NOAO](http://noao.edu) for ZTF and LSST.

ANTARES uses Apache Kafka to stream out alerts. This client allows you to subscribe to a Kafka topic and save all alerts to a directory.

## Install

Note: Python version 3.7 is reccomended. Older Python versions may work but are not tested.

With your Python environment set up, download `antares_client` and install the Python dependencies:

```bash
git clone git@github.com:cstubens/antares_client.git
cd antares_client
pip install -r requirements.txt
```

If all went well, you will now be able to view the help:

```bash
python antares_client.py -h
```

## Configure

Contact the ANTARES team to request API credentials. At this time we normally grant only one pair of credentials per institution. If approved, you will recieve a pair of credentials: your API Key and API Secret. Do not share these credentials with others. We request that you operate only one active consumer per set of credentials, except with the permission of the NOAO. The NOAO reserves the right to monitor your usage and revoke your credentials at any time.

Once you have your credentials, set `ANTARES_KAFKA_API_KEY` and `ANTARES_KAFKA_API_SECRET` in `antares_client.py` accordingly. If you prefer, you may specify these at runtime using `--api_key` and `--api_secret`.

## Subscribe to a stream

Subscribe to stream `test` and save all alerts to directory `./out/`:

```bash
python antares_client.py test --output_dir out --verbose
```

If you get an error _`Failed to locate openssl certs file`_, see section [Troubleshooting](#Troubleshooting) below.

You can also subscribe to multiple topics:

```bash
python antares_client.py topic1,topic2,topic3 --output_dir out
```

Note: The client will automatically reconnect to Kafka if it looses the connection. It is common for this to happen periodically. If it occurs, the client wil continue to operate normally but you will see messages like:

```
%3|1544735845.925|FAIL|rdkafka#consumer-1| [thrd:sasl_ssl://b0-pkc-epgnk.us-central1.gcp.confluent.cloud:9092/0]: sasl_ssl://b0-pkc-epgnk.us-central1.gcp.confluent.cloud:9092/0: Disconnected (after 600053ms in state UP)
```

### A note about Consumer Groups

Each connection to Kafka declares membership to a Consumer Group. Kafka keeps track of each group's position (cursor) in each topic, and will not deliver the same message more than once. Therefore, if you stop the script and restart it, it will pick up where it left off.

## Process alerts

If you want to run your own code on alerts in real-time, add your code to the empty function `process_alert(alert)` in `antares_client.py`. Each alert will be a Python dict/list datastructure of the same schema as the output json files. Inspect the json files in `example_data/` for examples.

## Troubleshooting

### "Failed to locate openssl certs file"

The confluent_kafka library needs to verify the certificate of the server. If it fails to find your local root certificate authority certificates, an error _`Failed to locate openssl certs file`_ will be printed.

To fix this, first locate your root CA certificates file, which is usually called `certs.pem` or `ca-certificates.crt`.

The following command will tell you where `openssl` is configured to look for certificates. Look in that directory for your cert file.

```bash
openssl version -d
```

If you are using anaconda or miniconda, it may be something like `.../miniconda/ssl/cert.pem`.

Once you have located the file, place its full path in variable `SSL_CA_LOCATION` near the top of `antares_client.py`. You may also specify it on the command line with `--ssl_ca_location /path/to/cert/file`.
