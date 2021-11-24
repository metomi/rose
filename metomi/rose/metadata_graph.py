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
"""Module to produce Graphviz graphing of Rose configuration metadata."""

import ast
from functools import cmp_to_key
import os
import sys
import tempfile

import metomi.rose.config
import metomi.rose.config_tree
import metomi.rose.external
import metomi.rose.macro
import metomi.rose.macros.trigger
import metomi.rose.opt_parse
import metomi.rose.reporter
import metomi.rose.resource

COLOUR_ENABLED = "green"
COLOUR_IGNORED = "red"
COLOUR_MISSING = "grey"
COLOUR_USER_IGNORED = "orange"

SHAPE_NODE_EXTERNAL = "rectangle"
SHAPE_NODE_SECTION = "octagon"

STATE_NORMAL = metomi.rose.config.ConfigNode.STATE_NORMAL

STYLE_ARROWHEAD_EMPTY = "empty"


def get_node_state_attrs(config, section, option=None, allowed_sections=None):
    """Get Graphviz node attributes like color for a given setting."""
    node_attrs = {}
    if option is None:
        node_attrs["shape"] = SHAPE_NODE_SECTION
    if not config.value.keys():
        # Empty configuration - we can assume pure metadata.
        return node_attrs
    if allowed_sections is None:
        allowed_sections = []
    config_section_node = config.get([section])
    id_ = metomi.rose.macro.get_id_from_section_option(section, option)
    state = ""
    config_node = config.get([section, option])
    node_attrs["color"] = COLOUR_IGNORED
    if (
        config_section_node is not None
        and config_section_node.state != STATE_NORMAL
        and option is not None
    ):
        state = metomi.rose.config.STATE_SECT_IGNORED
    if config_node is None:
        node_attrs["color"] = COLOUR_MISSING
    elif config_node.state != STATE_NORMAL:
        state += config_node.state
        if config_node.state == config_node.STATE_USER_IGNORED:
            node_attrs["color"] = COLOUR_USER_IGNORED
    elif not state:
        node_attrs["color"] = COLOUR_ENABLED
    if allowed_sections and section not in allowed_sections:
        node_attrs["shape"] = SHAPE_NODE_EXTERNAL
    if state:
        node_attrs["label"] = state + id_
    return node_attrs


def get_graph(
    config,
    meta_config,
    name,
    allowed_sections=None,
    allowed_properties=None,
    err_reporter=None,
):
    """Return a Graphviz graph object constructed from metadata properties."""
    import pygraphviz  # Graphviz and pygraphviz need to be installed.

    if allowed_sections is None:
        allowed_sections = []
    if allowed_properties is None:
        allowed_properties = []
    if err_reporter is None:
        err_reporter = metomi.rose.reporter.Reporter()
    graph = pygraphviz.AGraph(directed=True)
    graph.graph_attr["rankdir"] = "LR"
    graph.graph_attr["label"] = name
    if not allowed_properties or (
        allowed_properties and "trigger" in allowed_properties
    ):
        add_trigger_graph(
            graph,
            config,
            meta_config,
            err_reporter,
            allowed_sections=allowed_sections,
        )
    return graph


