odoo.define('theme_levelup.about_slider', function(require) {
    "use strict"
    var PublicWidget = require('web.public.widget');
     var AboutSlider = PublicWidget.Widget.extend({
     selector: '#wrapwrap',
     /* Start function for calling slider function */
     start: function() {
            this.about_carousel();
        },
          /*  Function for about page carousel slider */
        about_carousel:function () {
           if(this.$el.find("#owl-slider-8")){
              this.$el.find("#owl-slider-8").owlCarousel({
                  items: 3,
                  loop: true,
                  margin: 40,
                  stagePadding: 0,
                  smartSpeed: 450,
                  autoplay: true,
                  autoPlaySpeed: 3000,
                  autoPlayTimeout: 1000,
                  autoplayHoverPause: true,
                  dots: true,
                  nav: true,
                  animateIn: "fadeIn",
                  animateOut: "fadeOut",
                  center: true,
                });
           }
        },
    });
    PublicWidget.registry.banner = AboutSlider;
    return AboutSlider;
});
