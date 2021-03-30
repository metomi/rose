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

/* This file implements spoiler sections which are hidden by default. */

// sphinx_admonition_class: bootstrap_button_class
const sphinx_admonition_classes = {
    'attention': 'warning',
    'caution': 'warning',
    'error': 'danger',
    'hint': 'success',
    'important': 'success',
    'note': 'info',
    'tip': 'success',
    'warning': 'warning',
    'danger': 'danger'
}

$(document).ready(function() {
    var button_class;
    var spoilers = $('.spoiler');
    for (let spoiler of spoilers) {
        // Hide content.
        $(spoiler).children().hide();
        $(spoiler).find('.admonition-title').show();

        // Determine button class.
        button_class = 'default';
        for (let css_class of $(spoiler).attr('class').split(' ')) {
            if (css_class in sphinx_admonition_classes) {
                button_class = sphinx_admonition_classes[css_class];
                break;
            }
        }

        // Add button
        $(spoiler).append(
            $('<button />')
                .addClass('btn')
                .addClass('btn-' + button_class)
                .addClass('spoiler-show')
                .append('Show')
        );

    }

    // On-click un-hide the contents of the admonition and hide the button.
    $('.spoiler-show').click(function() {
        $(this).parent().children().show();
        $(this).hide();
    });
});
