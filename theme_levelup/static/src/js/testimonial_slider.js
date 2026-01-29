odoo.define('theme_levelup.testimonial_slider', function(require) {
  "use strict"
   var PublicWidget = require('web.public.widget');
   var TestimonialSlider = PublicWidget.Widget.extend({
   selector: '.awards',
   /* Start function for calling slider carousel function */
   start: function() {
          this.testimonial_carousel();
      },
      /*  Function for testimonial page carousel slider */
      testimonial_carousel:function () {
            if(this.$el.find('.owl-theme2')){
                var owl = this.$el.find('.owl-theme2');
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
  PublicWidget.registry.banner4 = TestimonialSlider;
  return TestimonialSlider;
});
