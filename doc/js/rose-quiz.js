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
    /* Function for displaying answer/result info.*/
    function show_answers() {
        $(".answers").show(500);
        $(".result-info").show(500);
    }

    /* Validate and present results on button click.*/
    $("#submitbutton").click(function() {
        $(".answer-status").remove();
        $(".results").hide();
        $(".result-info").remove();
        var names = [];
        var user_answers = new Array();
        var correct_answers = new Array();
        var missing_fields = [];
        /* Radio button answers */
        $("input[type='radio']").each(function() {
            var input_name = $(this).attr("name");
            if (names.indexOf(input_name) == -1) {
                names.push(input_name);
                user_answers[input_name] = [];
                correct_answers[input_name] = [];
            }
        });
        $.each(names, function(i, input_name) {
            var answer = $("input[name='" + input_name + "']:checked")
            if (answer.length == 0) {
                missing_fields.push(i + 1);
            }
            else {
                user_answers[input_name].push(answer.val());
            }
            var correct_answer = $("#" + input_name + " .answers").attr("class");
            correct_answer = correct_answer.replace("answers ", "");
            correct_answers[input_name].push(correct_answer);
        });
        /* Missing answer checking */
        if (missing_fields.length) {
            alert("Need answers for questions: " + missing_fields.join(", "));
            return false;
        }
        /* Correct answer checking */
        var good_answers = 0;
        var bad_answers = 0;
        $.each(names, function(i, input_name) {
            user_answers[input_name].sort();
            correct_answers[input_name].sort();
            if (user_answers[input_name].join("") ==
                correct_answers[input_name].join("")) {
                $("#" + input_name + " .answers").prepend(
                    $("<span/>",
                      {"class": "answer-status succeed"}
                     ).text("Correct: ")
                );
                good_answers += 1;
            }
            else {
                $("#" + input_name + " .answers").prepend(
                    $("<span/>",
                      {"class": "answer-status fail"}
                     ).text("Answer: ")
                );
                bad_answers += 1;
            }
        });
        var res_text = (
            "Right: " + good_answers +
            ", Wrong: " + bad_answers + "."
        );
        $("#results").append(
            $("<h2/>",
              {"id": "results",
               "class": "result-info"}
             ).text("Results")
        );
        $("#results").append(
            $("<p/>", {"class": "result-info"}).text(res_text)
        );
        $(".result-info").hide();
        $("html, body").animate({
            scrollTop: $("#results").offset().top,
        }, {
            "duration": 500,
            "complete": show_answers
        });
        $("#submitcontainer").remove();
        $("#answer").remove();
        return false;
    });

    /* Hide answers at startup.*/
    $(".answers").hide();

    /* Add appropriate attributes to the inputs and labels at startup.*/
    $(".questions").each(function() {
        var question_id = $(this).attr("id");
        $(this).find("input").each(function() {
            $(this).attr("name", question_id);
            $(this).attr("id", question_id + $(this).attr("value"));
        });
        $(this).find("label").each(function() {
            $(this).attr("for", question_id + $(this).attr("for"));
        });
    });
});
