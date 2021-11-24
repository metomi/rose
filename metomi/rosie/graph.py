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
"""Plot suite ancestry."""

import textwrap
import time

import pygraphviz

import metomi.rose.metadata_graph
import metomi.rose.opt_parse
import metomi.rose.reporter
import metomi.rosie.suite_id
import metomi.rosie.ws_client
import metomi.rosie.ws_client_cli


class NoConnectionsEvent(metomi.rose.reporter.Event):
    """An event raised if the graph has no edges or nodes.

    event.args[0] is the filter id string.

    """

    KIND = metomi.rose.reporter.Reporter.KIND_ERR

    def __str__(self):
        return "%s: no copy relationships to other suites" % self.args[0]


class PrintSuiteDetails(metomi.rose.reporter.Event):
    """An event to print out suite details when writing to CLI"""

    KIND = metomi.rose.reporter.Reporter.KIND_OUT

    def __str__(self):
        template = " %s"
        argslist = [self.args[0]]
        if len(self.args) > 1:
            for arg in self.args[1]:
                template += ", %s"
                argslist.append(arg)
        return template % tuple(argslist)


def get_suite_data(prefix, properties=None):
    """Retrieve a dictionary containing the contents of RosieWS

    Adds in any extra requested properties

    """

    if properties is None:
        properties = []

    ws_client = metomi.rosie.ws_client.RosieWSClient(
        prefixes=[prefix], event_handler=metomi.rose.reporter.Reporter()
    )
    suite_data = ws_client.search(prefix, all_revs=1)[0][0]
    for dict_row in sorted(suite_data, key=lambda _: _["revision"]):
        suite_id = metomi.rosie.suite_id.SuiteId.from_idx_branch_revision(
            dict_row["idx"], dict_row["branch"], dict_row["revision"]
        )
        dict_row["suite"] = suite_id.to_string_with_version()
        if "local" in properties:
            dict_row["local"] = suite_id.get_status()
        if "date" in properties:
            dict_row["date"] = time.strftime(
                metomi.rosie.ws_client_cli.DATE_TIME_FORMAT,
                time.gmtime(dict_row.get("date")),
            )

    return suite_data


def calculate_edges(
    graph, suite_data, filter_id=None, properties=None, max_distance=None
):
    """Get all connected suites for a prefix, optionally filtered."""
    if properties is None:
        properties = []

    node_rosie_properties = {}
    edges = []
    forward_edges = {}
    back_edges = {}

    for dict_row in sorted(suite_data, key=lambda _: _["revision"]):
        idx = dict_row["idx"]
        node_rosie_properties[idx] = []
        for prop in properties:
            node_rosie_properties[idx].append(dict_row.get(prop))
        from_idx = dict_row.get("from_idx")

        if from_idx is None:
            continue

        edges.append((from_idx, idx))
        forward_edges.setdefault(from_idx, [])
        forward_edges[from_idx].append(idx)
        back_edges.setdefault(idx, [])
        back_edges[idx].append(from_idx)

    if filter_id is None:
        # Plot all the edges we've found.
        for edge in sorted(edges):
            node0, node1 = edge
            add_node(graph, node0, node_rosie_properties.get(node0))
            add_node(graph, node1, node_rosie_properties.get(node1))
            graph.add_edge(edge[0], edge[1])
    else:
        reporter = metomi.rose.reporter.Reporter()

        # Only plot the connections involving filter_id.
        node_stack = []
        node_stack = [(filter_id, 0)]
        add_node(
            graph,
            filter_id,
            node_rosie_properties.get(filter_id),
            fillcolor="lightgrey",
            style="filled",
        )

        ok_nodes = set([])
        while node_stack:
            node, distance = node_stack.pop()
            if max_distance is not None and distance > max_distance:
                continue
            ok_nodes.add(node)
            for neighbour_node in forward_edges.get(node, []) + back_edges.get(
                node, []
            ):
                if neighbour_node not in ok_nodes:
                    node_stack.append((neighbour_node, distance + 1))

        if len(ok_nodes) == 1:
            # There are no related suites.
            reporter(NoConnectionsEvent(filter_id))

        for edge in sorted(edges):
            node0, node1 = edge
            if node0 in ok_nodes and node1 in ok_nodes:
                add_node(graph, node0, node_rosie_properties.get(node0))
                add_node(graph, node1, node_rosie_properties.get(node1))
                graph.add_edge(node0, node1)


