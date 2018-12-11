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
python antares_client.py test --verbose --output_dir out
```
