odoo.define('theme_eco_food.new_arrivals', function(require){
    'use strict';
    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
        var core = require('web.core');


    Animation.registry.new_products = Animation.Class.extend({
        xmlDependencies: ['/theme_eco_food/static/src/xml/snippets/new_arrival_products.xml'],
        selector : '.new_arrivals',
        start: function(){
            var self = this;
            var QWeb = core.qweb;
            ajax.jsonRpc('/eco_food_new_arrivals', 'call', {})
            .then(function (data) {
                if(data){
                      self.$el.html(QWeb.render('theme_eco_food.eco_food_new_arrivals1',{
                  new_arrival: data.new_arrival,
                  }));
                    self.product_carousel();
                }
            });
        },
    product_carousel: function (autoplay=false, items=5, slider_timing=5000) {
    var self= this;
         $("#demo_new").owlCarousel(
               {
                    items: 5,
                    loop: true,
                    margin: 30,
                    stagePadding: 30,
                    smartSpeed: 450,
                    autoplay: true,
                    autoPlaySpeed: 1000,
                    autoPlayTimeout: 1000,
                    autoplayHoverPause: true,
                    dots: false,
                    nav: true,
               }
            );
        },
});
});