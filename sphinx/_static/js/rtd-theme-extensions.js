// Make admonitions linkable.
$(document).ready(function() {
    var itt, element, id;
    $('p.admonition-title').each(function(itt, element) {
        id = 'admonition-' + itt;
        $(element).attr({'id': id});
        $(element).append($('<a />')
            .attr({'href': '#' + id})
            .addClass('headerlink')
            .append('¶')
        );
    });
});
