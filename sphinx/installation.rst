.. include:: hyperlinks.rst
   :start-line: 1

Installation
============

.. _GitHub: https://github.com/metomi/rose
.. _archives: https://github.com/metomi/rose/tags

The source code for Rose is available via `GitHub`_, code
releases are available in ``zip`` and ``tar.gz`` `archives`_.

1. Un-pack the archive file into an appropriate location on your system.
2. Add the ``rose/bin/`` directory into your ``PATH`` environment variable.
3. Check system compatibility by running :ref:`command-rose-check-software`.


System Requirements
-------------------

Rose runs on Unix/Linux systems and is known to run on RHEL6 and a number of
systems including those documented under `metomi-vms`_.

System compatibility can be tested using the :ref:`command-rose-check-software`
command.

.. script-include:: rose check-software --rst


Host Requirements
-----------------

Whilst you can install and use Rose & Cylc on a single host (i.e. machine),
most installations are likely to be more complex. There are five types of
installation:

Hosts For Running Cylc Suites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each user can just run their suites on the host where they issue the
:ref:`command-rose-suite-run` command. However, the local host may not meet the
necessary requirements for connectivity (to the hosts running the tasks)
or for availability (the host needs to remain up for the duration of
the suite). Therefore, Rose can be configured to run the suites on
remote hosts. If multiple hosts are available, by default the host with
the lowest system load average will be used.

Installation requirements:
   * Rose, Cylc, Bash, Python, jinja2.
   * Subversion & FCM *(only if you want* :ref:`command-rose-suite-run` *to
     install files from Subversion using FCM keywords).*
Connectivity requirements:
   * Must be able to submit tasks to the hosts which run the suite tasks,
     either directly or via SSH access to another host.

Hosts For Running Tasks In Suites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installation requirements:
   * Rose, Cylc, Bash, Python.
   * Subversion & FCM *only if you want to use the Rose install utility
     to install files from Subversion using FCM keywords*.

Connectivity requirements:
   * Must be able to communicate back to the hosts running the Cylc suites
     via HTTPS (preferred), HTTP or SSH.

Hosts For Running User Interactive Tools
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installation requirements:
   * Rose, Cylc, Bash, Python, requests, Subversion, FCM,
     Pygraphviz (+ graphviz), PyGTK (+ GTK).

Connectivity requirements:
   * Must have HTTP access to the hosts running the Rosie web service.
   * Must have access to the Rosie Subversion repositories via the
     appropriate protocol.
   * Must have HTTP and SSH access to the hosts running the Cylc suites.
   * Must share user accounts and ``$HOME`` directories with the hosts running
     the Cylc suites.

Hosts For Running Rose Bush
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installation requirements:
   * Rose, Bash, Python, cherrypy, jinja2.

Connectivity requirements:
   * Must be able to access the home directories of users' Cylc run directories.

Hosts For Rosie Subversion Repositories And The Rosie Web Services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Typically you will only need a single host but you can have multiple
repositories on different hosts if you require this.

Installation requirements:
   * Rose, Bash, Python, cherrypy, jinja2, sqlalchemy, Subversion.

.. note::

   This section has assumed that you wish to use Rose & Cylc (including
   their respective GUIs) and use Rosie to store your suites. However,
   there are many ways of using Rose. For instance:

   * You can use Rose without using cylc.
   * You can use Rose & Cylc but not use Rosie.
   * You can use Rose & Cylc from the command line without using their GUIs.


Configuring Rose
----------------

``lib/bash/rose_init_site``
   If you do not have root access to install the required Python libraries,
   you may need to edit this file to ensure Python libraries are included
   in the ``PYTHONPATH`` environment variable. For example, if you have
   installed some essential Python libraries in your ``HOME`` directory,
   you can add a ``lib/bash/rose_init_site`` file with the following
   contents:

   .. code-block:: bash

      # Essential Python libraries installed under
      # "/home/daisy/usr/lib/python2.6/site-packages/"
      if [[ -n "${PYTHONPATH:-}" ]]; then
          PYTHONPATH="/home/daisy/usr/lib/python2.6/site-packages:${PYTHONPATH}"
      else
          PYTHONPATH="/home/daisy/usr/lib/python2.6/site-packages"
      fi
      export PYTHONPATH

``etc/rose.conf``
   You should add/edit this file to meet the requirement of your site.
   Examples can be found at the ``etc/rose.conf.example`` file in your
   Rose distribution. See also :rose:file:`rose.conf` in the API reference.


Configuring Rosie Client
------------------------

Rosie is an optional suite storage and discovery system.

Rosie stores suites using Subversion repositories, with databases behind
a web interface for suite discovery and lookup.