def add_trigger_graph(
    graph, config, meta_config, err_reporter, allowed_sections=None
):
    """Add trigger-related nodes and edges to the graph."""
    trigger = metomi.rose.macros.trigger.TriggerMacro()
    bad_reports = trigger.validate_dependencies(config, meta_config)
    if bad_reports:
        err_reporter(
            metomi.rose.macro.get_reports_as_text(
                bad_reports, "trigger.TriggerMacro"
            )
        )
        return None
    ids = []
    for keylist, node in meta_config.walk(no_ignore=True):
        id_ = keylist[0]
        if id_.startswith(
            metomi.rose.META_PROP_NS + metomi.rose.CONFIG_DELIMITER
        ) or id_.startswith(metomi.rose.SUB_CONFIG_FILE_DIR + ":*"):
            continue
        if isinstance(node.value, dict):
            section, option = metomi.rose.macro.get_section_option_from_id(id_)
            if not allowed_sections or (
                allowed_sections and section in allowed_sections
            ):
                ids.append(id_)
    ids.sort(key=cmp_to_key(metomi.rose.config.sort_settings))
    for id_ in ids:
        section, option = metomi.rose.macro.get_section_option_from_id(id_)
        node_attrs = get_node_state_attrs(
            config, section, option, allowed_sections=allowed_sections
        )
        graph.add_node(id_, **node_attrs)
    for setting_id, id_value_dict in sorted(
        trigger.trigger_family_lookup.items()
    ):
        section, option = metomi.rose.macro.get_section_option_from_id(
            setting_id
        )
        section_node = config.get([section], no_ignore=True)
        node = config.get([section, option])
        if node is None:
            setting_value = None
        else:
            setting_value = node.value
        setting_is_section_ignored = option is None and section_node is None
        for dependent_id, values in sorted(id_value_dict.items()):
            (
                dep_section,
                dep_option,
            ) = metomi.rose.macro.get_section_option_from_id(dependent_id)
            if allowed_sections and (
                section not in allowed_sections
                and dep_section not in allowed_sections
            ):
                continue
            if not values:
                values = [None]
            has_success = False
            if setting_value is not None:
                for value in values:
                    if value is None:
                        if (
                            node.state == node.STATE_NORMAL
                            and not setting_is_section_ignored
                        ):
                            has_success = True
                            break
                    elif trigger._check_values_ok(
                        setting_value, setting_id, [value]
                    ):
                        has_success = True
                        break
            for value in values:
                value_id = setting_id + "=" + str(value)
                dependent_attrs = {}
                if setting_value is None:
                    dependent_attrs["color"] = COLOUR_MISSING
                else:
                    dependent_attrs["color"] = COLOUR_IGNORED
                    if value is None:
                        if (
                            node.state == node.STATE_NORMAL
                            and not setting_is_section_ignored
                        ):
                            dependent_attrs["color"] = COLOUR_ENABLED
                    elif trigger._check_values_ok(
                        setting_value, setting_id, [value]
                    ):
                        dependent_attrs["color"] = COLOUR_ENABLED
                if not graph.has_node(setting_id):
                    node_attrs = get_node_state_attrs(
                        config,
                        section,
                        option,
                        allowed_sections=allowed_sections,
                    )
                    graph.add_node(setting_id, **node_attrs)
                if not graph.has_node(dependent_id):
                    node_attrs = get_node_state_attrs(
                        config,
                        dep_section,
                        dep_option,
                        allowed_sections=allowed_sections,
                    )
                    graph.add_node(dependent_id, **node_attrs)
                if not graph.has_node(value_id):
                    node_attrs = {
                        "style": "filled",
                        "label": value,
                        "shape": "box",
                    }
                    node_attrs.update(dependent_attrs)
                    graph.add_node(value_id, **node_attrs)
                edge_attrs = {}
                edge_attrs.update(dependent_attrs)
                if setting_value is not None:
                    edge_attrs["label"] = setting_value
                graph.add_edge(setting_id, value_id, **edge_attrs)
                if dependent_attrs["color"] == COLOUR_IGNORED and has_success:
                    dependent_attrs["arrowhead"] = STYLE_ARROWHEAD_EMPTY
                graph.add_edge(value_id, dependent_id, **dependent_attrs)


def output_graph(graph, debug_mode=False, filename=None, form="svg"):
    """Output a Graphviz Graph object.

    If debug_mode is True, print the 'dot' text output.
    Otherwise, save to a temporary file and launch in an image viewer.

    """
    if debug_mode:
        form = "dot"
    if filename is None:
        image_file_handle = tempfile.NamedTemporaryFile(suffix=("." + form))
    else:
        image_file_handle = open(filename, "wb")
    graph.draw(image_file_handle.name, prog="dot")
    if debug_mode:
        image_file_handle.seek(0)
        print(image_file_handle.read().decode())
        image_file_handle.close()
        return
    metomi.rose.external.launch_image_viewer(
        image_file_handle.name, run_fg=True
    )


