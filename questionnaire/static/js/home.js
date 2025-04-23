! function($) {
    "use strict";

    var AI4NW = function() {};

    AI4NW.prototype.initStickyMenu = function() {
        // Add scroll class
        $(window).scroll(function() {
            var scroll = $(window).scrollTop();

            if (scroll >= 50) {
                $(".sticky").addClass("nav-sticky");
            } else {
                $(".sticky").removeClass("nav-sticky");
            }
        });
    },

    AI4NW.prototype.initSmoothLink = function() {
        // Smooth scroll
        $('.navbar-nav a').on('click', function(event) {
            var $anchor = $(this);
            $('html, body').stop().animate({
                scrollTop: $($anchor.attr('href')).offset().top - 0
            }, 1500, 'easeInOutExpo');
            event.preventDefault();
        });
    },

    AI4NW.prototype.init = function() {
        this.initStickyMenu();
        this.initSmoothLink();
    },

    //init
    $.AI4NW = new AI4NW, $.AI4NW.Constructor = AI4NW
}(window.jQuery),

//initializing
function($) {
    "use strict";
    $.AI4NW.init();
    feather.replace()
}(window.jQuery);