If users at your site are able to access Rosie services on the Internet
or if someone else has already configured Rosie services at your site,
all you need to do is configure the client to talk to the servers.
Refer to the `Configuring a Rosie Server`_ section if you need to
configure a Rosie server for your site.

To set up the Rosie client for the site, add/modify the
:rose:conf:`rose.conf[rosie-id]` E.g.:

.. code-block:: rose

   [rosie-id]
   prefix-default=x
   prefixes-ws-default=x myorg

   prefix-location.x=https://somehost.on.the.internet/svn/roses-x
   prefix-web.x=https://somehost.on.the.internet/trac/roses-x/intertrac/source:
   prefix-ws.x=https://somehost.on.the.internet/rosie/x

   prefix-location.myorg=svn://myhost.myorg/roses-myorg
   prefix-web.myorg=http://myhost.myorg/trac/roses-myorg/intertrac/source:
   prefix-ws.myorg=http://myhost.myorg/rosie/myorg

Check the following:

1. You can access the Rosie Subversion repository without being prompted
   for a username and a password. This may require configuring Subversion
   to cache your authentication information with a keyring.
   
   *(See Subversion Book > Advanced Topics > Network Model > Client
   Credentials for a discussion on how to do this.)*

2. The Rosie web service is up and running and you can access the Rosie
   web service from your computer. E.g. if the Rosie web service is
   hosted at ``https://somehost.on.the.internet/rosie/x``, you can check
   that you have access by typing the following on the command line::
   
      curl -I https://somehost.on.the.internet/rosie/x
      
   It should return a HTTP code 200. If you are prompted for a username
   and a password, you may need to have access to a keyring to cache
   the authentication information.

3. You can access the Rosie web service using the Rosie client. E.g.
   using the above configuration for the prefix ``x``, type the
   following on the command line::
   
      rosie hello --prefix=x
      
   It should return a greeting, e.g. ``Hello user``.


Deploying Configuration Metadata
--------------------------------

You may want to deploy :ref:`conf-meta` for projects using Rose
in a globally readable location at your site, so that they can be
easily accessed by users when using Rose utilities such as
:ref:`command-rose-config-edit` or :ref:`command-rose-macro`.

If the source tree of a project is version controlled under a
trusted Subversion repository, it is possible to automatically deploy
their configuration metadata. Assuming that the projects follow our
recommendation and store Rose configuration metadata under the
``rose-meta/`` directory of their source tree, you can:

* Check out a working copy for each sub-directory under the
  ``rose-meta/`` directory.
* Set up a crontab job to regularly update the working copies.

For example, suppose you want to deploy Rose :ref:`Metadata`
under ``/etc/rose-meta/`` at your site. You can do::

   # Deployment location
   DEST='/etc/rose-meta'
   cd "${DEST}"

   # Assume only Rose metadata configuration directories under "rose-meta/"
   URL1='https://somehost/foo/main/trunk/rose-meta'
   URL2='https://anotherhost/bar/main/trunk/rose-meta'
   # ...

   # Checkout a working copy for each metadata configuration directory
   for URL in "${URL1}" "${URL2}"; do
     for NAME in $(svn ls "${URL}"); do
         svn checkout -q "${URL}/${NAME}"
     done
   done

   # Set up a crontab job to update the working copies, e.g. every 10 minutes
   crontab -l || true >'crontab.tmp'
   {
     echo '# Update Rose configuration metadata every 10 minutes'
     echo "*/10 * * * * svn update -q ${DEST}/*"
   } >>'crontab.tmp'
   crontab 'crontab.tmp'
   rm 'crontab.tmp'

   # Finally add the root level "meta-path" setting to site's "rose.conf"
   # E.g. if Rose is installed under "/opt/rose/":
   {
     echo '[]'
     echo "meta-path=${DEST}"
   } >>'/opt/rose/etc/rose.conf'

.. tip::
   See also :ref:`app-meta-loc`.


Configuring Rose Bush
---------------------

Rose Bush provides an intranet web service at your site for users to
view their suite logs using a web browser. Depending on settings at
your site, you may or may not be able to set up this service.

You can start an ad-hoc Rose Bush web server by running::

   setsid /path/to/rose/bin/rose bush start 0</dev/null 1>/dev/null 2>&1 &

You will find the access and error logs under ``~/.metomi/rose-bush*``.

Alternatively you can run the Rose Bush web service under Apache
``mod_wsgi``. To do this you will need to set up an Apache module
configuration file (typically in ``/etc/httpd/conf.d/rose-wsgi.conf``)
containing the following (with the paths set appropriately)::

   WSGIPythonPath /path/to/rose/lib/python
   WSGIScriptAlias /rose-bush /path/to/rose/lib/python/rose/bush.py

Use the Apache log at e.g. ``/var/log/httpd/`` to debug problems.
See also `Configuring a Rosie Server`_.


Configuring a Rosie Server
--------------------------

