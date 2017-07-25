Admonitions
===========

Built-ins
---------

The following admonitions are rst/sphinx/rtd-theme built-ins.

.. attention::

   Some kind of warning

.. caution::

   Another kind of warning

.. danger::

   Yet another kind of warning

.. error::

   An error...

.. warning::

   A warning

.. hint::

   A usefull hint

.. tip::

   A usefull tip

.. important::

   Something important

.. note::

   Note: ...


The Practical Admonition
------------------------

To set practicals appart from the rest of the content I've added a
``..pratical::`` directive (ext/practical). At the moment it is a regular
admonition with the class ``note`` appended to it which causes the box to
appear in blue the same as the ``.. note::`` admonition - by centralising the
style/implementation can allways be changed later.

.. practical::

   My practical admonition...

   .. hint::

      The practical admonition can contain other RST elements.

   .. code-block:: bash

      Like this ...

