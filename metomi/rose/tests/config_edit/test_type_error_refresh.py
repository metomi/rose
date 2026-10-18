# Copyright (C) British Crown (Met Office) & Contributors.
# This file is part of Rose, a framework for meteorological suites.
#
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
"""Regression tests for the config editor type error refresh decision.

When the validation state ('type' error) of a variable flips, a variable
widget must be refreshed in place if its value widget can handle type
errors (e.g. the 'quoted' and 'character' widgets). Otherwise the whole
widget must be re-created. Getting this the wrong way around destroys the
widget holding the focus, so the GUI loses focus and jumps to the top of
the page (https://github.com/metomi/rose/issues/3115).

The tests drive the real refresh decision logic without building any
windows, so they can run headless.
"""

import sys
import types


try:
    import gi  # noqa: F401
except ImportError:
    # PyGObject is not installed (e.g. plain Windows host). Stub it out so
    # the config editor modules can be imported. The tests never build
    # windows or widgets, they only exercise refresh decision logic.
    class _StubMeta(type):
        """Class attribute access creates enum-like stand-ins."""

        def __call__(cls, *args, **kwargs):
            return _StubObject(cls.__name__)

        def __getattr__(cls, name):
            if name.startswith('__') and name.endswith('__'):
                raise AttributeError(name)
            kid = _StubMeta(cls.__name__ + '.' + name, (object,), {})
            setattr(cls, name, kid)
            return kid

    class _StubObject:
        """Stand-in instance for stubbed GTK objects."""

        def __init__(self, name=''):
            object.__setattr__(self, '_name', name)

        def __getattr__(self, name):
            if name.startswith('__') and name.endswith('__'):
                raise AttributeError(name)
            return _StubObject(self._name + '.' + name)

        def __call__(self, *args, **kwargs):
            return _StubObject(self._name + '()')

        def __iter__(self):
            return iter([])

        def __and__(self, other):
            return 1

        __rand__ = __and__

        def __truediv__(self, other):
            return 0.0

        __rtruediv__ = __truediv__

        def __mul__(self, other):
            return 0

        __rmul__ = __mul__

        def __add__(self, other):
            return 0

        __radd__ = __add__

        def __sub__(self, other):
            return 0

        __rsub__ = __sub__

        def __int__(self):
            return 0

        def __float__(self):
            return 0.0

        def __eq__(self, other):
            return self is other

        def __hash__(self):
            return id(self)

    class _StubRepoType(types.ModuleType):
        """Module type whose missing names become stub classes."""

        def __getattr__(self, name):
            if name.startswith('__'):
                raise AttributeError(name)
            value = _StubMeta(
                'gi.repository.' + name, (object,), {}
            )
            setattr(self, name, value)
            return value

    def _install_stub_gi():
        if 'gi' in sys.modules:
            return
        repo = types.ModuleType('gi.repository')
        repo.__class__ = _StubRepoType
        gi_mod = types.ModuleType('gi')
        gi_mod.require_version = lambda *args, **kwargs: None
        gi_mod.repository = repo
        sys.modules['gi'] = gi_mod
        sys.modules['gi.repository'] = repo

    _install_stub_gi()


from metomi.rose import META_PROP_TYPE  # noqa: E402
from metomi.rose.config_editor import page as rose_page  # noqa: E402
from metomi.rose.config_editor import variable as rose_variable  # noqa: E402


class _RecorderContainer:
    """Stand-in page container recording widget re-creations."""

    def __init__(self):
        self.added = []
        self.reloaded = []
        self.removed = []

    def add_variable_widget(self, variable):
        self.added.append(variable)

    def reload_variable_widget(self, variable):
        self.reloaded.append(variable)

    def remove_variable_widget(self, variable):
        self.removed.append(variable)


class _RecorderMenu:
    """Stand-in menu/key widget recording refreshes."""

    def __init__(self):
        self.refreshed = []

    def refresh(self, variable=None):
        self.refreshed.append(variable)


class _FakeValueWidget:
    """Value widget stand-in exercising the style refresh code paths."""

    def __init__(self):
        self.colour_badges = []

    def get_children(self):
        return []

    def get_sensitive(self):
        return 1

    def modify_base(self, state, colour):
        self.colour_badges.append((state, colour))

    def override_color(self, *args):
        pass

    def get_style_context(self):
        return types.SimpleNamespace(
            get_color=lambda *args: types.SimpleNamespace(
                red=0, green=0, blue=0
            )
        )


