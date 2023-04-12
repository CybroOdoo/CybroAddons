odoo.define('theme_eco_food.eco_food_best_seller', function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');

    Animation.registry.get_best_seller = Animation.Class.extend({
      xmlDependencies: ['/theme_eco_food/static/src/xml/snippets/best_seller.xml'],
        selector : '.best_seller',
         start: function(){
            var self = this;
            var QWeb = core.qweb;
            ajax.jsonRpc('/get_best_seller', 'call', {})
            .then((data) => {
                      this.$el.html(QWeb.render('theme_eco_food.eco_food_best_seller1',{
                  best_seller: data.best_seller,
                  }));
            });
         }
    });
});
