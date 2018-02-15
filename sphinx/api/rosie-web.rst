.. _RESTful: https://en.wikipedia.org/wiki/Representational_state_transfer
.. _RDBMS: https://en.wikipedia.org/wiki/Relational_database_management_system
.. _JSON: http://www.json.org/

Rosie Web
=========

This section explains how to use the Rosie web service API. All Rosie
discovery services (e.g. ``rosie search``, ``rosie go``, web page) use a
`RESTful`_ API to interrogate a web server, which then interrogates an
`RDBMS`_. Returned data is encoded in the `JSON`_ format.

You may wish to utilise the Python class ``rosie.ws_client.Client`` as an
alternative to this API.

Location
--------

The URLs to access the web API of a Rosie web service (with a given prefix
name) can be found in your rose site configuration file as the value of
``[rosie-id]prefix-ws.PREFIX_NAME``. To access the API for a given repository
with prefix ``PREFIX_NAME``, you must select a format (the only currently
supported format is 'json') and use a url that looks like:

.. code-block:: none

   http://host/PREFIX_NAME/get_known_keys?format=json

Usage
-----

.. TODO - complete/remove section as desired
