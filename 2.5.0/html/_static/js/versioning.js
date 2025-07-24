/* global root_dir current_builder current_page_name current_version */
/* eslint camelcase: "off" */ // global vars not in camel case

$(document).ready(function () {
  $.ajax({
    async: false,
    type: 'GET',
    url: root_dir + 'versions.json',
    dataType: 'json',
    success: function (versions) {
      // the DOM element to append version and format selectors to
      var ele = $('#version-selector')

      // construct version selector
      var ver = ele.append($('<dl />'))
      $(ver).append($('<dt />').append('Versions'))
      for (const version of Object.keys(versions).sort().reverse()) {
        $(ver).append($('<dd />')
          .append($('<a />')
            .attr({
              href: root_dir
                + version + '/'
                + current_builder
                + '/'
                + current_page_name + '.html'
            })
            .append(version)
          )
        )
      }

      // construct format selector
      var bui = ele.append($('<dl />'))
      $(bui).append($('<dt />').append('Formats'))
      var href
      for (const builderForVersion of versions[current_version].sort()) {
        href = root_dir
          + current_version
          + '/'
          + builderForVersion
          + '/'
        if (['html', 'slides'].indexOf(builderForVersion) >= 0) {
          // format has compatible document structure
          href += current_page_name + '.html'
        } else {
          // structure different, link to the index.html page
          href += 'index.html'
        }

        $(bui).append($('<dd />')
          .append($('<a />')
            .attr({ href: href })
            .append(builderForVersion)
          )
        )
      }
    }
  })
})
