odoo.define('theme_eco_food.eco_food_best_seller', function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    /**
    Extend the class animation to add the details for best seller snippet in
    theme eco food
    **/
    Animation.registry.get_best_seller = Animation.Class.extend({
      xmlDependencies: ['/theme_eco_food/static/src/xml/snippets/eco_food_best_sellers_templates.xml'],
         selector : '.best_seller_products',
         disabledInEditableMode: false,
         /**
         To show the best seller product in theme eco food best seller snippet
         **/
         start: function(){
            var QWeb = core.qweb;
            const el = this.$el;
            async function fetchBestSellerData(){
                const data = await ajax.jsonRpc('/get_best_seller', 'call', {})
                console.log(data, "get_best_seller")
                if(data){
                    el.html(QWeb.render('theme_eco_food.eco_food_best_sellers',{
                    best_seller: data,
                  }));
                }

            }

            fetchBestSellerData();
         },
         destroy: function () {
            this._clearContent();
            this._super.apply(this, arguments);
         },
        _clearContent: function () {
            const $templateArea = this.$el.find('.best_seller_products');
            console.log(this.$el,"destroy", $templateArea)

            this.trigger_up('widgets_stop_request', {
                $target: $templateArea,
            });
            $templateArea.html('');
        },

    });
});
