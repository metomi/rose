/* ----------------------------------------------------------------------------
 * THIS FILE IS PART OF THE CYLC SUITE ENGINE.
 * Copyright (C) NIWA & British Crown (Met Office) & Contributors.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 * ------------------------------------------------------------------------- */

/* Return a list of matches for the provided string, see also String.indexOf. */
String.prototype.indicesOf = function (sub) {
    var str = String(this);
    var index = str.indexOf(sub);
    var count = 0;
    var ret = [];
    while (index != -1) {
        str = str.substr(index + 1);
        ret.push(index + count);
        count += index + 1;
        index = str.indexOf(sub);
    }
    return ret;
}


/* Split a text node on the newline character, see also Text.splitText. */
Text.prototype.splitLines = function () {
    var indices = $(this).text().indicesOf('\n');
    if (indices && indices[0] == 0) {
        // ignore leading new line characters
        indices.shift();
    }
    if (indices.length < 1) {
        // no line breaks - skip
        return [];
    }
    var node = this;
    var offset = 0;
    for (let index of indices) {
        node = node.splitText(index - offset);
        offset = index;
    }
}

/* Remove the leading (+| ) character from each line of a diff block and
 * re-insert them with CSS so that they are not included in the copy selection.
 *
 * Add the ".noselect" class to lines prefixed (-) to make them disappear from
 * copied text. */
$(document).ready(function() {
    $('div.highlight-diff pre').each(function () {
        // Unformatted text is represented as text nodes which don't fit into
        // the DOM in the way regular HTML elements do so we cannot iterate
        // over .children() but must use childNodes instead.
        for (let node of this.childNodes) {
            if (node.nodeName == '#text') {  // "unchanged" line.
                // Split multi-line text nodes into separate lines so we can
                // remove the leading whitespace.
                node.splitLines();
            } else {
                text = $(node).html().substr(1);
                if ($(node).hasClass('gi')) {  // "added" line.
                    // Remove leading character.
                    $(node).html($(node).html().substr(1));
                } else if ($(node).hasClass('gd')) {  // "removed" line.
                    // Make un-selectable.
                    $(node).addClass('noselect');
                }
            }
        }
    });

    // Iterate again to remove the leading whitespace from unchanged lines.
    var node, text, newnode;
    $('div.highlight-diff pre').each(function () {
        node = this.childNodes[0];
        while (node) {
            // Skip nodes if they just contain whitespace (including new
            // line characters).
            if (node.nodeName == '#text' && $(node).text().trim()) {
                text = $(node).text();
                if (text[0] == '\n') {
                    // Move leading new lines onto the end of the string.
                    text = text.substr(1);
                    node = node.splitText(1);
                }
                if (text[0] == ' ') {
                    // Remove leading whitespace, this will be provided via
                    // CSS.
                    text = text.substr(1);
                }

                // Create a new span to represent this text node. Apply the 'gn'
                // class which will provide leading whitespace.
                $('<span />')
                    .append(text)
                    .addClass('gn')
                    .insertBefore(node);

                // Move on to the next node and remove the current text node.
                newnode = node.nextSibling;
                $(node).remove();
                node = newnode;
            } else {
                // To avoid iterating over any nodes we are adding (infinite loop)
                // we use node.nextSibling to get the next node and insert any
                // new nodes before the current one.
                node = node.nextSibling;
            }
        }
    });

});
