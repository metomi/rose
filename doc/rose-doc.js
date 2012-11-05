/******************************************************************************
 * (C) British crown copyright 2012 Met Office.
 * 
 * This file is part of Rose, a framework for scientific suites.
 * 
 * Rose is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * Rose is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with Rose. If not, see <http://www.gnu.org/licenses/>.
 *
 ******************************************************************************/
$(function() {
    var NODE;

    // Table of content
    NODE = $("#content");
    if (NODE) {
        var CONTENT_INDEX_OF = {"H2": 1, "H3": 2, "H4": 3, "H5": 4, "H6": 5};
        var stack = [];
        var done_something = false;
        $("#body-main").children("h2, h3, h4, h5, h6").each(function(i) {
            if (this.id == null || this.id == "") {
                return;
            }
            // Add to table of content
            while (CONTENT_INDEX_OF[this.tagName] < stack.length) {
                stack.shift();
            }
            while (stack.length < CONTENT_INDEX_OF[this.tagName]) {
                var node = stack.length == 0 ? NODE : $("> :last-child", stack[0]);
                stack.unshift($("<ul/>").appendTo(node));
            }
            stack[0].append($("<li/>").append(
                $("<a/>", {"href": "#" + this.id}).html(this.innerHTML)
            ));

            // Add a section link as well
            var section_link_anchor = $("<a/>", {"href": "#" + this.id});
            section_link_anchor.addClass("sectionlink");
            section_link_anchor.append("\xb6");
            $(this).append(section_link_anchor);

            done_something = true;
        });
        if (done_something) {
            NODE.prepend($("<h2/>").text("Contents"));
        }
    }

    // Display shell prompts for <pre class="shell"></pre>
    NODE = $(".shell");
    if (NODE) {
        NODE.each(function() {
            var node = $("<pre/>").addClass("shell-prompt");
            $(this).wrap($("<div/>")).before(node);
            var index = 0;
            var data = $(this).text();
            while (index >= 0 && index + 1 < data.length) {
                node.append("(shell)$\n");
                index = data.indexOf("\n", index + 1);
            }
        });
    }

    // Display version information
    NODE = $("#rose-version");
    if (NODE) {
        NODE.text(ROSE_VERSION);
    }
});