class _FakeHandlerValueWidget(_FakeValueWidget):
    """Value widget that can handle type errors (quoted/like)."""

    def __init__(self):
        super().__init__()
        self.handled = []

    def handle_type_error(self, has_error):
        self.handled.append(has_error)


def _make_variable(error=None):
    """A variable stand-in for the refresh decision logic."""
    return types.SimpleNamespace(
        metadata={'id': 'demo', 'name': 'demo'},
        error=dict(error or {}),
    )


def _make_variable_widget(valuewidget, error_keys, old_variable):
    """A VariableWidget instance built without building GTK widgets."""
    widget = rose_variable.VariableWidget.__new__(
        rose_variable.VariableWidget
    )
    widget.valuewidget = valuewidget
    widget.errors = list(error_keys)
    widget.variable = old_variable
    widget.is_ghost = False
    widget.bad_colour = 'bad-colour'
    widget.menuwidget = _RecorderMenu()
    widget.keywidget = _RecorderMenu()
    return widget


def _make_page(panel_variable, widget):
    """A ConfigPage instance with the parts used by refresh()."""
    page = rose_page.ConfigPage.__new__(rose_page.ConfigPage)
    page.panel_data = [panel_variable]
    page.ghost_data = []
    page.get_main_variable_widgets = lambda: [widget]
    page.main_container = _RecorderContainer()
    page.update_ignored = lambda *args, **kwargs: None

    def no_full_remake(*args, **kwargs):
        raise AssertionError('unexpected full page remake')

    page.sort_main = no_full_remake
    return page


def test_widget_with_type_error_handler_is_refreshed_in_place():
    """A quoted/character widget must not be re-created on type error."""
    old_variable = _make_variable({META_PROP_TYPE: 'some error'})
    new_variable = _make_variable()
    valuewidget = _FakeHandlerValueWidget()
    widget = _make_variable_widget(
        valuewidget, [META_PROP_TYPE], old_variable
    )
    page = _make_page(new_variable, widget)
    page.refresh(new_variable.metadata['id'])
    # The refreshed variable goes to the key and menu widgets, which are
    # not destroyed or re-created during the in-place refresh.
    assert widget.menuwidget.refreshed == [new_variable]
    assert widget.keywidget.refreshed == [new_variable]
    # The page container never re-created the widget.
    assert page.main_container.reloaded == []


def test_in_place_refresh_calls_handle_type_error():
    """The in-place refresh calls handle_type_error on the widget."""
    validity_moves = (
        # Valid -> invalid:
        (True, {}, {META_PROP_TYPE: 'some error'}),
        # Invalid -> valid:
        (False, {META_PROP_TYPE: 'some error'}, {}),
    )
    for goes_bad, old_error, new_error in validity_moves:
        old_variable = _make_variable(old_error)
        new_variable = _make_variable(new_error)
        valuewidget = _FakeHandlerValueWidget()
        widget = _make_variable_widget(
            valuewidget, list(old_error), old_variable
        )
        page = _make_page(new_variable, widget)
        page.refresh(new_variable.metadata['id'])
        assert valuewidget.handled == [goes_bad]


def test_widget_without_type_error_handler_is_recreated():
    """Widgets that cannot handle type errors must be re-created."""
    old_variable = _make_variable({META_PROP_TYPE: 'some error'})
    new_variable = _make_variable()
    valuewidget = _FakeValueWidget()
    widget = _make_variable_widget(
        valuewidget, [META_PROP_TYPE], old_variable
    )
    page = _make_page(new_variable, widget)
    page.refresh(new_variable.metadata['id'])
    assert page.main_container.reloaded == [new_variable]


def test_needs_type_error_refresh_matches_widget_capability():
    """needs_type_error_refresh: only widgets without a handler rebuild."""
    widget = rose_variable.VariableWidget.__new__(
        rose_variable.VariableWidget
    )
    widget.valuewidget = _FakeHandlerValueWidget()
    assert widget.needs_type_error_refresh() is False
    widget.valuewidget = _FakeValueWidget()
    assert widget.needs_type_error_refresh() is True
