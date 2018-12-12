# antares_client
A light-weight client for receiving alerts from [ANTARES](http://antares.noao.edu).

ANTARES is an Alert Broker developed by the [NOAO](http://noao.edu) for ZTF and LSST.

ANTARES uses Apache Kafka to stream out alerts. This client allows you to subscribe to a Kafka topic and save all alerts to a directory.

## Install

```bash
pip install -r requirements.txt
```

Print help:

```bash
python antares_client.py -h
```

## Configure

Contact the ANTARES team to request API credentials.

In `antares_client.py`, set `ANTARES_KAFKA_API_KEY` and `ANTARES_KAFKA_API_SECRET` accordingly. If you prefer, you may specify these at runtime using `--api_key` and `--api_secret`.

## Subscribe to a stream

Subscribe to stream `test` and save all alerts to directory `./out/`:

```bash
python antares_client.py test --output_dir out --verbose
```

If you get a Kafka error about _`Failed to verify broker certificate: unable to get local issuer certificate`_, see section [Troubleshooting](#Troubleshooting) below.

You can also subscribe to multiple topics:

```bash
python antares_client.py topic1,topic2,topic3 --output_dir out
```

### A note about Consumer Groups

Each connection to Kafka declares membership to a Consumer Group. Kafka keeps track of each group's position (cursor) in each topic, and will not deliver the same message more than once. Therefore, if you stop the script and restart it, it will pick up where it left off.

## Process alerts

If you want to run your own code on alerts in real-time, add your code to the empty function `process_alert(alert)` in `antares_client.py`. Each alert will be a Python dict/list datastructure of the same schema as the output json files. Inspect the json files in `example_data/` for examples.

## Troubleshooting

### "Failed to verify broker certificate"

The confluent_kafka library needs to verify the certificate of the server. If it fails to find your local root certificate authority certificates, it will print an error like: _`Failed to verify broker certificate: unable to get local issuer certificate`_.

To fix this, first locate your root CA certificates file, which is usually called `certs.pem` or `ca-certificates.crt`.

If you are using anaconda or miniconda, it may be something like `.../miniconda/ssl/cert.pem`.

Once you have located the file, place its full path in variable `SSL_CA_LOCATION` near the top of `antares_client.py`. You may also specify it on the command line with `--ssl_ca_location /path/to/cert/file`.
