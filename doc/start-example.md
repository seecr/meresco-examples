Example server
==============

![Meresco](https://seecr.nl/img/meresco/meresco-logo-small.png)

The Meresco example server can be started if all dependencies are installed.

Overview
--------

The example server is constructed out of 4 services:

* Gateway service, will accept sru update requests from e.g. Meresco Harvester

* API service, provides a.o. an SRU output for queries.

* Index service, provides access to a Lucene Service, indexes data and handles internal queries.

* Lucene service, providen by Meresco Lucene package is an HTTP frontend for a Lucene index.

How to start
------------

* Lucene service: `start-lucene-server --port 9300 --stateDir /data/lucene-state --core oai_dc`

* Gateway service: `start-gateway --port 9000 --stateDir /data/gateway-state`

* Index service: `start-index --port 9100 --serverPort 9300 --gatewayPort 9000 --stateDir /data/index-state`

* API service: `start-api --port 8000 --indexPort 9100 --gatewayPort 9000 --stateDir /data/api-state`