def _exit_with_metadata_fail():
    """Handle a load metadata failure."""
    text = metomi.rose.macro.ERROR_LOAD_METADATA.format("")
    metomi.rose.reporter.Reporter()(
        text,
        kind=metomi.rose.reporter.Reporter.KIND_ERR,
        level=metomi.rose.reporter.Reporter.FAIL,
    )
    sys.exit(1)


def _load_override_config():
    conf = (
        metomi.rose.resource.ResourceLocator.default()
        .get_conf()
        .get(["rose-metadata-graph"])
    )
    if conf is None:
        return
    for key, node in conf.value.items():
        if node.is_ignored():
            continue
        try:
            cast_value = ast.literal_eval(node.value)
        except Exception:
            cast_value = node.value
        globals()[key.replace("-", "_").upper()] = cast_value


def main():
    """Run the metadata graphing from the command line."""
    _load_override_config()
    metomi.rose.macro.add_meta_paths()
    opt_parser = metomi.rose.opt_parse.RoseOptionParser(
        usage='rose metadata-graph [OPTIONS] [SECTION ...]',
        description='Graph configuration metadata.',
        epilog='''
ARGUMENTS
    SECTION
        One or more configuration sections to graph. If
        specified, only these sections will be checked.

ENVIRONMENT VARIABLES
    optional ROSE_META_PATH
        Prepend `$ROSE_META_PATH` to the metadata search path.
        ''',
    )
    opt_parser.add_my_options(
        "conf_dir",
        "meta_path",
        "output_dir",
        "property",
    )
    opt_parser.modify_option(
        'conf_dir',
        help=(
            'The directory containing either the configuration or'
            ' the configuration metadata.'
            '\nIf the configuration is'
            'given, the metadata will be looked up in the normal'
            'way (see also `--meta-path`, `ROSE_META_PATH`). If the'
            'configuration metadata is given, there will be no'
            'configuration data used in the graphing.'
            'If not specified, the current directory will be used.'
        ),
    )
    opt_parser.modify_option(
        'property',
        help=(
            'Graph a certain property e.g. `trigger`.'
            '\nIf specified, only this property will be graphed.'
        ),
    )
    opts, args = opt_parser.parse_args()
    if opts.conf_dir:
        os.chdir(opts.conf_dir)
    opts.conf_dir = os.getcwd()
    metomi.rose.macro.add_opt_meta_paths(opts.meta_path)

    config_file_path = os.path.join(opts.conf_dir, metomi.rose.SUB_CONFIG_NAME)
    meta_config_file_path = os.path.join(
        opts.conf_dir, metomi.rose.META_CONFIG_NAME
    )
    config_tree_loader = metomi.rose.config_tree.ConfigTreeLoader()
    if os.path.exists(config_file_path):
        config = config_tree_loader(
            opts.conf_dir, metomi.rose.SUB_CONFIG_NAME, conf_dir_paths=sys.path
        ).node
        meta_path = metomi.rose.macro.load_meta_path(config, opts.conf_dir)[0]
        if meta_path is None:
            _exit_with_metadata_fail()
        meta_config = metomi.rose.macro.load_meta_config(
            config,
            directory=opts.conf_dir,
        )
        if not meta_config.value.keys():
            _exit_with_metadata_fail()
    elif os.path.exists(meta_config_file_path):
        config = metomi.rose.config.ConfigNode()
        meta_config = (
            config_tree_loader(opts.conf_dir, metomi.rose.META_CONFIG_NAME)
        ).node
    else:
        _exit_with_metadata_fail()
    name = opts.conf_dir
    if args:
        name += ": " + ",".join(args)
    if opts.property:
        name += " (" + ",".join(opts.property) + ")"
    graph = get_graph(
        config,
        meta_config,
        name,
        allowed_sections=args,
        allowed_properties=opts.property,
    )
    if graph is None:
        _exit_with_metadata_fail()
    output_graph(graph, debug_mode=opts.debug_mode)


if __name__ == "__main__":
    main()
