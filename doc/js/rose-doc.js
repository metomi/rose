/******************************************************************************
 * (C) British crown copyright 2012-6 Met Office.
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
$(function () {
    var ALT_COLLAPSE = "collapse";
    var ALT_EXPAND = "expand";
    var ICON_COLLAPSE = "img/rose-icon-collapse.png";
    var ICON_EXPAND = "img/rose-icon-expand.png";
    var IS_MAIN = true;

    // Toggle a collapse/expand image.
    function collapse_expand_icon_toggle(anchor) {
        var img = $("img", anchor);
        if (img.attr("alt") === ALT_EXPAND) {
            img.attr("alt", ALT_COLLAPSE);
            img.attr("src", ICON_COLLAPSE);
            anchor.siblings().filter("ul").show();
        } else { // if (img.attr("alt") == "collapse")
            img.attr("alt", ALT_EXPAND);
            img.attr("src", ICON_EXPAND);
            anchor.siblings().filter("ul").hide();
        }
    }

    // Add collapse/expand anchor to a ul tree.
    function ul_collapse_expand(ul, is_main) {
        var nodes = $("li", ul);
        nodes.each(function (i) {
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
                anchor.click(function () {
                    var href = li_anchor.attr("href");
                    $.get(
                        href,
                        function (data) {
                            collapse_expand_icon_toggle(anchor);
                            anchor.unbind("click");
                            if (content_gen(li, data, href)) {
                                ul_collapse_expand(li.children().filter("ul"));
                                anchor.click(function () {
                                    collapse_expand_icon_toggle(anchor);
                                });
                            } else {
                                img.css("opacity", 0);
                            }
                        },
                        "html"
                    ).error(function () {
                        anchor.unbind("click");
                        img.css("opacity", 0);
                    });
                });
            } else if (li_ul.length) {
                anchor.click(function () {
                    collapse_expand_icon_toggle(anchor);
                });
            } else {
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
        headings.each(function (i) {
            if (this.id === null || this.id === "") {
                return;
            }
            var tag_name = this.tagName.toLowerCase();
            // Add to table of content
            while (CONTENT_INDEX_OF[tag_name] < stack.length) {
                stack.shift();
            }
            var node;
            while (stack.length < CONTENT_INDEX_OF[tag_name]) {
                node = stack.length === 0 ? root : $("> :last-child", stack[0]);
                stack.unshift($("<ul/>").appendTo(node));
            }
            var href = "#" + this.id;
            if (d_href) {
                href = d_href + href;
            }
            stack[0].append($("<li/>").append(
                $("<a/>", {"href": href}).html($.trim($(this).text()))
            ));

            // Add a section link as well
            if (d === document) {
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
        NODE.each(function () {
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

    // Current time in Cylc Format
    NODE = $("#cylc-time");
    if (NODE) {
        NODE.each(function () {
            var d = new Date();
            var now = d.toISOString().replace(
                RegExp("[\\-:]", "g"), "").slice(0, 11).concat("Z");
            $(this).text(now);
        });
    }

    // foreward and back buttons
    NODE = $("#back-button");
    if (NODE) {
        $.get("rose.html", function (data) {
            var sections = $("#body-main li a", $(data));
            var i;
            var last = null;
            var next = null;
            var href;
            var thisHref = window.location.href.split('/').pop().split('#')[0];
            for (i = 0; i < sections.length; i += 1) {
                if ($(sections[i]).attr("class") !== "collapse-expand") {
                    href = $(sections[i]).attr("href");
                    if (href === thisHref) {
                        next = $(sections[i + 1]).attr("href");
                        break;
                    } else {
                        last = href;
                    }
                }
            }
            if (!last) {
                $("#back-button").css({"display": "none"});
            } else {
                $("#back-button").on("click", function () {
                    window.location.href = last;
                });
            }
            if (!next) {
                $("#next-button").css({"display": "none"});
            } else {
                $("#next-button").on("click", function () {
                    window.location.href = next;
                });
            }
        });
    }

    // collapse non-active sub-sections of #sidenav
    function collapseSidenav() {
        $("#sidenav li.active ul").show();
        $("#sidenav li:not(.active) ul").hide();
        $("#sidenav li ul li:not(.active) ul").hide();
    }

    // scroll the sidenav if the currently selected element is offscreen
    function scrollSidenav(minOffset) {
        // get the active anchor which is the furthest down the page
        var active = $("#sidenav li.active > a");
        var maxY = -1;
        var ele;
        var y;
        var i;
        for (i = 0; i < active.length; i += 1) {
            y = $(active[i]).offset().top;
            if (y > maxY) {
                maxY = y;
                ele = active[i];
            }
        }

        if (ele) {
            // get the offset of this element from the bottom of the page
            var topPos = $("#sidenav").offset().top;
            var yPos = maxY - topPos;
            var height = $(window).innerHeight() - $("#sidenav").position().top;
            var offset = yPos - height + $(ele).outerHeight() + minOffset;

            // if the element is offscreen scroll so that it is visible
            if (offset > 0) {
                $("#sidenav").css({"margin-top": -offset});
            } else {
                $("#sidenav").css({"margin-top": 0});
            }
        }
    }

    // sidenav - scrollspy, onchange
    $("#sidenav").on("activate.bs.scrollspy", function () {
        collapseSidenav(); // collapse any non-active sections
        scrollSidenav(50); // scroll the sidenav if selected element off screen
    });

    // removes characters from a string which are not permitted in an html id
    // and replaces space(s) with a single hyphon for readability
    function safeID(id) {
        return id.replace(/[\s]+/g, "-").replace(/[^\w_\-]+/g, "");
    }

    // ajaxes in content and returns a sidebar nav
    // function called recursively, to initiate use loadFromContentsTree(c, true)
    function loadFromContentsTree(contents, isRoot, path) {
        if (!path) {
            path = [];
        }

        // start at the top level, recursively call this function for each
        // section
        var ul;
        if (contents.type === "section") {
            // top level of the contents is a section

            if (!isRoot) {
                // add this section to the path for all items
                path.push(contents.title);
                // add a title for this section
                $("#ajax-body").append(
                    $("<div />", {
                        "id": safeID(contents.title)
                    }).append(
                        $("<span />", {
                            "class": "top-level-section"
                        }).append(
                            $("<span />", {
                                "class": "label label-default"
                            }).append(contents.title)
                        ),
                        $("<br />"),
                        $("<br />")
                    )
                );
            }

            // create a <ul> entry for this section (for the nav)
            ul = $("<ul />");
            if (isRoot) {
                ul.addClass("nav");
                ul.attr({"role": "tablist"});
            }

            // for each sub-section call this function
            var i;
            for (i = 0; i < contents.sections.length; i += 1) {
                ul.append(loadFromContentsTree(contents.sections[i], false,
                        $.extend(true, [], path)));
            }

            // if this the very top level of the contents it has no header ...
            if (isRoot) {
                return ul;
            }
            // ... else append an <a> for this section
            return $("<li />").append(
                $("<a />", {
                    "href": "#" + safeID(contents.title)
                }).append(contents.title),
                ul
            );

        } else if (contents.type === "item") {
            // top level of the contents is an article (page)

            // add this article to the path
            path.push(contents.title);
            // create an html id for this article (for namespacing)
            var pathStr = safeID(path.join("_"));
            // create a holder for this article and a menu for its subsections
            // (h2 tags) in the nav
            var div = $("<div />", {"id": pathStr});
            // add a loading label which gets over-written by ajax data as a
            // placeholder to help scrollspy
            div.append(
                $("<h3 />").append(
                    $("<span />", {"class": "label label-info"}).append(
                        "Loading..."
                    )
                )
            );
            ul = $("<ul />");
            // ajax in the content
            div.load(contents.url + " #panel-main", function () {
                // refresh pretty print
                PR.prettyPrint();

                // remove #panel-main tag
                $(this).find("#panel-main").attr({"id": ""});

                // remove panel footer if present (contains previous / next btns)
                $($(document).find(".panel-footer")).remove();

                // namespace all section ids and add h2 elements to the nav
                pathStr = $(this).attr("id");
                var headings = $(this).find("h2, h3, h4, h5, h6");
                var k;
                var headingID;
                for (k = 0; k < headings.length; k += 1) {
                    if (!$(headings[k]).attr("id")) {
                        continue;
                    }
                    headingID = safeID($(headings[k]).attr("id"));
                    if (headingID !== null) {
                        // namespace the heading
                        $(headings[k]).attr({"id": pathStr + "_" + headingID});
                        if (headings[k].tagName === "H2") {
                            // if heading is an h2 element add to the sidebar
                            // nav
                            ul.append(
                                $("<li />").append(
                                    $("<a />", {
                                        "href": "#" + pathStr + "_" + headingID
                                    }).append($(headings[k]).html())
                                )
                            );
                        }
                    }
                }
            });
            $("#ajax-body").append(div);

            // return the nav
            return $("<li />").append(
                $("<a />", {
                    "href": "#" + pathStr
                }).append(contents.title),
                ul
            );
        }
    }

    // return a tree containing the structure of the contents
    function getContentsTree(section) {
        var subsections = $(section).find("> ul > li");
        if (subsections.length === 0) {
            return {
                "type": "item",
                "url": $($(section).find("a")).attr("href"),
                "title": $($(section).find("a")).html().replace(/\s[\s]+/g, " ")
            };
        } else {
            var ret = [];
            var i;
            for (i = 0; i < subsections.length; i += 1) {
                ret.push(getContentsTree(subsections[i]));
            }
            return {
                "type": "section",
                "title": $(section)[0].childNodes[0].data,
                "sections": ret
            };
        }
    }

    // continueous scroller
    NODE = $("#ajax-body");
    if (NODE.length > 0) {
        // load in the index page in order to obtain the contents from which
        // we can generate this page
        $.ajax({
            "async": false,
            "type": "GET",
            "url": "rose.html",
            "success": function (data) {
                // load in content
                var rootUl = $("#body-main", $(data));
                var contents = getContentsTree(rootUl);
                $("#sidenav").append(loadFromContentsTree(contents, true));

                // setup scroll spy to follow us as we scroll down the page
                $('body').scrollspy({"target": "#sidenav", "offset": 100});
                $('[data-spy="scroll"]').each(function () {
                  var $spy = $(this).scrollspy('refresh')
                })
            }
        });
    }
});

