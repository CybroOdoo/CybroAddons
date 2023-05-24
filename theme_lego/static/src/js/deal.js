odoo.define('theme_lego.deal_week', function(require) {
    'use strict';
    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    // Define Animation class for the 'Deal of the Week' snippet
    Animation.registry.deal_of_the_week = Animation.Class.extend({
        selector: '.deal',
        start: function() {
            var self = this;
            // Call backend JSON endpoint to fetch the products marked as 'Deal of the Week'
            ajax.jsonRpc('/get_deal_of_the_week', 'call', {})
                .then(function(data) {
                    if (data) {
                        // Render the fetched product information on the webpage
                        self.$target.empty().append(data);
                    }
                });
        }
    });
});
