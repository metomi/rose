/*eslint no-console: off*/

// Default Cylc colour theme.
var minicylc_default_theme = {
    'waiting_fill': 'none',
    'waiting_stroke': '#88c6ff',
    'running_fill': '#00c410',
    'running_stroke': 'black',
    'succeed_fill': '#ada5a5',
    'succeed_stroke': 'black'
}

// Demo colour theme for demmonstrating workflow logic.
var minicylc_demo_theme = {
    'succeed_fill': '#aabbff',
    'succeed_stroke': 'black'
}


class MiniCylc {
    /**
     * Class for animating SVG graphs.
     *
     * Attributes:
     *   - nodes: A dictionary of task names against a list of SVG nodes.
     *   - edges: A dictionary of task edges against a list SVG nodes.
     *   - dependencies: A dictionary of task names against a list of
     *     conditional expressions.
     */

    constructor(div) {
        /**
         * Initiate the object.
         * @param div The <div> element containing the SVG.
         * */

        // Obtain nodes and edges from svg.
        var svg = ($(div).find('object:first')[0]).contentDocument;
        this._find_svg_elements(svg);

        // Parse dependencies.
        var deps = this._get_dependencies_from_graph(div);
        this._construct_dependency_map(deps);

        // Process colour theme.
        this.setup_colours($(div).data('theme'));
    }

    setup_colours(theme) {
        /**
         * Set the colour theme.
         * @param theme The name of a colour theme as a string.
         */
        if (!theme || theme == 'default') {
            this.theme = minicylc_default_theme;
        } else if (theme == 'demo') {
            this.theme = minicylc_demo_theme;
        } else {
            console.log('Warning: Invalid theme detected "' + theme +
                        '", defaulting to black.');
            this.theme = {};
        }
    }

    _find_svg_elements(svg) {
        /**
         * Associate task/dependency names with SVG nodes.
         *
         * Associations stored as dicionaries this.nodes and this.edges.
         * @param svg The <svg> element containg the workflow.
         */
        var nodes = {};
        var edges = {};
        $(svg).find('.graph g').each(function() {
            var node = $(this)[0];
            var node_class = $(node).attr('class');
            if (node_class == 'node') {
                nodes[node.textContent.split('\n')[0]] = node;
            } else if (node_class == 'edge') {
                edges[node.textContent.split('\n')[0]] = node;
            }
        });
        this.nodes = nodes;
        this.edges = edges;
    }

    _get_dependencies_from_graph(div) {
        /**
         * Extract, parse and return a list of dependencies.
         * @param div The minicylc <div> element.
         * @return A list of [left, right] lists e.g. ['a & b', 'c'].
         */
        var deps = [];
        var ind = 0;
        var parts;
        for (let dep of $(div).data('dependencies').split('//')) {
            parts = dep.split('=>');
            if (parts.length == 0) {
                continue;  // Graph line does not contain a dependency => skip.
            }
            for(ind = 0; ind < parts.length-1; ind++) {
                deps.push([parts[ind], parts[ind + 1]]);  // [left, right].
            }
        }

        return deps;
    }

    _construct_dependency_map(deps) {
        /**
         * Associate tasks with conditional expressions.
         *
         * Associations stored as a dictionary - this.dependencies.
         * @param deps A list of dependencies in the form [[left, right], ...].
         */
        var condition;
        var conditional_regex = /[()&]/;
        var conditional_regex2 = /([()&|])/;
        var conditional_chars = ['(', ')', '|', '&'];
        this.dependencies = {};
        for (let dep of deps) {
            // Build a javascript parsable conditional statement.
            condition = [];
            for (let left of dep[0].split(conditional_regex2)) {
                left = left.trim();
                if (left) {
                    if (!conditional_chars.includes(left)) {
                        // All dependencies are :succeed by default,
                        // dependencies are checked using
                        // this.succeed.has(task).
                        condition.push('this.succeed.has("' + left + '")');
                    } else {
                        // conditional character.
                        condition.push(left);
                    }
                }
            }
            condition = condition.join(' ');

            // Associate conditional statements with tasks.
            for (let right of dep[1].split(conditional_regex)) {
                right = right.trim();
                if (!this.dependencies[right]) {
                    this.dependencies[right] = [];
                }
                this.dependencies[right].push(condition);
            }
        }
    }

    evaluate_dependencies(task) {
        /**
         * Check if a task's dependencies are satisfied.
         * @param task The name of the task to evaluate.
         * @return true if satisfied else false.
         */
        var deps = this.dependencies[task];
        if (!deps) {
            return true;
        }
        for (let dep of deps) {
            if (eval(dep) == 0) {
                return false;
            }
        }
        return true;
    }

    _style_node(node, fill, stroke) {
        /**
         * Style a graphviz node.
         * @param fill The fill colour for SVG e.g. 'none', '#aabbcc', 'black'.
         * @param stroke The stroke colour for SVG.
         */
        if (!fill) {
            fill = 'none';  // Default to an unfilled node.
        }
        if (!stroke) {
            stroke = 'black';  // Default to a black border.
        }
        // Style nodes.
        $($(this.nodes[node]).find('ellipse:first')).attr({
            'fill': fill,
            'stroke': stroke
        });
    }

    _style() {
        /**
         * Refresh the style of graph nodes based on their state.
         */
        for (let task of this.waiting) {
            this._style_node(task,
                             this.theme['waiting_fill'],
                             this.theme['waiting_stroke']);
        }
        for (let task of this.running) {
            this._style_node(task,
                             this.theme['running_fill'],
                             this.theme['running_stroke']);
        }
        for (let task of this.succeed) {
            this._style_node(task,
                             this.theme['succeed_fill'],
                             this.theme['succeed_stroke']);
        }
    }

    _init() {
        /**
         * Initiate the simulation / animation.
         */
        this.waiting = new Set();
        this.running = new Set();
        this.succeed = new Set();
        for (let task in this.nodes) {
            this.waiting.add(task);
        }
        this._style();
    }

    _advance() {
        /*
         * To be called with each main loop.
         * @return true if the task pool has changed else false.
         */
        var changed = false;
        for (let task of this.running) {
            this.running.delete(task);
            this.succeed.add(task);
            changed = true;
        }
        for (let task of this.waiting) {
            if (this.evaluate_dependencies(task)) {
                this.waiting.delete(task);
                this.running.add(task);
                changed = true;
            }
        }
        return changed;
    }

    _main_loop(itt) {
        /*
         * The main loop - runs the simulation and handles restyling of nodes.
         * Note function calls itself reccursively.
         */
        var exit = false;

        // Action.
        if (this._advance()) {  // Advance the task pool.
            // If anything has changed restyle.
            this._style();
        } else {
            // If nothing has changed...
            if (this.waiting.size == 0 && this.running.size == 0) {
                // The simulation has ended, reset and restart.
                this._init();
            } else {
                // The suite is stalled, log a console message and do nothing.
                exit = true;
                console.log('Suite stalled :(');
            }
        }

        // Callback.
        if (!exit) {
            var self_ref = this;
            setTimeout(function(){
               self_ref._main_loop(itt + 1);
            }, 3000);
        }
    }

    run() {
        /*
         * Run this simulation.
         */
        this._init();
        this._main_loop(0);
    }

}


// Activate minicylc.
$(document).ready(function() {
    $('.minicylc').each(function() {
        var obj = this;
        $(this).find('object:first').on('load', function() {
            new MiniCylc(obj).run();
        });
    });
});
