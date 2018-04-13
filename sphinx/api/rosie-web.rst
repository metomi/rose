.. _RESTful: https://en.wikipedia.org/wiki/Representational_state_transfer
.. _RDBMS: https://en.wikipedia.org/wiki/Relational_database_management_system
.. _JSON: http://www.json.org/


Rosie Web API
=============

This section explains how to use the Rosie web service API. All Rosie
discovery services (e.g. ``rosie search``, ``rosie go``, web page) use a
`RESTful`_ API to interrogate a web server, which then interrogates an
`RDBMS`_. Returned data is encoded in the `JSON`_ format.


Location
--------

The URLs to access the web API of a Rosie web service (with a given prefix
name) can be found in your Rose site configuration file as the value of
``[rosie-id]prefix-ws.PREFIX_NAME``. To access the API for a given repository
with prefix ``PREFIX_NAME``, you must select a format (the only currently
supported format is JSON) and use a url that looks like:

.. code-block:: sub

   http://host/<PREFIX_NAME>/get_known_keys?format=json


REST API
--------

.. http:get:: (str:prefix)/get_known_keys

   Return the main property names stored for suites (e.g. ``idx``, ``branch``,
   ``owner``) plus any additional names specified in the site config.

   :arg str prefix: Repository prefix.
   :param string format: Desired return format (``json`` or ``None``).

   Example Request
      .. code-block:: http

         GET http://host/my_prefix/get_known/keys?format=json HTTP/1.1

   Example Response
      .. code-block:: json

         ["access-list", "idx", "branch", "owner", "project", "revision", "status",  "title"]


.. http:get:: (str:prefix)/get_optional_keys

   Return all unique optional or user-defined property names given in suite
   discovery information.

   :arg str prefix: Repository prefix.
   :param string format: Desired return format (``json`` or ``None``).

   Example Request
      .. code-block:: http
         
         GET http://host/my_prefix/get_optional_keys?format=json HTTP/1.1

   Example Response
      .. code-block:: json

         ["access-list", "description", "endgame_status", "operational_flag", "tag-list"]


.. http:get:: (str:prefix)/get_query_operators

   Returns all the SQL-like operators used to compare column values that you
   may use in :http:get:`(str:prefix)/query` (e.g. ``eq``, ``ne``, ``contains``, ``like``).
   
   :arg str prefix: Repository prefix.
   :param string format: Desired return format (``json`` or ``None``).

   Example Request
      .. code-block:: http

         GET http://host/my_prefix/get_query_operators?format=json HTTP/1.1

   Example Response
      .. code-block:: json

         ["eq", "ge", "gt", "le", "lt", "ne", "contains", "endswith", "ilike", "like", "match", "startswith"]


.. http:get:: (str:prefix)/query

   Return a list of suites matching all search terms.

   :arg str prefix: Repository prefix.
   :param list query: List of queries.
   :param string format: Desired return format (``json`` or ``None``).
   :param flag all_revs: Switch on searching older revisions of current suites
      and deleted suites.

   :queryparameter str CONJUNCTION: ``and`` or ``or``\ .
   :queryparameter str OPEN_GROUP: optional, one or more ``(``\ .
   :queryparameter str FIELD: e.g. ``idx`` or ``description``\ .
   :queryparameter str OPERATOR: e.g. ``contains`` or ``between``, one of
      the operators returned by :http:get:`(str:prefix)/get_query_operators`.
   :queryparameter str VALUE: e.g. ``euro4m`` or ``200``\ .
   :queryparameter str CLOSE_GROUP: optional, one or more ``)``\ .

   Query Format
      .. code-block:: none

         CONJUNCTION+[OPEN_GROUP+]FIELD+OPERATOR+VALUE[+CLOSE_GROUP]

      The first ``CONJUNCTION`` is technically superfluous. The ``OPEN_GROUP``
      and ``CLOSE_GROUP`` do not have to be used.

      Parentheses can be used in the query to group expressions.

   Example Request
      Return all current suites that have an ``idx`` that ends with 78 and also
      all suites that have the owner ``bob``.

      .. code-block:: http

         GET http://host/my_prefix/query?q=and+idx+endswith+78&q=or+owner+eq+bob&format=json HTTP/1.1

   Example Response
      Each suite is returned as an entry in a list - each entry is an
      associative array of property name-value pairs.

      .. code-block:: json

         [{"idx": "mo1-aa078", "branch": "trunk", "revision": 200, "owner": "fred",
           "project": "fred's project.", "title": "fred's awesome suite",
           "status": "M ", "access-list": ["fred", "jack"], "description": "awesome"},
          {"idx": "mo1-aa090", "branch": "trunk", "revision": 350, "owner": "bob",
           "project": "var", "title": "A copy of var.vexcs.", "status": "M ",
           "access-list": ["*"], "operational": "Y"}]


.. http:get:: (str:prefix)/search

   Return a list of suites matching one or more search terms.

   :arg str prefix: Repository prefix.
   :param list search: List of queries in the same format as
      :http:get:`(str:prefix)/query`
   :param string format: Desired return format (``json`` or ``None``).
   :param flag all_revs: Switch on searching older revisions of current suites
      and deleted suites.

   Example Request
      Return suites which match ``var``, ``bob`` or ``nowcast``.

      .. code-block:: http

         GET http://host/my_prefix/search?var+bob+nowcast&format=json HTTP/1.1

   Example Response
      .. code-block:: json

         [{"idx": "mo1-aa090", "branch": "trunk", "revision": 330, "owner": "bob",
           "project": "um", "title": "A copy of um.alpra.", "status": "M ",
           "description": "Bob's UM suite"},
          {"idx": "mo1-aa092", "branch": "trunk", "revision": 340, "owner": "jim",
           "project": "var", "title": "6D Quantum VAR.", "status": "M ",
           "location": "NAE"},
          {"idx": "mo1-aa100", "branch": "trunk", "revision": 352, "owner": "ops_account",
           "project": "nowcast", "title": "The operational Nowcast suite",
           "status": "M ", "ensemble": "yes"}]


Python API
----------

The REST API maps onto the Python :py:class:`RosieWSClient` back-end which can be
used as a standalone Python API.

.. autoclass:: rosie.ws_client.RosieWSClient
   :members:
