rose stem
=========

Introduction
------------

.. image:: http://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Cassini_Saturn_Orbit_Insertion.jpg/320px-Cassini_Saturn_Orbit_Insertion.jpg
   :align: right
   :alt: Artist's Impression of Cassini entering Saturn orbit
   :width: 300px

This advanced tutorial will walk you through creating a simple example of the
``rose stem`` testing system. Our tutorial will involve you commanding a
spaceship flying through space.

You should already be familiar with the ``rose stem`` part of the
documentation.


Getting started
---------------

We will start the ``rose stem`` tutorial by setting up an FCM repository
called ``SPACESHIP`` to store the code and test suite in.

Usually you would add a ``rose stem`` suite to an existing repository with
the keyword already set up to test the accompanying source code. For the
purposes of this tutorial we will create a new one.

Type the follow to create a temporary repository (you can safely delete
it after finishing this tutorial)::

   svnadmin create ~/spaceship_repos
   (cd $(mktemp -d); mkdir -p trunk/src; svn import -m "" . file://$HOME/spaceship_repos)

We then need to link the project name ``SPACESHIP`` with this project. Edit
the file::

   $HOME/.metomi/fcm/keyword.cfg

and add the line:

.. code-block:: rose

   location{primary}[spaceship] = file:///home/user/spaceship_repos

making sure the path on the right-hand side matches the location you
specified in the ``svnadmin`` command.

Now you can checkout a working copy of your repository by typing::

   mkdir ~/spaceship_working_copy
   cd ~/spaceship_working_copy
   fcm checkout fcm:spaceship_tr .

``spaceship_command.f90``
-------------------------

Our Fortran program is ``spaceship_command.f90``, which reads in an
initial position and spaceship mass from one namelist, and a series
of commands to apply thrust in three-dimensional space. It then uses
Newtonian mechanics to calculate a final position.

Create a file called ``src/spaceship_command.f90`` with this content.
Have a look at it and see what it does.


Creating the test suite
-----------------------

We now need to create the test suite. In the top-level directory of your
working copy, create a directory named ``rose-stem``, along side the
``src`` directory which you've just put the Fortran program in.

Inside your ``rose-stem`` directory create empty ``rose-suite.conf`` and
``suite.rc`` files. We will fill these in later.

Next, create an ``app`` sub-directory inside your ``rose-stem`` directory,
and inside there create a directory named spaceship.


The ``spaceship`` app
---------------------

Open the file::

   app/spaceship/rose-app.conf

in a text editor, and paste in the following configuration:

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

We now need to provide the instructions for ``fcm make`` to build the
Fortran executable. Create an ``app/fcm_make_spaceship`` directory with
an empty ``rose-app.conf`` file.

Then, inside ``app/fcm_make_spaceship``, create a sub-directory named file
with the file ``fcm-make.cfg`` inside. Put the following contents in that
file:

.. code-block:: ini

   steps = build
   build.source = $SOURCE_SPACESHIP/src
   build.target{task} = link

The ``$SOURCE_SPACESHIP`` environment variable will be set using the
Jinja2 variable of the same name which is provided by ``rose stem``.


The ``suite.rc`` file
---------------------

We're now in a position to create the ``suite.rc`` file for the test
suite. Copy and paste the contents of ``suite.rc`` into your ``suite.rc``
file.

We will now take a few moments to examine this file and see how it works.

The ``suite.rc`` file starts off with ``UTC mode = True``, which you
should already be familiar with. The next part is a Jinja2 block which
links the group names the user can specific with the
:term:`dependency graph <graph>` for that group. In this case, the group
``command_spaceship`` gives you the dependency graph:

.. code-block:: cylc-graph

   fcm_make_spaceship => spaceship => rose_ana_position

This variable ``name_graphs`` is used later to work out the scheduling graph
at runtime. The Jinja2 variable groups is next. This enables you to set
shortcuts to a list of groups, in this case specifying all on the
command line will run the tasks associated with both ``command_spaceship``
and ``fire_lasers``.

The scheduling section contains the Jinja2 code to use the information we
have already set to generate the dependency graph based on what the user
requested on the command line.

The runtime section should be familiar. Note, however, that the
``fcm_make_spaceship`` task sets the environment variable
``SOURCE_SPACESHIP`` from the Jinja2 variable of the same name. This
is how the variables passed with ``--source`` on the command line ar
passed to ``fcm-make``, which then uses these environment variables in
its own configuration files.


The ``rose-suite.conf`` file
----------------------------

The suites associated with ``rose-stem`` require a version number
indicating the version of the ``rose stem`` command with which they
are compatible. This is specified in the ``rose-suite.conf`` file,
together with the default values of ``RUN_NAMES`` and ``SOURCE_SPACESHIP``.
Paste the following into your ``rose-suite.conf`` file:

.. code-block:: rose

   ROSE_STEM_VERSION=1

   [jinja2:suite.rc]
   RUN_NAMES=[]
   SOURCE_SPACESHIP='fcm:spaceship_tr@head'

Both of the Jinja2 variables will be overriden by the user when they
execute ``rose stem`` on the command line.


The ``rose_ana_position`` app
-----------------------------

The final component is a ``rose ana`` app to test the position of our
spaceship matches the correct output.

Create an app named ``rose_ana_position`` and paste the contents of the
following slide into the ``rose-app.conf`` file:

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

Now create a file named ``kgo.txt`` with these contents. Replace the
``/home/user/spaceship`` path in the files variable list with the path to
this file.

The known good output should be the result of a control run. ``rose ana``
will compare the answers from this file (obtained using the extract and
comparison methods in the ``rose-app.conf`` file) with the results from
the user's code change.


Adding the suite to version control
-----------------------------------

Before running the suite we need to make sure that all the files and
directories we have created are known to the version control system.

Add all the new files you've created using ``fcm add -c``.


Running the test suite
----------------------

We should now be able to run the test suite. Simply type::

   rose stem --group=command_spaceship

anywhere in your working copy (the ``--source`` argument defaults to.
so it should automatically pick up your working copy as the source). If
your site uses a cylc server, and your home directory is not shared
with the cylc server, you will need to add the option::

   --host=localhost

We use ``--group`` in preference to ``--task`` in this suite (both are
synonymous) as we specify a group of tasks set up in the Jinja2 variable
``name_graphs``.


A failing test
--------------

Now edit the file::

   rose-stem/app/spaceship/rose-app.conf

and change one of the thrusts, then rerun ``rose stem``. You will find the
``rose ana`` task fails, as the results have changed.

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

It is possible to automatically add options to ``rose-stem`` using the
automatic-options variable in a section named ``[rose-stem]`` in the site
``rose.conf`` file. This takes the syntax of key-value pairs on a single
line, and is functionally equivalent to adding them using the ``-S``
option on the ``rose-stem`` command line. For example:

.. code-block:: rose

   [rose-stem]
   automatic-options=GRAVITY=newtonian PLANET=jupiter

sets the variable ``GRAVITY`` to have the value ``newtonian``, and
``PLANET`` to be ``jupiter``. These can then be used in the ``suite.rc``
file as Jinja2 variables.
