odoo.define('theme_levelup.home_slider', function(require) {
  "use strict"
   var PublicWidget = require('web.public.widget');
   var BlogSlider = PublicWidget.Widget.extend({
   selector: '.awards',
   /* Start function for calling carousel function */
   start: function() {
          this.blog_carousel();
      },
      /* Function for slider page blog carousel*/
      blog_carousel:function () {
        if(this.$el.find('.owl-theme1').length > 0) {
           var owl = this.$el.find('.owl-theme1');
           console.log('owl', owl)
             owl.owlCarousel({
                loop: true,
                margin: 10,
                nav: false,
                items: 1,
                autoplay: true,
            });
            this.$el.find('.custom-nav .prev').click(function () {
                owl.trigger('prev.owl.carousel');
            });
            this.$el.find('.custom-nav .next').click(function () {
                owl.trigger('next.owl.carousel');
            });
        }
      },
  });
  PublicWidget.registry.banner3 = BlogSlider;
  return BlogSlider;
});
