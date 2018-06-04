try:
    import pygtk
    pygtk.require('2.0')
    import gtk
except (ImportError, RuntimeError, AssertionError):
    INTERACTIVE_ENABLED = False
else:
    INTERACTIVE_ENABLED = True
