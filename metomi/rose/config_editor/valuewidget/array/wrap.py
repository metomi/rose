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

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk

# Right-hand allowance (px) for the value column's padding, so a widget sized
# to the available width does not overrun the viewport into a page scrollbar.
VALUE_RIGHT_MARGIN = 8

# Style class applied to a value widget's own scrollbar; see
# ensure_scrollbar_css.
ARRAY_SCROLLBAR_CLASS = "rose-array-scroll"
_SCROLLBAR_CSS_INSTALLED = False


def ensure_scrollbar_css():
    """Install, once, the CSS making array scrollbars thick and solid."""
    global _SCROLLBAR_CSS_INSTALLED
    if _SCROLLBAR_CSS_INSTALLED:
        return
    screen = Gdk.Screen.get_default()
    if screen is None:
        return
    provider = Gtk.CssProvider()
    css = b"""
.rose-array-scroll scrollbar slider {
    min-height: 8px;
    min-width: 8px;
    border-radius: 7px;
    background-color: rgba(128, 128, 128, 0.85);
}
.rose-array-scroll scrollbar slider:hover {
    background-color: rgba(90, 90, 90, 0.95);
}
"""
    try:
        provider.load_from_data(css)
    except Exception:
        return
    Gtk.StyleContext.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    _SCROLLBAR_CSS_INSTALLED = True


def visible_width(ref_widget):
    """Return the visible width available to ``ref_widget`` on its page.

    The scrolled viewport's width minus the widget's offset in content
    coordinates (the navigation panel and the variable name column) and a
    small right-hand margin for the value column's padding. Content
    coordinates keep this independent of any horizontal scroll position.
    """
    fallback = ref_widget.get_allocation().width
    scrolled = ref_widget.get_parent()
    while scrolled is not None and not isinstance(
        scrolled, Gtk.ScrolledWindow
    ):
        scrolled = scrolled.get_parent()
    if scrolled is None:
        return fallback
    viewport = scrolled.get_child()
    if viewport is None:
        return fallback
    content = viewport.get_child()
    if content is None:
        return fallback
    coords = ref_widget.translate_coordinates(content, 0, 0)
    if coords is None:
        return fallback
    width = viewport.get_allocation().width - coords[0] - VALUE_RIGHT_MARGIN
    return max(1, width)


class WrappingArrayTable(Gtk.Box):
    """Shared dynamic column wrapping for array value widgets.

    A single rule drives every array widget: fit as many equal-width columns
    as the visible value space allows, wrapping the remaining elements onto
    new rows, never fewer than one column.

    Hosts must provide:
      * ``self.entry_table`` - the homogeneous ``Gtk.Table`` of cells,
      * ``self.num_allowed_columns`` - the current column count,
      * ``self.populate_table()`` - (re)lay out the cells for that count.
    Hosts may override ``_get_cell_widgets`` if their grid cells are not
    ``self.entries + [self.button_box]``.
    """

    RESHAPE_DEBOUNCE_MS = 50

    def init_wrapping(self):
        """Wire up reshaping. Call once from the host's ``__init__``."""
        self._reshape_timer = None
        self._viewport = None
        self._viewport_handler = None
        self.entry_table.connect_after(
            "size-allocate", lambda w, e: self.reshape_table()
        )
        # The page scrolls horizontally, so the table's own size-allocate does
        # not fire on window resize; watch the scrolled viewport instead.
        self.connect("hierarchy-changed", self._connect_viewport_resize)
        self.connect("destroy", self._disconnect_viewport_resize)

    def _get_cell_widgets(self):
        """Return the widgets occupying the homogeneous grid cells."""
        return self.entries + [self.button_box]

    def reshape_table(self):
        """Set the column count to the most cells fitting the visible width."""
        widgets = self._get_cell_widgets()
        if not widgets:
            return False
        column_width = max(w.get_preferred_width()[1] for w in widgets)
        if column_width <= 0:
            return False
        available = self._get_available_width()
        columns = max(1, min(int(available / column_width), len(widgets)))
        if columns != self.num_allowed_columns:
            self.num_allowed_columns = columns
            self.populate_table()

    def _get_available_width(self):
        """Return the visible width the table can use without overflowing."""
        return visible_width(self.entry_table)

    def _connect_viewport_resize(self, widget, old_toplevel):
        """Recompute wrapping when the scrolled viewport (window) resizes."""
        if self._viewport is not None:
            return
        scrolled = self.entry_table.get_parent()
        while scrolled is not None and not isinstance(
            scrolled, Gtk.ScrolledWindow
        ):
            scrolled = scrolled.get_parent()
        if scrolled is None:
            return
        viewport = scrolled.get_child()
        if viewport is None:
            return
        self._viewport = viewport
        self._viewport_handler = viewport.connect(
            "size-allocate", self._queue_reshape
        )

    def _queue_reshape(self, widget, allocation):
        """Debounce rapid resize events into a single reshape."""
        if self._reshape_timer is not None:
            GLib.source_remove(self._reshape_timer)
        self._reshape_timer = GLib.timeout_add(
            self.RESHAPE_DEBOUNCE_MS, self._do_queued_reshape
        )

    def _do_queued_reshape(self):
        self._reshape_timer = None
        if self.entry_table.get_mapped():
            self.reshape_table()
        return False

    def _disconnect_viewport_resize(self, widget):
        if self._reshape_timer is not None:
            GLib.source_remove(self._reshape_timer)
            self._reshape_timer = None
        if self._viewport is not None and self._viewport_handler is not None:
            self._viewport.disconnect(self._viewport_handler)
        self._viewport = None
        self._viewport_handler = None