You should only need to configure and run your own Rosie service if you do
not have access to Rosie services on the Internet, or if you need a
private Rosie service for your site. Depending on settings at your
site, you may or may not be able to set up this service.

You will need to select a machine to host the Subversion repositories.
This machine will also host the web server and databases.

.. _Subversion FSFS: https://en.wikipedia.org/wiki/Apache_Subversion#FSFS

Login to your host, create one or more `Subversion FSFS`_ repositories.

If you want to use FCM for your version control, you should set a
special property on the repository to allow branching and merging
with FCM in the Rosie convention. For example, if your repository
is served from ``HOST_AND_PATH`` (e.g. ``myhost001/svn-repos``) with
given repository base name ``NAME`` (e.g. ``roses_foo``), change into a
new directory and enter the following commands::

   svn co -q "svn://${HOST_AND_PATH}/${NAME}/"
   svn ps fcm:layout -F - "${NAME}" <<'__FCM_LAYOUT__'
   depth-project = 5
   depth-branch = 1
   depth-tag = 1
   dir-trunk = trunk
   dir-branch =
   dir-tag =
   level-owner-branch =
   level-owner-tag =
   template-branch =
   template-tag =
   __FCM_LAYOUT__
   svn ci -m 'fcm:layout: defined.' "${NAME}"
   rm -fr "${NAME}"

Add the following hook scripts to the repository:

* pre-commit:

  .. code-block:: sub

     #!/bin/bash
     exec <path-to-rose>/sbin/rosa svn-pre-commit "$@"

* post-commit:

  .. code-block:: sub

      #!/bin/bash
      exec <path-to-rose>/sbin/rosa svn-post-commit "$@"

You should replace ``/path/to/rose/`` with the location of your Rose
installation.

Make sure the hook scripts are executable.

The ``rosa svn-post-commit`` command in the ``post-commit`` hook is used
to populate a database with the suite discovery information as suites
are committed to the repository. Edit the :rose:conf:`rose.conf[rosie-db]`
settings to point to your host machine and provide relevant
paths such as the location for your repository and database.

Once you have done that, create the Rosie database by running::

   /path/to/rose/sbin/rosa db-create

Make sure that the account that runs the repository hooks has read/write
access to the database and database directory.

You can test that everything is working using the built-in web server.
Edit the :rose:conf:`rose.conf[rosie-disco]` settings to configure
the web server's log directory and port number. Start the web server
by running::

   setsid /path/to/rose/bin/rosie disco start 0</dev/null 1</dev/null 2>&1 &

Check that the server is up and running using ``curl`` or a local
web browser. E.g. If you have configured the server's port to be 1234,
you can do::

   curl -I http://localhost:1234/

It should return a HTTP code 200.

Alternatively you can run the Rosie web service under Apache ``mod_wsgi``.
To do this you will need to set up an Apache module configuration file
(typically in ``/etc/httpd/conf.d/rose-wsgi.conf``) containing the
following (with the paths set appropriately)::

   WSGIPythonPath /path/to/rose/lib/python
   WSGIScriptAlias /rosie /path/to/rose/lib/python/rosie/ws.py

Use the Apache log at e.g. ``/var/log/httpd/`` to debug problems.
See also `Configuring Rose Bush`_.

Hopefully, you should now have a working Rosie service server. Configure
the client settings by editing the :rose:conf:`rose.conf[rosie-id]`
settings. If you are using the built-in web server, you
should ensure that you include the port number in the URL. E.g.:

.. code-block:: rose

   [rosie-id]
   prefix-ws.foo=http://127.0.0.1:1234/foo

You should now be able to talk to the Rosie web service server via
the Rosie web service client. Test by doing::

   rosie hello

To test that everything is connecting together, create your first
suite in the repository by doing::

   rosie create

which will create the first suite in your repository, with an ID
ending in ``aa000`` - e.g. ``foo-aa000``. Locate it by running::

   rosie lookup 000

``ROSIE`` special suite
^^^^^^^^^^^^^^^^^^^^^^^

You can define a special suite in each Rosie repository that provides
some additional repository-specific data and metadata. The suite
ID will end with ``ROSIE`` - e.g. ``foo-ROSIE``.

This can be created by running ``rosie create --meta-suite``.

Creating a Known Keys File
^^^^^^^^^^^^^^^^^^^^^^^^^^

You can extend the list of search keys used in the Rosie discovery
interfaces (such as ``rosie go``). Create a text file at the root
of a Rosie suite working copy called ``rosie-keys``.

Add a space-delimited list of search keys into the file - for example:

.. code-block:: none

   sub-project experiment model

Run ``fcm add -c`` and ``fcm commit``. After the commit, these will be
added to the list of Rosie interface search keys.

You can continue to modify the list by changing the file contents and
committing.
