/******************************************************************************
 * (C) British crown copyright 2012-3 Met Office.
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
    var ALT_COLLAPSE = "collapse";
    var ALT_EXPAND = "expand";
    var ICON_COLLAPSE = "rose-icon-collapse.png";
    var ICON_EXPAND = "rose-icon-expand.png";
    var IS_MAIN = true;

    // Toggle a collapse/expand image.
    function collapse_expand_icon_toggle(anchor) {
        var img = $("img", anchor);
        if (img.attr("alt") == ALT_EXPAND) {
            img.attr("alt", ALT_COLLAPSE);
            img.attr("src", ICON_COLLAPSE);
            anchor.siblings().filter("ul").show();
        }
        else { // if (img.attr("alt") == "collapse")
            img.attr("alt", ALT_EXPAND);
            img.attr("src", ICON_EXPAND);
            anchor.siblings().filter("ul").hide();
        }
    }

    // Add collapse/expand anchor to a ul tree.
    function ul_collapse_expand(ul, is_main) {
        var nodes = $("li", ul);
        nodes.each(function(i) {
            var li = $(this);
            var li_anchor = li.children().first();
            if (!li_anchor.is("a")) {
                return;
            }
            var li_ul = $("> ul", li);
            li_ul.hide();
            var img = $("<img/>", {"alt": ALT_EXPAND, "src": ICON_EXPAND});
            img.addClass("collapse-expand");
            var anchor = $("<a/>").append(img);
            li.prepend(anchor);
            if (is_main) {
                anchor.click(function() {
                    var href = li_anchor.attr("href");
                    $.get(
                        href,
                        function(data) {
                            collapse_expand_icon_toggle(anchor);
                            anchor.unbind("click");
                            if (content_gen(li, data, href)) {
                                ul_collapse_expand(li.children().filter("ul"));
                                anchor.click(function() {
                                    collapse_expand_icon_toggle(anchor);
                                });
                            }
                            else {
                                img.css("opacity", 0);
                            }
                        },
                        "xml"
                    )
                    .error(function() {
                        anchor.unbind("click");
                        img.css("opacity", 0);
                    });
                });
            }
            else if (li_ul.length) {
                anchor.click(function() {
                    collapse_expand_icon_toggle(anchor);
                });
            }
            else {
                img.css("opacity", 0);
            }
        });
    }

    // Generate table of content of a document.
    function content_gen(root, d, d_href) {
        if (d == null) {
            d = document;
        }
        var CONTENT_INDEX_OF = {"h2": 1, "h3": 2, "h4": 3, "h5": 4, "h6": 5};
        var stack = [];
        var done_something = false;
        var headings = $("#body-main", $(d)).children("h2, h3, h4, h5, h6");
        headings.push.apply(headings, $(".slide", $(d)).children("h2, h3, h4, h5, h6"));
        headings.each(function(i) {
            if (this.id == null || this.id == "") {
                return;
            }
            var tag_name = this.tagName.toLowerCase();
            // Add to table of content
            while (CONTENT_INDEX_OF[tag_name] < stack.length) {
                stack.shift();
            }
            while (stack.length < CONTENT_INDEX_OF[tag_name]) {
                var node = stack.length == 0 ? root : $("> :last-child", stack[0]);
                stack.unshift($("<ul/>").appendTo(node));
            }
            var href = "#" + this.id;
            if (d_href) {
                href = d_href + href;
            }
            stack[0].append($("<li/>").append(
                $("<a/>", {"href": href}).html($(this).text())
            ));

            // Add a section link as well
            if (d == document) {
                var section_link_anchor = $("<a/>", {"href": "#" + this.id});
                section_link_anchor.addClass("sectionlink");
                section_link_anchor.append("\xb6");
                $(this).append(section_link_anchor);
            }

            done_something = true;
        });
        return done_something;
    }

    var NODE;

    // Top page table of content
    NODE = $("#main-content");
    if (NODE) {
        ul_collapse_expand(NODE, IS_MAIN);
    }

    // Table of content
    NODE = $("#content");
    if (NODE) {
        if (content_gen(NODE)) {
            ul_collapse_expand(NODE);
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
        NODE.text("Rose " + ROSE_VERSION);
    }

    // Google Code Prettify
    if (typeof prettyPrint != 'undefined') {
        prettyPrint();
    }
    
    // Time now in Cylc Format
    NODE = $("#cylc-time");
    if (NODE) {
        NODE.each(function(){
            var d = new Date();
            var now = d.toISOString().replace(
                        RegExp("[\\-:T]", "g"),"").slice(0,10)
            $(this).text(now);
        });
    }
});
