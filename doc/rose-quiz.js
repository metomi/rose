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
    /* Function for displaying answer/result info.*/
    function show_answers() {
        $(".answers").show(500);
        $(".resultinfo").show(500);
    }
    
    /* Validate and present results on button click.*/
    $("#submitbutton").click(function() {
        $(".answerstatus").remove();
        $(".results").hide();
        $(".resultinfo").remove();
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
            answer = $("input[name='" + input_name + "']:checked")
            if (answer.length == 0) {
                missing_fields.push(i + 1);
            }
            else {
                user_answers[input_name].push(answer.val());
            }
            correct_answer = $("#" + input_name + " .answers").attr("class").replace("answers ", "");
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
                $("#" + input_name + " .answers").prepend("<span class='answerstatus'><strong class='succeed'>Correct:</strong> </span>");
                good_answers += 1;
            }
            else {
                $("#" + input_name + " .answers").prepend("<span class='answerstatus'><strong class='fail'>Answer:</strong> </span>");
                bad_answers += 1;
            }
        });
        $("#results").append("<h2 id='results' class='resultinfo'>Results<\/h2>" +
                             "<p class='resultinfo'>You got " + good_answers +
                             " answers correct, and " + bad_answers + " wrong.<\/p>");
        $(".resultinfo").hide()
        $("html, body").animate({
            scrollTop: $("#results").offset().top,
        }, {
            "duration": 500,
            "complete": show_answers
        });
        $("#submitbutton").remove();
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
