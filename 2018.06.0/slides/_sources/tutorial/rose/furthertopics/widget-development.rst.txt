.. _widget-dev:

Widget Development
==================


The :ref:`command-rose-config-edit` GUI displays configurations using built-in
widgets. For more complex requirements :ref:`command-rose-config-edit` supports
custom widgets as plugins.

In this tutorial we will write a custom widget which offers typing suggestions
when entering usernames.

.. image:: img/rose-edit-custom-widget.png
   :align: center
   :width: 450px

.. warning::

   If you find yourself needing to write a custom widget, please contact the
   Rose team for guidance.

Example
-------

Create a new Rose app by running the following command replacing
``DIRECTORY`` with the path in which to create the suite:

.. code-block:: sub

   rose tutorial widget <DIRECTORY>
   cd <DIRECTORY>

You will now have a Rose app which contains the following files:

.. code-block:: sub

   <DIRECTORY>/
   |-- meta/
   |   `-- lib/
   |       `-- python/
   |           `-- widget/
   |               |-- __init__.py
   |               `-- username.py
   `-- rose-app.conf

The :rose:file:`rose-app.conf` file defines an environment variable called
``USER``:

.. code-block:: rose

   [env]
   USER=fred

.. _python package: https://docs.python.org/3/tutorial/modules.html#packages

The ``__init__.py`` file is empty - the presence of this file declares the
``widget`` directory as a `python package`_.

The ``username.py`` file is where we will write our widget.

Initial Code
^^^^^^^^^^^^

We will start with a slimmed-down copy of the class
:py:class:`rose.config_editor.valuewidget.text.RawValueWidget` which you will
find in the file ``username.py``. It contains all the API calls you would
normally ever need.

We are now going to extend the widget to be more useful.

Add a line importing the ``pwd`` package at the top of the file:

.. code-block:: diff

   + import pwd

    import gobject
    import pygtk
    pygtk.require('2.0')
    import gtk

This adds the Python library that we'll use in a minute.

Now we need to create a predictive text model by adding some data to our
``gtk.Entry`` text widget.

We need to write our method ``_set_completion``, and put it in the main body
of the class. This will retrieve usernames from the ``pwd.getpwall()``
function and store them so they can be used by the text widget ``self.entry``.

Add the following method to the ``UsernameValueWidget`` class:

.. code-block:: python

   def _set_completion(self):
       # Return a predictive text model.
       completion = gtk.EntryCompletion()
       model = gtk.ListStore(str)
       for username in [p.pw_name for p in pwd.getpwall()]:
           model.append([username])
       completion.set_model(model)
       completion.set_text_column(0)
       completion.set_inline_completion(True)
       self.entry.set_completion(completion)

We need to make sure this method gets called at the right time, so we add
the following line to the ``__init__`` method:

.. code-block:: diff

     self.entry.show()
   + gobject.idle_add(self._set_completion)
     self.pack_start(self.entry, expand=True, fill=True,
                     padding=0)

We could just call ``self._set_completion()`` there, but this would hang the
config editor while the database is retrieved.

Instead, we've told GTK to fetch the predictive text model when it's next idle
(``gobject.idle_add``). This means it will be run after it finishes loading
the page, and will be more-or-less invisible to the user. This is a better
way to launch something that may take a second or two. If it took any longer,
we'd probably want to use a separate process.

Referencing the Widget
^^^^^^^^^^^^^^^^^^^^^^

Now we need to refer to it in the metadata to make use of it.

Create the file ``meta/rose-meta.conf`` and paste the following configuration
into it:

.. code-block:: rose

   [env=USER]
   widget[rose-config-edit]=username.UsernameValueWidget

This means that we've set our widget up for the option ``USER``
under the section :guilabel:`env`. It will now be used as the widget for this
variable's value.

Results
^^^^^^^

Try opening up the config editor in the application directory (where the
:rose:file:`rose-app.conf` is) by running::

   rose config-edit

Navigate to the :guilabel:`env` page. You should see your widget on
the page! As you type, it should provide helpful
auto-completion of usernames. Try typing your own username.

Further Reading
---------------

.. _PYGTK: http://www.pygtk.org/

For more information, see :ref:`api-gtk` and the `PyGTK`_ web page.
