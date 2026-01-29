odoo.define('theme_eco_food.new_arrivals', function(require){
    'use strict';
    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    /**
    Extend the class animation to add the details for new arrival product
    snippet in theme eco food
    **/
    Animation.registry.new_products = Animation.Class.extend({
        xmlDependencies: ['/theme_eco_food/static/src/xml/snippets/eco_food_new_arrivals_new_templates.xml'],
        selector : '.new_arrival_products',
        disabledInEditableMode: false,
        /** To show the new arrival products in theme eco food best seller snippet **/
        start: function(){
            var self = this;
            var QWeb = core.qweb;
            ajax.jsonRpc('/eco_food_new_arrivals', 'call', {})
            .then(function (data) {
                console.log("new ", data)
                if(data){
                  self.$el.html(QWeb.render('theme_eco_food.eco_food_new_arrivals_new',{
                    new_arrival: data,
                  }));
                  self.product_carousel();
                }
            });
        },
        /** To align the style in new arrival product snippet **/
        product_carousel: function (autoplay=false, items=5, slider_timing=5000) {
            this.$(".new_arrival_carousel").owlCarousel({
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
                responsiveClass: true,
                responsive: {
                    0: {
                        items: 1,
                    },
                    576: {
                        items: 2,
                    },
                    768: {
                        items: 3,
                    },
                    992: {
                        items: 6,
                    }
                },

            });
        },
        destroy: function () {
            this._clearContent();
            this._super.apply(this, arguments);
         },
        _clearContent: function () {
            const $templateArea = this.$el.find('.new_arrival_products');
            this.trigger_up('widgets_stop_request', {
                $target: $templateArea,
            });
            $templateArea.html('');
        },
    });
});