class EntryFit(Gtk.Box):
    """Size a single-line ``self.entry`` to min(content, visible width).

    When the text fits the visible value area the entry matches its length;
    when it is longer the entry fills the available width and scrolls its text
    internally, so it never forces the page wider than the window.

    Hosts must provide ``self.entry`` (a ``Gtk.Entry``) and call
    ``init_entry_fit()`` once it is packed.
    """

    FIT_DEBOUNCE_MS = 50

    def init_entry_fit(self):
        self._fit_timer = None
        self._fit_viewport = None
        self._fit_handler = None
        # A small width-chars keeps the minimum request low so the entry can
        # shrink; the real width is driven by fit_entry_width().
        self.entry.set_width_chars(1)
        self.entry.connect("changed", lambda w: self.fit_entry_width())
        self.entry.connect("map", lambda w: self.fit_entry_width())
        self.connect("hierarchy-changed", self._fit_connect_viewport)
        self.connect("destroy", self._fit_disconnect_viewport)

    def _entry_chrome(self):
        """Pixels the entry needs around its text (border, padding, cursor)."""
        ctx = self.entry.get_style_context()
        state = ctx.get_state()
        border = ctx.get_border(state)
        padding = ctx.get_padding(state)
        chrome = (
            border.left + border.right + padding.left + padding.right + 4
        )
        return max(chrome, 8)

    def fit_entry_width(self):
        """Resize the entry to the smaller of its text and visible width."""
        layout = self.entry.create_pango_layout(self.entry.get_text() or "")
        content = layout.get_pixel_size()[0] + self._entry_chrome()
        target = max(1, min(content, visible_width(self.entry)))
        if self.entry.get_size_request()[0] != target:
            self.entry.set_size_request(target, -1)

    def _fit_connect_viewport(self, widget, old_toplevel):
        if self._fit_viewport is not None:
            return
        scrolled = self.entry.get_parent()
        while scrolled is not None and not isinstance(
            scrolled, Gtk.ScrolledWindow
        ):
            scrolled = scrolled.get_parent()
        if scrolled is None:
            return
        viewport = scrolled.get_child()
        if viewport is None:
            return
        self._fit_viewport = viewport
        self._fit_handler = viewport.connect("size-allocate", self._fit_queue)

    def _fit_queue(self, widget, allocation):
        if self._fit_timer is not None:
            GLib.source_remove(self._fit_timer)
        self._fit_timer = GLib.timeout_add(
            self.FIT_DEBOUNCE_MS, self._fit_timeout
        )

    def _fit_timeout(self):
        self._fit_timer = None
        if self.entry.get_mapped():
            self.fit_entry_width()
        return False

    def _fit_disconnect_viewport(self, widget):
        if self._fit_timer is not None:
            GLib.source_remove(self._fit_timer)
            self._fit_timer = None
        if self._fit_viewport is not None and self._fit_handler is not None:
            self._fit_viewport.disconnect(self._fit_handler)
        self._fit_viewport = None
        self._fit_handler = None
