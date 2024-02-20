odoo.define('theme_eco_food.eco_food_recently_added', function(require) {
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc')
    /**
    Extend the class animation to add the details for recently added product
    snippet in theme eco food
    **/
    Animation.registry.get_recently_added_products = Animation.Class.extend({
        xmlDependencies:['/theme_eco_food/static/src/xml/snippets/eco_food_recently_added_product_new_templates.xml'],
        selector: '.recently_added_carousel',
        disabledInEditableMode: false,
        /** To show the recently added products in theme eco food best seller snippet **/
        start: function() {
            var self = this;
            var QWeb = core.qweb;
            ajax.jsonRpc('/get_recently_added_products', 'call', {})
                .then(function(data) {
                    if (data) {
                        self.$el.html(QWeb.render('theme_eco_food.eco_food_recently_added_product_new',{
                            slides: data,
                        }));
                        self.product_carousel();
                    }
                });
        },
         /** To align the style in recently added product snippet **/
        product_carousel: function(autoplay = false, items = 1, slider_timing = 5000) {
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
            });
        },
        destroy: function () {
            this._clearContent();
            this._super.apply(this, arguments);
         },
        _clearContent: function () {
            const $templateArea = this.$el.find('.recently_added_carousel');
            this.trigger_up('widgets_stop_request', {
                $target: $templateArea,
            });
            $templateArea.html('');
        },
    });
});
