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
$(function() {
    $(".collapse").collapse();
    $(".livestamp").each(function() {
        $(this).livestamp($(this).attr("title"));
    });
    $(".entry:even").each(function() {
        $(this).addClass("even");
    });
    $(".entry .cycle").each(function() {
        var cycle = $(this).text();
        if (/^\d{10}$/.test(cycle)) { // Classic Cylc YYYYmmDDHH cycle time
            $(this).html(
                "<code>" + cycle.substr(0, 8) + "</code>" // year month day
                + "<code>" + cycle.substr(8, 2) + "</code>" // hour of day
            );
            $(this).attr("title",
                cycle.substr(0, 4) // year
                + "-"
                + cycle.substr(4, 2) // month of year
                + "-"
                + cycle.substr(6, 2) // day of month
                + " "
                + cycle.substr(8, 2) // hour of day
            );
        }
    });
    $(".entry select.seq_log").change(function() {
        this.form.submit();
    });
    var dt_as_m_and_s = function(dt) {
        var s = dt.seconds();
        if (s < 10) {
            s = "0" + s.toString();
        }
        else {
            s = s.toString();
        }
        var m = Math.floor(dt.asMinutes());
        return m.toString() + ":" + s;
    }
    var toggle_fuzzy_time = function(on) {
        if (on) {
            $(".livestamp").each(function() {
                $(this).livestamp($(this).attr("title"));
            });
            $(".entry").each(function() {
                var s_init = $(".t_init", this).attr("title");
                if (s_init == null) {
                    return;
                }
                var s_submit = $(".t_submit", this).attr("title");
                var m_submit = moment(s_submit);
                var m_init = moment(s_init);
                if (m_init.isBefore(m_submit)) {
                    m_init = m_submit;
                }
                $(".t_init", this).prev().removeClass("icon-play");
                $(".t_init", this).prev().addClass("icon-time");
                $(".t_init", this).prev().attr("title", "Queue duration");
                var dt_q = moment.duration(m_init.diff(m_submit));
                $(".t_init", this).text(dt_as_m_and_s(dt_q));
                var s_exit = $(".t_exit", this).attr("title");
                if (s_exit == null) {
                    return;
                }
                var m_exit = moment(s_exit);
                if (m_exit.isBefore(m_init)) {
                    m_exit = m_init;
                }
                $(".t_exit", this).prev().removeClass("icon-stop");
                $(".t_exit", this).prev().addClass("icon-play-circle");
                $(".t_exit", this).prev().attr("title", "Run duration");
                var dt_r = moment.duration(m_exit.diff(m_init));
                $(".t_exit", this).text(dt_as_m_and_s(dt_r));
            });
            $("#toggle-fuzzy-time").addClass("active");
            $("#toggle-fuzzy-time a").click(function() {toggle_fuzzy_time(false);});
        }
        else {
            $(".livestamp").each(function() {
                $(this).livestamp("destroy");
            });
            $(".entry").each(function() {
                var s_init = $(".t_init", this).attr("title");
                if (s_init == null) {
                    return;
                }
                var m_submit = moment($(".t_submit", this).attr("title"));
                $(".t_init", this).prev().removeClass("icon-time");
                $(".t_init", this).prev().addClass("icon-play");
                $(".t_init", this).prev().attr("title", "Started");
                var m_init = moment(s_init);
                if (m_init.isSame(m_submit, "day")) {
                    m_init.utc();
                    s_init = m_init.format("HH:mm:ss");
                }
                $(".t_init", this).text(s_init);
                var s_exit = $(".t_exit", this).attr("title");
                if (s_exit == null) {
                    return;
                }
                $(".t_exit", this).prev().removeClass("icon-play-circle");
                $(".t_exit", this).prev().addClass("icon-stop");
                $(".t_exit", this).prev().attr("title", "Exited");
                var m_exit = moment(s_exit);
                if (m_exit.isSame(m_submit, "day")) {
                    m_exit.utc();
                    s_exit = m_exit.format("HH:mm:ss");
                }
                $(".t_exit", this).text(s_exit);
            });
            $("#toggle-fuzzy-time").removeClass("active");
            $("#toggle-fuzzy-time a").click(function() {toggle_fuzzy_time(true);});
        }
    }
    toggle_fuzzy_time(true);
    $("#page").change(function() {
        this.form.submit();
    });
    $("#page-next").click(function() {
        $("#page").prop("selectedIndex", $("#page").prop("selectedIndex") + 1);
    });
    $("#page-prev").click(function() {
        $("#page").prop("selectedIndex", $("#page").prop("selectedIndex") - 1);
    });
    $("#per_page_max").click(function() {
        $("#per_page").prop("disabled", $(this).prop("checked"));
    });
});
