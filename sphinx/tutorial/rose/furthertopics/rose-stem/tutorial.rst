.. include:: ../../../../hyperlinks.rst
   :start-line: 1


.. _Rose Stem Tutorial:

Rose Stem Tutorial
==================

.. warning::

   Before proceeding you should already be familiar with the :ref:`Rose Stem`
   section.

.. image:: http://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Cassini_Saturn_Orbit_Insertion.jpg/320px-Cassini_Saturn_Orbit_Insertion.jpg
   :align: right
   :alt: Artist's Impression of Cassini entering Saturn orbit
   :width: 300px

This tutorial will walk you through creating a simple example of the
Rose Stem testing system which will involve piloting a spaceship
through space.


Getting Started
---------------

We will start the Rose Stem tutorial by setting up an `FCM`_ repository
called ``SPACESHIP`` to store the code and test suite in.

.. _keyword: https://metomi.github.io/fcm/doc/user_guide/code_management.html#svn_basic_keywords

Usually you would add a Rose Stem suite to an existing repository with
the `keyword`_ already set up to test the accompanying source code. For the
purposes of this tutorial we will create a new one.

Type the follow to create a temporary repository (you can safely delete
it after finishing this tutorial)::

   mkdir -p ~/rose-tutorial
   svnadmin create ~/rose-tutorial/spaceship_repos
   (cd $(mktemp -d); mkdir -p trunk/src; svn import -m "" . file://$HOME/rose-tutorial/spaceship_repos)

We then need to link the project name ``SPACESHIP`` with this project.
Creating the file and directory if they do not exist
add the following line to the file ``$HOME/.metomi/fcm/keyword.cfg``:

.. code-block:: rose

   location{primary}[spaceship] = file:///home/user/rose-tutorial/spaceship_repos

Make sure the path on the right-hand side matches the location you
specified in the ``svnadmin`` command.

Now you can checkout a working copy of your repository by typing::

   mkdir -p ~/rose-tutorial/spaceship_working_copy
   cd ~/rose-tutorial/spaceship_working_copy
   fcm checkout fcm:spaceship_tr .

Finally populate your working copy by running (answering ``y`` to the prompt)::

   rose tutorial rose-stem .


``spaceship_command.f90``
-------------------------

Our Fortran program is ``spaceship_command.f90``, which reads in an
initial position and spaceship mass from one namelist, and a series
of commands to apply thrust in three-dimensional space. It then uses
Newtonian mechanics to calculate a final position.

You will find it in the ``src`` directory. Have a look at it and see
what it does.


The ``spaceship`` app
---------------------

.. TODO - outline what this app does.

Create a new Rose app called ``spaceship``::

   mkdir -p rose-stem/app/spaceship

Paste the following configuration into a :rose:file:`rose-app.conf` file within
that directory:

.. code-block:: rose

   [command]
   default=spaceship_command.exe

   [file:spaceship.NL]
   source=namelist:spaceship

   [file:command.NL]
   source=namelist:command

   [namelist:spaceship]
   mass=2.0
   position=0.0,0.0,0.0

   [namelist:command]
   thrust(1,:) =  1.0,  0.0, 0.0, 1.0,  0.0, -1.0, -1.0, 0.0, 0.0,  0.0
   thrust(2,:) =  0.0, -2.0, 0.0, 1.0,  1.0,  0.5, -1.0, 1.5, 0.0, -1.0
   thrust(3,:) =  0.0,  1.0, 0.0, 1.0, -1.0,  1.0, -1.5, 0.0, 0.0, -0.5


The ``fcm-make`` app
--------------------

We now need to provide the instructions for :rose:app:`fcm_make` to build the
Fortran executable.

Create a new app called ``fcm_make_spaceship`` with an empty
:rose:file:`rose-app.conf` file.

Inside this app create a subdirectory called ``file`` and paste the following
into the ``fcm-make.cfg`` file within that directory:

.. code-block:: ini

   steps = build
   build.source = $SOURCE_SPACESHIP/src
   build.target{task} = link

The ``$SOURCE_SPACESHIP`` environment variable will be set using the
Jinja2 variable of the same name which is provided by Rose Stem.


The ``suite.rc`` file
---------------------

Next we will look at the ``rose-stem/suite.rc`` file.

The ``suite.rc`` file starts off with ``UTC mode = True``, which you
should already be :ref:`familiar with <tutorial-cylc-datetime-utc>`.
The next part is a Jinja2 block which links the group names the user
can specify with the :term:`graph <graph>` for that group. In this
case, the group ``command_spaceship`` gives you the graph:

.. digraph:: Example
   :align: center

   fcm_make_spaceship -> spaceship -> rose_ana_position

This variable ``name_graphs`` is used later to generate the graph when
the suite is run. The Jinja2 variable ``groups`` is next. This enables you
to set shortcuts to a list of groups, in this case specifying ``all`` on the
command line will run the tasks associated with both ``command_spaceship``
and ``fire_lasers``.

The scheduling section contains the Jinja2 code to use the information we
have already set to generate the graph based on what the user
requested on the command line.

The runtime section should be familiar. Note, however, that the
``fcm_make_spaceship`` task sets the environment variable
``SOURCE_SPACESHIP`` from the Jinja2 variable of the same name. This
is how the variables passed with ``--source`` on the command line are
passed to ``fcm-make``, which then uses these environment variables in
its own configuration files.


The ``rose-suite.conf`` file
----------------------------

The suites associated with Rose Stem require a version number
indicating the version of the ``rose stem`` command with which they
are compatible. This is specified in the :rose:file:`rose-suite.conf` file,
together with the default values of ``RUN_NAMES`` and ``SOURCE_SPACESHIP``.
Paste the following into your :rose:file:`rose-suite.conf` file:

.. code-block:: rose

   ROSE_STEM_VERSION=1

   [jinja2:suite.rc]
   RUN_NAMES=[]
   SOURCE_SPACESHIP='fcm:spaceship_tr@head'

Both of the Jinja2 variables will be overridden by the user when they
execute ``rose stem`` on the command line.


The ``rose_ana_position`` app
-----------------------------

The final component is a :rose:app:`rose_ana` app to test whether the position
of our spaceship matches the correct output.

Create an app named ``rose_ana_position`` and paste the following into its
:rose:file:`rose-app.conf` file.

.. code-block:: rose

   [ana:grepper.FilePattern(Check X position at each timestep)]
   pattern='^\s*Position:\s*(.*?)\s*,'
   files=/home/user/spaceship/kgo.txt
        =../spaceship/output.txt

   [ana:grepper.FilePattern(Check Y position at each timestep)]
   pattern='^\s*Position:.*?,\s*(.*?)\s*,'
   files=/home/user/spaceship/kgo.txt
        =../spaceship/output.txt

   [ana:grepper.FilePattern(Check Z position at each timestep)]
   pattern='^\s*Position:.*,\s*(.*)\s*$'
   files=/home/user/spaceship/kgo.txt
        =../spaceship/output.txt

This will check that the positions reported by the program match those
within the known good output file.


Known Good Output
-----------------

In the root of the working copy is a file called ``kgo.txt``.

The known good output should be the result of a control run. Rose Ana
will compare the answers from this file (obtained using the extract and
comparison methods in the :rose:file:`rose-app.conf` file) with the results
from the user's code change.

Replace the ``/home/user/spaceship`` paths in the ``rose_ana_position``
app with the path to this file.


Adding the suite to version control
-----------------------------------

Before running the suite we need to make sure that all the files and
directories we have created are known to the version control system.

Add all the new files you've created using ``fcm add -c`` *(answer yes
to the prompts)*.