def add_node(graph, node, node_label_properties, **kwargs):
    """Add a node with a particular label."""
    label_lines = [node]
    if node_label_properties is not None:
        for property_value in node_label_properties:
            label_lines.extend(textwrap.wrap(str(property_value)))
    label_text = "\\n".join(label_lines)  # \n must be escaped for graphviz.
    kwargs.update({"label": label_text})
    graph.add_node(node, **kwargs)


def make_graph(suite_data, filter_id, properties, prefix, max_distance=None):
    """Construct the pygraphviz graph."""
    graph = pygraphviz.AGraph(directed=True)
    graph.graph_attr["rankdir"] = "LR"
    if filter_id:
        graph.graph_attr["name"] = filter_id + " copy tree"
    else:
        graph.graph_attr["name"] = prefix + " copy tree"
    calculate_edges(
        graph, suite_data, filter_id, properties, max_distance=max_distance
    )
    return graph


def output_graph(graph, filename=None, debug_mode=False):
    """Draw the graph to filename (or temporary file if None)."""
    metomi.rose.metadata_graph.output_graph(
        graph, debug_mode=debug_mode, filename=filename
    )


def print_graph(suite_data, filter_id, properties=None, max_distance=None):
    """Dump out list of graph entries relating to a suite"""
    if properties is None:
        properties = []

    reporter = metomi.rose.reporter.Reporter()

    ancestry = {}
    # Process suite_data to get ancestry tree
    for dict_row in sorted(suite_data, key=lambda _: _["revision"]):
        idx = dict_row["idx"]
        from_idx = dict_row.get("from_idx")

        if idx not in ancestry:
            ancestry[idx] = {'parent': None, 'children': []}

        if from_idx:
            ancestry[idx]['parent'] = from_idx

        for prop in properties:
            ancestry[idx][prop] = dict_row.get(prop)

        if from_idx in ancestry:
            ancestry[from_idx]['children'].append(idx)
        else:
            ancestry[from_idx] = {'parent': None, 'children': [idx]}

    # Print out info
    parent_id = ancestry[filter_id]['parent']

    if parent_id:
        reporter(
            PrintSuiteDetails(
                parent_id, [ancestry[parent_id][p] for p in properties]
            ),
            prefix="[parent]",
        )
    else:
        reporter(PrintSuiteDetails(None), prefix="[parent]")

    children = ancestry[filter_id]['children']
    generation = 1
    # Print out each generation of child suites
    while children:
        next_children = []
        for child in children:
            reporter(
                PrintSuiteDetails(
                    child, [ancestry[child][p] for p in properties]
                ),
                prefix="[child%s]" % generation,
            )
            # If a child has children add to list of next generation children
            if ancestry[child]['children']:
                next_children += ancestry[child]['children']
        if max_distance and generation >= max_distance:
            break
        generation += 1
        children = next_children


def main():
    """Provide the CLI interface."""
    opt_parser = metomi.rose.opt_parse.RoseOptionParser(
        usage='rosie graph [OPTIONS] [ID]',
        description='Graph suite copy ancestry.',
        epilog='''
ARGUMENTS
    ID
        A suite id to graph. If given, only the suites that are
        connected to this id by copy history will be graphed.
        '''
    )
    opt_parser.add_my_options(
        "distance", "output_file", "prefix", "property", "text"
    )
    opt_parser.modify_option(
        'output_file',
        help=(
            'The name of the file for dumping the output.'
            '\nOtherwise, the output will go to a temporary file which will'
            ' get tidied up.'
            '\nThe extension of the filename determines the'
            ' output format - see graphviz AGraph.draw documentation.'
        ),
    )
    opts, args = opt_parser.parse_args()
    filter_id = None
    if args:
        filter_id = args[0]
        prefix = metomi.rosie.suite_id.SuiteId(id_text=filter_id).prefix
        if opts.prefix:
            opt_parser.error("No need to specify --prefix when specifying ID")
    elif opts.prefix:
        prefix = opts.prefix
    else:
        prefix = metomi.rosie.suite_id.SuiteId.get_prefix_default()
    if opts.distance and not args:
        opt_parser.error("distance option requires an ID")
    if opts.text and not args:
        opt_parser.error("print option requires an ID")

    suite_data = get_suite_data(prefix, opts.property)

    if opts.text:
        print_graph(
            suite_data, filter_id, opts.property, max_distance=opts.distance
        )
    else:
        graph = make_graph(
            suite_data,
            filter_id,
            opts.property,
            prefix,
            max_distance=opts.distance,
        )
        output_graph(
            graph, filename=opts.output_file, debug_mode=opts.debug_mode
        )


if __name__ == "__main__":
    main()
