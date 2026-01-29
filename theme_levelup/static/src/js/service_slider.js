odoo.define('theme_levelup.service_slider', function(require) {
  "use strict"
  var PublicWidget = require('web.public.widget');
   var ServiceSlider = PublicWidget.Widget.extend({
   selector: '.testimonial',
   /* Start function for calling slider function */
   start: function() {
          this.service_slider();
      },
      /* Function for slider in service page   */
      service_slider:function () {
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
  PublicWidget.registry.banner2 = ServiceSlider;
  return ServiceSlider;
});
