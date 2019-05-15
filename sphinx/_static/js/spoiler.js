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

    // On-click un-hide the contents of the adminition and hide the button.
    $('.spoiler-show').click(function() {
        $(this).parent().children().show();
        $(this).hide();
    });
});