Running the test suite
----------------------

We should now be able to run the test suite. Simply type::

   rose stem --group=command_spaceship

anywhere in your working copy (the ``--source`` argument defaults to ``.``
so it should automatically pick up your working copy as the source).

.. note::

   If your site uses a Cylc server, and your home directory is not shared
   with the Cylc server, you will need to add the option::

      --host=localhost

We use ``--group`` in preference to ``--task`` in this suite (both are
synonymous) as we specify a group of tasks set up in the Jinja2 variable
``name_graphs``.


A failing test
--------------

Now edit the file::

   rose-stem/app/spaceship/rose-app.conf

and change one of the thrusts, then rerun ``rose stem``. You will find the
``rose_ana_position`` task fails, as the results have changed.

.. TODO - Do we need to reset previous changes?!

Try modifying the Fortran source code - for example, changing the direction
in which thrust is applied (by changing the acceleration to be subtracted
from the velocity rather than added). Again, rerun ``rose stem``, and see
the failure.

In this way, you can monitor whether the behaviour of code is changed by
any of the code alterations you have made.


Further Exercises
-----------------

If you wish, you can try extending the suite to include the ``fire_lasers``
group of tasks which was in the list of groups in the ``suite.rc`` file.
Using the same technique as we've just demonstrated for piloting the
spaceship, you should be able to aim and fire the ship's weapons.


Automatic Options
-----------------

It is possible to automatically add options to ``rose stem`` using the
:rose:conf:`rose.conf[rose-stem]automatic-options` variable in the
:ref:`Site And User Configuration` file.
This takes the syntax of key-value pairs on a single
line, and is functionally equivalent to adding them using the ``-S``
option on the ``rose stem`` command line. For example:

.. code-block:: rose

   [rose-stem]
   automatic-options=GRAVITY=newtonian PLANET=jupiter

sets the variable ``GRAVITY`` to have the value ``newtonian``, and
``PLANET`` to be ``jupiter``. These can then be used in the ``suite.rc``
file as Jinja2 variables.
