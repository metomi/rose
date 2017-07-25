Basic Demo Page
===============

Mauris Sem Libero
-----------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi augue neque,
suscipit quis ipsum ac, elementum mattis metus. Phasellus eget malesuada
libero.

.. epigraph::

   Nulla nisl tellus, scelerisque nec tortor tempus, tempor consequat nisl

   -- Aliquam Volutpat

Quisque vitae condimentum mauris. Morbi diam velit, facilisis rhoncus erat non,
rutrum accumsan ante. Praesent ut sapien odio. Suspendisse rutrum maximus risus
finibus eleifend


Nunc sagittis
-------------

Integer porta eu ex vel dictum. Nunc sagittis egestas tempor. Cras sit amet
arcu ac quam bibendum lobortis. Sed cursus iaculis neque, maximus hendrerit
massa eleifend vitae. Sed dolor velit, rutrum ac faucibus vel, rhoncus nec
nibh. Quisque et est at magna aliquet rutrum:

- Phasellus id
- Consequat nulla
- Nunc consequat

Equit emet id:

.. code-block:: javascript

   $(function(){function t(t){var n=$("img",t);n.attr("alt")===p?(n.attr("alt",c),n.attr("src",d),t.siblings().filter("ul").show()):(n.attr("alt",p),n.attr("src",h),t.siblings().filter("ul").hide())}function n(i,a){var l=$("li",i);l.each(function(i){var l=$(this),r=l.children().first();if(r.is("a")){var s=$("> ul",l);s.hide();var o=$("<img/>",{alt:p,src:h});o.addClass("collapse-expand");var c=$("<a/>").append(o);l.prepend(c),a?c.click(function(){var i=r.attr("href");$.get(i,function(a){t(c),c.unbind("click"),e(l,a,i)?(n(l.children().filter("ul")),c.click(function(){t(c)})):o.css("opacity",0)},"html").error(function(){c.unbind("click"),o.css("opacity",0)})}):s.length?c.click(function(){t(c)}):o.css("opacity",0)}})}function e(t,n,e){null==n&&(n=document);var i={h2:1,h3:2,h4:3,h5:4,h6:5},a=[],l=!1,r=$("#body-main",$(n)).children("h2, h3, h4, h5, h6");return r.push.apply(r,$(".slide",$(n)).children("h2, h3, h4, h5, h6")),r.each(function(r){if(null!==this.id&&""!==this.id){for(var s=this.tagName.toLowerCase();i[s]<a.length;)a.shift();for(var o;a.length<i[s];)o=0===a.length?t:$("> :last-child",a[0]),a.unshift($("<ul/>").appendTo(o));var c="#"+this.id;if(e&&(c=e+c),a[0].append($("<li/>").append($("<a/>",{href:c}).html($.trim($(this).text())))),n===document){var p=$("<a/>",{href:"#"+this.id});p.addClass("sectionlink"),p.append("¶"),$(this).append(p)}l=!0}}),l}function i(){$("#sidenav li.active ul").show(),$("#sidenav li:not(.active) ul").hide(),$("#sidenav li ul li:not(.active) ul").hide()}function a(t){var n,e,i,a=$("#sidenav li.active > a"),l=-1;for(i=0;i<a.length;i+=1)e=$(a[i]).offset().top,e>l&&(l=e,n=a[i]);if(n){var r=$("#sidenav").offset().top,s=l-r,o=$(window).innerHeight()-$("#sidenav").position().top,c=s-o+$(n).outerHeight()+t;c>0?$("#sidenav").css({"margin-top":-c}):$("#sidenav").css({"margin-top":0})}}function l(t){return t.replace(/[\s]+/g,"-").replace(/[^\w_\-]+/g,"")}function r(t,n,e){e||(e=[]);var i;if("section"===t.type){n||(e.push(t.title),$("#ajax-body").append($("<div />",{id:l(t.title)}).append($("<span />",{"class":"top-level-section"}).append($("<span />",{"class":"label label-default"}).append(t.title)),$("<br />"),$("<br />")))),i=$("<ul />"),n&&(i.addClass("nav"),i.attr({role:"tablist"}));var a;for(a=0;a<t.sections.length;a+=1)i.append(r(t.sections[a],!1,$.extend(!0,[],e)));return n?i:$("<li />").append($("<a />",{href:"#"+l(t.title)}).append(t.title),i)}if("item"===t.type){e.push(t.title);var s=l(e.join("_")),o=$("<div />",{id:s});return o.append($("<h3 />").append($("<span />",{"class":"label label-info"}).append("Loading..."))),i=$("<ul />"),o.load(t.url+" #panel-main",function(){PR.prettyPrint(),$(this).find("#panel-main").attr({id:""}),$($(document).find(".panel-footer")).remove(),s=$(this).attr("id");var t,n,e,a,r=$(this).find("h2, h3, h4, h5, h6");for(t=0;t<r.length;t+=1)if($(r[t]).attr("id")&&(a=$(r[t]).attr("id"),e=l(a),null!==e&&($(r[t]).attr({id:s+"_"+e}),"H2"===r[t].tagName))){i.append($("<li />").append($("<a />",{href:"#"+s+"_"+e}).append($(r[t]).html())));var o=$(this).find('a[href="#'+a+'"]');for(n=0;n<o.length;n+=1)$(o[n]).attr("href","#"+s+"_"+e)}}),$("#ajax-body").append(o),$("<li />").append($("<a />",{href:"#"+s}).append(t.title),i)}}function s(t){var n=$(t).find("> ul > li");if(0===n.length)return{type:"item",url:$($(t).find("a")).attr("href"),title:$($(t).find("a")).html().replace(/\s[\s]+/g," ")};var e,i=[];for(e=0;e<n.length;e+=1)i.push(s(n[e]));return{type:"section",title:$(t)[0].childNodes[0].data,sections:i}}var o,c="collapse",p="expand",d="img/rose-icon-collapse.png",h="img/rose-icon-expand.png",f=!0;o=$("#main-content"),o&&n(o,f),o=$("#content"),o&&e(o)&&(n(o),o.prepend($("<h2/>").text("Contents"))),o=$(".shell"),o&&o.each(function(){var t=$("<pre/>").addClass("shell-prompt");$(this).wrap($("<div/>")).before(t);for(var n=0,e=$(this).text();n>=0&&n+1<e.length;)t.append("(shell)$\n"),n=e.indexOf("\n",n+1)}),o=$("#rose-version"),o&&o.text("Rose "+ROSE_VERSION),"undefined"!=typeof prettyPrint&&prettyPrint(),o=$("#cylc-time"),o&&o.each(function(){var t=new Date,n=t.toISOString().replace(RegExp("[\\-:]","g"),"").slice(0,11).concat("Z");$(this).text(n)}),o=$("#back-button"),o&&$.get("rose.html",function(t){var n,e,i=$("#body-main li a",$(t)),a=null,l=null,r=window.location.href.split("/").pop().split("#")[0];for(n=0;n<i.length;n+=1)if("collapse-expand"!==$(i[n]).attr("class")){if(e=$(i[n]).attr("href"),e===r){l=$(i[n+1]).attr("href");break}a=e}a?$("#back-button").on("click",function(){window.location.href=a}):$("#back-button").css({display:"none"}),l?$("#next-button").on("click",function(){window.location.href=l}):$("#next-button").css({display:"none"})}),$("#sidenav").on("activate.bs.scrollspy",function(){i(),a(50)}),o=$("#ajax-body"),o.length>0&&$.ajax({async:!1,type:"GET",url:"rose.html",success:function(t){var n=$("#body-main",$(t)),e=s(n);$("#sidenav").append(r(e,!0)),$("body").scrollspy({target:"#sidenav",offset:100}),$('[data-spy="scroll"]').each(function(){$(this).scrollspy("refresh")})}})});

Et emit ided:

.. table:: 
   :widths: auto

   =====  =====
     x      y
   =====  =====
   Ystad  Malmo
   Midds  Murde
   =====  =====



Mauris Sem Libero =
===================

Mauris Sem Libero -
-------------------

Mauris Sem Libero ^
^^^^^^^^^^^^^^^^^^^

Mauris Sem Libero "
"""""""""""""""""""


.. tip::

   Note that characters aren't assigned to levels, its just a reccomended
   convention.
