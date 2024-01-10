odoo.define('theme_levelup.service_slider', function(require) {
  "use strict"
  var PublicWidget = require('web.public.widget');
   var Slider2 = PublicWidget.Widget.extend({
   selector: '.testimonial',

   start: function() {
          this.slider_2();
      },
        /*   slider service page   */
      slider_2:function () {
        if(this.$el.find('.test_slider2')){
          var owl = this.$el.find('.test_slider2').owlCarousel({
              loop: true,
              margin: 10,
              nav: false,
              dots:false,
              items: 3,
              center:true,
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
  PublicWidget.registry.banner2 = Slider2;
  return Slider2;
});
