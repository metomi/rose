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

from io import StringIO

import gi
import pytest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from metomi.rose.config import ConfigNode, dump, load
from metomi.rose.config_editor.valuewidget import ValueWidgetHook
from metomi.rose.config_editor.valuewidget.array.mixed import (
    MixedArrayValueWidget,
)
from metomi.rose.config_editor.valuewidget.array.row import RowArrayValueWidget
from metomi.rose.variable import array_join, array_split


if not Gtk.init_check()[0]:
    pytest.skip("Headed testing required", allow_module_level=True)


@pytest.fixture(params=[
    (MixedArrayValueWidget, False),
    (MixedArrayValueWidget, True),
    (RowArrayValueWidget, False),
], ids=["mixed", "mixed-titles", "row"])
def make_widget(request):
    widget_class, titles = request.param
    widgets = []

    def create(value="", types=None, length=":"):
        if types is None:
            types = ["quoted"] * 3
        metadata = {
            "id": "template variables=FIELDS",
            "type": types,
            "length": length,
        }
        if titles:
            metadata["element-titles"] = ["A", "B", "C"]
        updates = []
        widget = widget_class(
            value, metadata, updates.append, ValueWidgetHook()
        )
        widgets.append(widget)
        return widget, updates

    yield create
    for widget in widgets:
        widget.destroy()


@pytest.mark.parametrize("column", range(3))
def test_partial_quoted_row_persists(make_widget, column):
    widget, updates = make_widget()
    widget.setter(column, '"field"')
    expected = ['""', '""', '""']
    expected[column] = '"field"'
    assert array_split(widget.value) == expected
    assert updates == [array_join(expected)]


@pytest.mark.parametrize("column", range(3))
@pytest.mark.parametrize("types, defaults, edits", [
    (["character"] * 3, ["''"] * 3, ["'field'"] * 3),
    (["integer"] * 3, ["0"] * 3, ["7"] * 3),
    (["real"] * 3, ["0"] * 3, ["1.5"] * 3),
    (["boolean"] * 3, ["false"] * 3, ["true"] * 3),
    (["logical"] * 3, [".false."] * 3, [".true."] * 3),
    (["python_boolean"] * 3, [""] * 3, ["True"] * 3),
    (["raw"] * 3, [""] * 3, ["field"] * 3),
    (["quoted", "integer", "logical"], ['""', "0", ".false."],
     ['"field"', "7", ".true."]),
])
def test_untouched_columns_persist(
    make_widget, column, types, defaults, edits
):
    widget, updates = make_widget(types=types)
    widget.setter(column, edits[column])
    expected = defaults.copy()
    expected[column] = edits[column]
    assert array_split(widget.value) == expected
    assert updates == [array_join(expected)]


@pytest.mark.parametrize("types, edit, expected", [
    (["quoted"] * 3, '"field"', '"field","",""'),
    (["raw"] * 3, "field", "field,,"),
    (["quoted", "integer", "logical"], '"field"', '"field",0,.false.'),
])
def test_saved_partial_row_round_trip(make_widget, types, edit, expected):
    widget, updates = make_widget(types=types)
    widget.setter(0, edit)
    assert updates == [expected]
    config = ConfigNode()
    config.set(["template variables", "FIELDS"], updates[-1])
    stream = StringIO()
    dump(config, stream)
    stream.seek(0)
    saved = load(stream).get_value(["template variables", "FIELDS"])
    restored, restored_updates = make_widget(saved, types=types)
    assert restored.value == expected
    assert restored.value_array == array_split(expected)
    assert restored_updates == []


# TODO: Comment out on main, as it requires fixes not on 2.8.x.
# def test_cell_signal_updates_model(make_widget):
#     widget, updates = make_widget()
#     child = widget.rows[-1][1]
#     child.entry.set_text("field")
#     child.setter()
#     assert updates == ['"","field",""']


def test_untouched_table_does_not_update(make_widget):
    widget, updates = make_widget()
    assert widget.value == ""
    assert updates == []


def test_edit_existing_row_preserves_neighbors(make_widget):
    widget, updates = make_widget('"first","","last"')
    widget.setter(1, '"middle"')
    assert updates == ['"first","middle","last"']


@pytest.mark.parametrize("types, initial, empty, expected", [
    (["quoted"] * 3, '"first","middle","last"', '""',
     '"first","","last"'),
    (["raw"] * 3, "first,middle,last", "", "first,,last"),
])
def test_clear_cell_persists(make_widget, types, initial, empty, expected):
    widget, updates = make_widget(initial, types=types)
    widget.setter(1, empty)
    assert updates == [expected]


def test_add_delete_and_reedit_row(make_widget):
    widget, updates = make_widget()
    widget.setter(1, '"first"')
    widget.add_row()
    widget.setter(5, '"discard"')
    widget.del_row()
    assert updates[-1] == '"","first",""'
    widget.add_row()
    widget.setter(3, '"second"')
    assert updates[-1] == '"","first","","second","first",""'


def test_multiple_rows_keep_column_positions(make_widget):
    widget, updates = make_widget(',,first,,,last', types=["raw"] * 3)
    widget.add_row()
    widget.setter(7, "middle")
    assert updates[-1] == ",,first,,,last,,middle,last"


def test_invalid_length_fallback_is_preserved(make_widget):
    widget, updates = make_widget('"only one"')
    assert widget.value == '"only one"'
    assert updates == []
    widget.setter(0, '"changed"')
    assert updates == ['"changed"']


def test_noncompound_row_behavior_is_preserved():
    updates = []
    widget = RowArrayValueWidget(
        "1,2",
        {"id": "env=NUMBERS", "type": "integer", "length": ":"},
        updates.append,
        ValueWidgetHook(),
    )
    try:
        widget.setter(0, "3")
        widget.add_element()
        assert updates == ["3,2", "3,2,0"]
    finally:
        widget.destroy()
