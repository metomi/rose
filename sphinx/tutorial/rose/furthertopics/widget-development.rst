Widget Development
==================


This tutorial walks you through using custom widget plugins to the Rose config
editor (``rose edit``).

These allow users to define their own bespoke widgets that can help improve
usability in specialised situations.

.. warning::

   If you find yourself needing to write a custom widget, please contact the
   Rose team for guidance.

Example
-------

This example uses the example suite from the brief tour and assumes you are
familiar with it. Change directory to your suite directory or recreate it if
has been deleted.

We are going to develop a value widget for the app ``fred_hello_world/``.
Change directory to ``app/fred_hello_world/``.

The metadata for the app lives under the ``meta/`` sub directory. Our new
widget will live with the metadata.

Create the directories ``meta/lib/python/widget/`` by running::

   mkdir -p meta/lib/python/widget

Create an empty file called ``__init__.py`` in the directory::

   touch meta/lib/python/widget/__init__.py

Create a file called ``username.py`` in the directory::

   touch meta/lib/python/widget/username.py

Initial Code
^^^^^^^^^^^^

Open ``username.py`` in a text editor and paste in this text.

This is a slimmed-down copy of the class
``rose.config_editor.valuewidget.text.RawValueWidget``. It contains all
the API calls you would normally ever need.

We are now going to extend the widget to be more useful.

Add the line:

.. code-block:: python

   import pwd

at the top of the file, so it looks like this:

.. code-block:: python

   import pwd

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

Add the following method to the class (append to the bottom of the file):

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
the line:

.. code-block:: python

           gobject.idle_add(self._set_completion)

in the ``__init__`` method as follows:

.. code-block:: python

           self.entry.show()
           self.pack_start(self.entry, expand=True, fill=True,
                           padding=0)

becomes

.. code-block:: python

           self.entry.show()
           gobject.idle_add(self._set_completion)
           self.pack_start(self.entry, expand=True, fill=True,
                           padding=0)

We could just call ``self._set_completion()`` there, but this would hang the
config editor while the database is retrieved.

Instead, we've told GTK to fetch the predictive text model when it's next idle
(``gobject.idle_add``). This means it will be run after it finishes loading
the page, and will be more-or-less invisible to the user. This is a better
way to launch something that may take a second or two. If it took any longer,
we'd probably want to use a separate process.

Code Summary
^^^^^^^^^^^^

Our file should now look like this.

Now we need to refer to it in the metadata to make use of it.

Referencing the Widget
^^^^^^^^^^^^^^^^^^^^^^

Open the file ``meta/rose-meta.conf`` in a text editor and add the lines:

.. code-block:: rose

   [env=HELLO_GREETER]
   widget[rose-config-edit]=username.UsernameValueWidget

This means that we've set our widget up for the option ``HELLO_GREETER``
under the section ``env``. It will now be used as the widget for this
variable's value.

Results
^^^^^^^

Try opening up the config editor in the application directory (where the
``rose-app.conf`` is) by typing::

   rose edit

at the command line. Navigate to the env page. You should see your widget on
the top right of the page! As you type, it should provide helpful
auto-completion of usernames. Try typing your own username.

Further Reading
---------------

For more information, see the Rose API reference and the PyGTK web page.

.. TODO - link me!
