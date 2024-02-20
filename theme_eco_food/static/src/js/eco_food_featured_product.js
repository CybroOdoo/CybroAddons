odoo.define('theme_eco_food.eco_food_featured_product', function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
     /**
    Extend the class animation to add the details for featured product snippet
    in theme eco food
     **/
    Animation.registry.get_featured_products = Animation.Class.extend({
        xmlDependencies: ['/theme_eco_food/static/src/xml/snippets/eco_food_featured_product_new_templates.xml'],
        selector : '.featured_product_carousal',
        disabledInEditableMode: false,
        /** To show the featured products in theme eco food best seller snippet **/
        start: function(){
            var self = this;
            var QWeb = core.qweb;
            ajax.jsonRpc('/get_featured_products', 'call', {})
            .then(function (data) {
                if(data){
                  self.$el.html(QWeb.render('theme_eco_food.eco_food_featured_product_new',{
                      slides: data,
                  }));
                  self.product_carousel();
                }
            });
        },
        /** To align the style in featured product snippet **/
        product_carousel: function (autoplay=true, items=8, slider_timing=5000) {
            this.$(".favorite-carousel").owlCarousel({
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
            });
        },
        destroy: function () {
            this._clearContent();
            this._super.apply(this, arguments);
         },
        _clearContent: function () {
            const $templateArea = this.$el.find('.featured_product_carousal');
            console.log(this.$el,"destroy", $templateArea)

            this.trigger_up('widgets_stop_request', {
                $target: $templateArea,
            });
            $templateArea.html('');
        },
    });
});
