odoo.define('theme_eco_food.eco_food_featured_products', function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');

    Animation.registry.get_featured_products = Animation.Class.extend({
          xmlDependencies: ['/theme_eco_food/static/src/xml/snippets/featured_products.xml'],
        selector : '.featured_product',
        start: function(){
            var self = this;
            var QWeb = core.qweb;
            ajax.jsonRpc('/get_featured_products', 'call', {})
            .then(function (data) {
                if(data){
                      self.$el.html(QWeb.render('theme_eco_food.eco_food_featured_products1',{
                  slide1: data.slide1,
                  slide2: data.slide2,
                  slide3: data.slide3,
                  slide4: data.slide4,
                  }));
                self.product_carousel();
                }
            });
        },
        product_carousel: function (autoplay=true, items=8, slider_timing=5000) {
        var self= this;
        console.log('init product carousel');
            $("#featured_eco_food").owlCarousel(
                {
                    items: 1,
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
                    responsiveClass: true,
                }
            );
        },
    });
});